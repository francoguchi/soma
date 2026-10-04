"""Validate SOMA documentation and explain impacts relative to a Git baseline."""

import argparse
import difflib
import json
import re
import subprocess
from collections import defaultdict, deque
from pathlib import Path, PurePosixPath

from soma.foundation.strict_json import loads_strict

ROOT = Path(__file__).resolve().parents[1]
RELATIONS = ("depends_on", "implements", "covers", "relates_to", "supersedes")
PROPAGATING = ("depends_on", "implements", "covers")
SECTION_FIELDS = {"id", "anchor", "code_paths", "retired", *RELATIONS}
DOCUMENT_FIELDS = SECTION_FIELDS - {"anchor"} | {
    "version",
    "scope",
    "items",
    "tags",
    "status",
    "reset_db",
}
ID = re.compile(r"[A-Z][A-Z0-9_.-]*\Z")
STATUSES = {"queued", "in_progress", "working", "revisit", "blocked"}


def without_fences(text: str) -> str:
    output = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            output.append("\n")
        else:
            output.append(line if fence is None else "\n")
    return "".join(output)


def unique_strings(node: dict, key: str) -> list[str]:
    values = node.get(key, [])
    if not isinstance(values, list) or any(type(v) is not str or not v for v in values):
        raise ValueError(f"Invalid {key} array on {node.get('id')}")
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {key} on {node.get('id')}")
    return values


def path_valid(path: str) -> bool:
    parsed = PurePosixPath(path)
    return not (
        parsed.is_absolute()
        or ".." in parsed.parts
        or "\\" in path
        or ":" in path
        or any(c in path for c in "*?[]")
        or path.startswith("./")
        or parsed.as_posix() != path.rstrip("/")
        or parsed.as_posix() == "."
    )


def parse_graph(documents: dict[str, str]) -> dict[str, dict]:
    nodes = {}
    for path, raw in sorted(documents.items()):
        text = without_fences(raw.lstrip("\ufeff"))
        comments = list(re.finditer(r"(?m)^<!-- soma-meta\r?\n(.*?)^-->\s*$", text, re.S))
        if not comments:
            if "<!-- soma-meta" in text:
                raise ValueError(f"Malformed metadata comment in {path}")
            continue
        if len(comments) != 1 or text[: comments[0].start()].strip():
            raise ValueError(f"Metadata must appear once before the title: {path}")
        metadata = loads_strict(comments[0][1])
        if type(metadata) is not dict or set(metadata) - DOCUMENT_FIELDS:
            raise ValueError(f"Unknown/invalid document metadata in {path}")
        if type(metadata.get("version")) is not int or metadata["version"] != 1:
            raise ValueError(f"Invalid metadata version in {path}")
        scope = metadata.get("scope")
        if type(scope) is not str or not re.fullmatch(r"[0-9]{2}", scope):
            raise ValueError(f"Invalid scope in {path}")
        numbered = re.match(r"docs/(?:LLD|implementation)/([0-9]{2})/", path)
        if numbered and numbered[1] != scope or path == "docs/architecture.md" and scope != "00":
            raise ValueError(f"Scope disagrees with path: {path}")
        tags = unique_strings(metadata, "tags")
        if any(not re.fullmatch(r"[a-z][a-z0-9_-]*", tag) for tag in tags):
            raise ValueError(f"Invalid tags in {path}")
        goal = path.startswith("docs/implementation/") and numbered is not None
        if goal:
            if not {"status", "reset_db", "implements", "code_paths"} <= metadata.keys():
                raise ValueError(f"Missing goal fields in {path}")
            if metadata["status"] not in STATUSES or type(metadata["reset_db"]) is not bool:
                raise ValueError(f"Invalid goal status/reset_db in {path}")
            expected = re.fullmatch(r"docs/implementation/([0-9]{2})/\1\.([0-9]{2})\.md", path)
            if not expected or metadata.get("id") != f"IMP-{expected[1]}-{expected[2]}":
                raise ValueError(f"Goal ID disagrees with path: {path}")
        elif "status" in metadata or "reset_db" in metadata:
            raise ValueError(f"Goal-only fields in {path}")
        items = metadata.get("items", [])
        if type(items) is not list:
            raise ValueError(f"Invalid item array in {path}")
        anchors = set()
        for entry, section in [(metadata, False), *((item, True) for item in items)]:
            if type(entry) is not dict or section and set(entry) - SECTION_FIELDS:
                raise ValueError(f"Invalid section metadata in {path}")
            identity = entry.get("id")
            if type(identity) is not str or not ID.fullmatch(identity) or identity in nodes:
                raise ValueError(f"Invalid/duplicate ID {identity} in {path}")
            anchor = entry.get("anchor") if section else None
            if section and (
                type(anchor) is not str or not anchor or text.count(f'<a id="{anchor}"></a>') != 1
            ):
                raise ValueError(f"Missing/duplicate anchor for {identity}")
            if section:
                if anchor in anchors:
                    raise ValueError(f"Multiple items share an anchor in {path}")
                anchors.add(anchor)
            if "retired" in entry and type(entry["retired"]) is not bool:
                raise ValueError(f"Invalid retired value on {identity}")
            node = {**entry, "path": path, "scope": scope, "anchor": anchor, "tags": tags}
            for relation in (*RELATIONS, "code_paths"):
                node[relation] = unique_strings(entry, relation)
            if any(not path_valid(value) for value in node["code_paths"]):
                raise ValueError(f"Illegal code path on {identity}")
            nodes[identity] = node
    for node in nodes.values():
        for relation in RELATIONS:
            for target in node[relation]:
                if target not in nodes:
                    raise ValueError(f"Unresolved {relation}: {node['id']} -> {target}")
    return nodes


