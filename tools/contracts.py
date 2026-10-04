"""Offline schema validation and deterministic shared-subset TypeScript generation."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote

from jsonschema import Draft202012Validator

from soma.foundation.strict_json import loads_strict

ROOT = Path(__file__).resolve().parents[1]
DRAFT = "https://json-schema.org/draft/2020-12/schema"
KEYWORDS = {
    "$schema",
    "$id",
    "$ref",
    "$defs",
    "title",
    "description",
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "minItems",
    "maxItems",
    "uniqueItems",
    "minLength",
    "maxLength",
    "pattern",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "enum",
    "const",
    "anyOf",
    "oneOf",
}


def load_schemas(root: Path) -> dict[Path, dict]:
    result = {}
    identities = set()
    for path in sorted((root / "docs/LLD").glob("[0-9][0-9]/contracts/*.schema.json")):
        schema = loads_strict(path.read_text(encoding="utf-8-sig"))
        Draft202012Validator.check_schema(schema)
        scope = path.parent.parent.name
        if schema.get("$schema") != DRAFT or not re.fullmatch(
            rf"urn:soma:{scope}:[a-z0-9-]+:v[1-9][0-9]*", schema.get("$id", "")
        ):
            raise ValueError(f"Invalid draft/identity: {path}")
        if schema["$id"] in identities:
            raise ValueError("Duplicate contract identity")
        identities.add(schema["$id"])
        result[path.resolve()] = schema
    return result


def resolve_ref(path: Path, ref: str, schemas: dict[Path, dict]) -> tuple[Path, dict]:
    filename, _, fragment = ref.partition("#")
    if ":" in filename or "\\" in filename or Path(filename).is_absolute():
        raise ValueError("Remote/absolute schema references are forbidden")
    target = (path.parent / filename).resolve() if filename else path
    if target.parent != path.parent or target not in schemas:
        raise ValueError("Schema references must remain in the same scope contract directory")
    node = schemas[target]
    if fragment:
        if not fragment.startswith("/"):
            raise ValueError("Only JSON pointer schema references are supported")
        for part in fragment[1:].split("/"):
            node = node[unquote(part).replace("~1", "/").replace("~0", "~")]
    return target, node


def ts_type(node: dict, path: Path, schemas: dict[Path, dict], stack: tuple = ()) -> str:
    if not isinstance(node, dict) or set(node) - KEYWORDS:
        raise ValueError("Schema uses unsupported shared-subset keywords")
    if "$ref" in node:
        if set(node) - {"$ref", "description", "title"}:
            raise ValueError("Shared references cannot have validation siblings")
        key = (path, node["$ref"])
        if key in stack:
            raise ValueError("Recursive shared contracts are unsupported")
        target, referenced = resolve_ref(path, node["$ref"], schemas)
        return ts_type(referenced, target, schemas, stack + (key,))
    for definition in node.get("$defs", {}).values():
        ts_type(definition, path, schemas, stack)
    if "const" in node:
        return json.dumps(node["const"], ensure_ascii=False)
    if "enum" in node:
        return " | ".join(json.dumps(value, ensure_ascii=False) for value in node["enum"])
    if "oneOf" in node or "anyOf" in node:
        alternatives = node.get("oneOf", node.get("anyOf"))
        kinds = [branch.get("type") for branch in alternatives]
        if len(set(kinds)) != len(kinds):
            raise ValueError("Overlapping union branches are unsupported")
        return " | ".join(ts_type(branch, path, schemas, stack) for branch in alternatives)
    kind = node.get("type")
    if isinstance(kind, list):
        return " | ".join(ts_type({**node, "type": value}, path, schemas, stack) for value in kind)
    if kind == "object":
        if node.get("additionalProperties") is not False or "required" not in node:
            raise ValueError("Contract objects must be closed with explicit required fields")
        properties = node.get("properties", {})
        if set(node["required"]) - properties.keys():
            raise ValueError("Required property is undefined")
        fields = []
        for name, child in sorted(properties.items()):
            optional = "" if name in node["required"] else "?"
            fields.append(
                f"readonly {json.dumps(name)}{optional}: {ts_type(child, path, schemas, stack)};"
            )
        return "{ " + " ".join(fields) + " }"
    if kind == "array":
        if "maxItems" not in node or "items" not in node:
            raise ValueError("Contract arrays require explicit bounds and items")
        return "ReadonlyArray<" + ts_type(node["items"], path, schemas, stack) + ">"
    if kind == "string":
        if "maxLength" not in node and "pattern" not in node:
            raise ValueError("Contract strings require bounds")
        return "string"
    if kind in ("integer", "number"):
        if "minimum" not in node or "maximum" not in node:
            raise ValueError("Contract numbers require bounds")
        return "number"
    if kind in ("boolean", "null"):
        return kind
    raise ValueError("Unsupported/untyped shared contract")


def outputs(root: Path) -> dict[Path, str]:
    schemas = load_schemas(root)
    bindings = ["// Generated by tools/contracts.py; do not edit.\n"]
    catalog = {}
    names = set()
    for path, schema in schemas.items():
        name = schema.get("title", "")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name) or name in names:
            raise ValueError("Contracts require unique TypeScript-safe titles")
        names.add(name)
        bindings.append(f"export type {name} = {ts_type(schema, path, schemas)};\n")

        def normalize(node):
            if isinstance(node, list):
                return [normalize(child) for child in node]
            if not isinstance(node, dict):
                return node
            result = {key: normalize(value) for key, value in node.items()}
            if "$ref" in result:
                target, _ = resolve_ref(path, result["$ref"], schemas)
                fragment = result["$ref"].partition("#")[2]
                result["$ref"] = schemas[target]["$id"] + ("#" + fragment if fragment else "")
            return result

        catalog[schema["$id"]] = normalize(schema)
    return {
        root / "src/main/shared/api/generated/contracts.ts": "".join(bindings),
        root
        / "src/main/shared/api/generated/schemas.ts": "// Generated by tools/contracts.py; do not edit.\nexport const schemas = "
        + json.dumps(catalog, ensure_ascii=False, sort_keys=True)
        + " as const;\n",
        root / "src/core/soma/foundation/contracts.schemas.json": json.dumps(
            catalog, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
    }


def generate(root: Path = ROOT, *, check: bool = False) -> None:
    for path, content in outputs(root).items():
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise ValueError(f"Contract binding drift: {path.relative_to(root)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(check=args.check)