def validate_state(root: Path, documents: dict[str, str], nodes: dict, branch: str | None) -> None:
    rows = {}
    for path, text in documents.items():
        if not path.endswith("/migration.md"):
            continue
        for line in text.splitlines():
            if not (line.lstrip().startswith("-") and "**R" in line):
                continue
            match = re.fullmatch(
                r"- \[([ x])\] \*\*(R([0-9]{2})\.([0-9]{2})-[A-Z0-9]+) — (PENDING|REUSED|REWRITTEN|REJECTED|DEFERRED|NEW):\*\* .+",
                line,
            )
            if not match:
                raise ValueError(f"Malformed migration row: {path}: {line}")
            checked, row, scope, number, status = match.groups()
            if row in rows or (checked == "x") != (status != "PENDING"):
                raise ValueError(f"Duplicate/inconsistent migration row: {row}")
            goal_id = f"IMP-{scope}-{number}"
            if goal_id not in nodes or path != f"docs/LLD/{scope}/migration.md":
                raise ValueError(f"Migration row has no matching scope/goal: {row}")
            rows[row] = (goal_id, status)
            if nodes[goal_id]["status"] == "working" and status == "PENDING":
                raise ValueError(f"Working goal has open migration row: {row}")
    pointer = documents.get("docs/LLD/CONTINUE.md", "")
    fields = dict(re.findall(r"^\| ([^|]+?) \| ([^|]+?) \|$", pointer, re.M))

    def value(name):
        lane_fields = {
            "Goal file": "Implementation goal file",
            "Scope migration ledger": "Implementation migration ledger",
            "Active goal": "Implementation goal",
            "Active scope": "Implementation scope",
            "Active branch": "Implementation branch",
        }
        key = lane_fields.get(name, name) if "Implementation goal file" in fields else name
        found = re.search(r"`([^`]+)`", fields.get(key, ""))
        if not found:
            raise ValueError(f"Missing continuation field: {name}")
        return found[1]

    goal_path = value("Goal file")
    ledger = value("Scope migration ledger")
    goal_id = value("Active goal").split(" — ")[0]
    scope = value("Active scope").split(" — ")[0]
    if (
        goal_id not in nodes
        or nodes[goal_id]["path"] != goal_path
        or nodes[goal_id]["scope"] != scope
    ):
        raise ValueError("Continuation goal/scope does not resolve")
    if ledger != f"docs/LLD/{scope}/migration.md" or ledger not in documents:
        raise ValueError("Continuation migration ledger does not resolve")
    if branch and value("Active branch") != branch:
        raise ValueError("Continuation branch differs from checked-out branch")
    for node in nodes.values():
        for code_path in node["code_paths"]:
            current = root
            for part in PurePosixPath(code_path).parts:
                if not current.is_dir():
                    break
                entries = {p.name for p in current.iterdir()}
                if part not in entries:
                    if part.casefold() in {name.casefold() for name in entries}:
                        raise ValueError(f"Incorrect path case: {code_path}")
                    break
                current /= part
            if node.get("status") == "working" and not (root / code_path).exists():
                raise ValueError(f"Missing working-goal path: {code_path}")


def match_path(path: str, mapped: str) -> bool:
    return path.startswith(mapped) if mapped.endswith("/") else path == mapped


def document_changes(path: str, before: str, after: str, old: dict, new: dict) -> set[str]:
    owners = {key: node for key, node in {**old, **new}.items() if node["path"] == path}
    if not before or not after:
        return set(owners)
    # Attribute changed lines to explicit anchor sections. Metadata/document text affects all.
    affected = set()

    def owner_at(lines, index, graph):
        anchor = None
        for line in lines[: index + 1]:
            match = re.fullmatch(r'<a id="([^"]+)"></a>', line.strip())
            if match:
                anchor = match[1]
        return (
            next(
                (
                    key
                    for key, node in graph.items()
                    if node["path"] == path and node["anchor"] == anchor
                ),
                None,
            )
            if anchor
            else None
        )

    a, b = before.splitlines(), after.splitlines()
    for tag, a0, a1, b0, b1 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            continue
        found = {owner_at(a, i, old) for i in range(a0, a1)} | {
            owner_at(b, i, new) for i in range(b0, b1)
        }
        if None in found:
            return set(owners)
        affected.update(found)
    return affected


def impacts(old: dict, new: dict, changes: list[str], before: dict, after: dict) -> dict:
    direct = set()
    gaps = []
    all_nodes = list(old.values()) + list(new.values())
    for path in changes:
        if path.endswith(".md"):
            direct.update(
                document_changes(path, before.get(path, ""), after.get(path, ""), old, new)
            )
        mapped = {
            node["id"] for node in all_nodes if any(match_path(path, p) for p in node["code_paths"])
        }
        direct.update(mapped)
        if not mapped and (
            path.startswith(("src/", "tools/", "tests/")) or path in ("pyproject.toml",)
        ):
            gaps.append(path)
    incoming = defaultdict(set)
    for node in all_nodes:
        for relation in PROPAGATING:
            for target in node[relation]:
                incoming[target].add((node["id"], relation))
        for target in node["supersedes"]:
            incoming[target].add((node["id"], "supersedes"))
    explanations = {key: [key] for key in sorted(direct)}
    queue = deque(sorted(direct))
    while queue:
        identity = queue.popleft()
        for consumer, relation in sorted(incoming[identity]):
            if consumer not in explanations:
                explanations[consumer] = explanations[identity] + [f"{relation}:{consumer}"]
                queue.append(consumer)
    return {
        "direct": sorted(direct),
        "indirect": sorted(set(explanations) - direct),
        "explanations": dict(sorted(explanations.items())),
        "mapping_gaps": sorted(set(gaps)),
    }


def git(root, *args, optional=False):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if result.returncode and not optional:
        raise ValueError(result.stderr.decode(errors="replace"))
    return result.stdout.decode("utf-8") if result.returncode == 0 else ""


def report(root: Path = ROOT, baseline: str = "HEAD") -> dict:
    after = {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8-sig")
        for path in (root / "docs").rglob("*.md")
    }
    new = parse_graph(after)
    validate_state(root, after, new, git(root, "branch", "--show-current", optional=True).strip())
    exists = bool(git(root, "rev-parse", "--verify", baseline, optional=True))
    if not exists and baseline != "HEAD":
        raise ValueError("Requested Git baseline does not exist")
    before = {}
    if exists:
        for path in git(root, "ls-tree", "-r", "--name-only", baseline, "docs").splitlines():
            if path.endswith(".md"):
                before[path] = git(root, "show", f"{baseline}:{path}")
    old = parse_graph(before)
    tracked = (
        git(root, "diff", "--name-only", "-z", baseline, "--")
        if exists
        else git(root, "ls-files", "-z")
    ).split("\0")
    # --no-renames yields deletion + addition, covering both paths of a move.
    if exists:
        tracked = git(root, "diff", "--no-renames", "--name-only", "-z", baseline, "--").split("\0")
    untracked = sorted(
        filter(None, git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    )
    changes = sorted(set(filter(None, tracked)) | set(untracked))
    planned = sorted(
        {p for node in new.values() for p in node["code_paths"] if not (root / p).exists()}
    )
    return {
        "baseline": baseline if exists else "empty",
        "index": dict(sorted(new.items())),
        "planned_paths": planned,
        "untracked": untracked,
        **impacts(old, new, changes, before, after),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="HEAD")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = report(baseline=args.baseline)
    content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
