import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools import build_identity, contracts, impact

ROOT = Path(__file__).resolve().parents[3]


def doc(metadata, body=""):
    return "<!-- soma-meta\n" + json.dumps(metadata) + "\n-->\n# Test\n" + body


def fixture_docs():
    return {
        "docs/LLD/00/backend.md": doc(
            {
                "version": 1,
                "id": "BACKEND",
                "scope": "00",
                "items": [
                    {
                        "id": "PROVIDER",
                        "anchor": "provider",
                        "code_paths": ["src/core/provider.py"],
                    },
                    {"id": "CONSUMER", "anchor": "consumer", "depends_on": ["PROVIDER"]},
                ],
            },
            '<a id="provider"></a>\nProvider text\n<a id="consumer"></a>\nConsumer text\n',
        ),
        "docs/implementation/00/00.01.md": doc(
            {
                "version": 1,
                "id": "IMP-00-01",
                "scope": "00",
                "status": "queued",
                "reset_db": False,
                "implements": ["CONSUMER"],
                "code_paths": [],
            }
        ),
        "docs/LLD/00/migration.md": "- [ ] **R00.01-A — PENDING:** donor\n",
        "docs/LLD/CONTINUE.md": "\n".join(
            [
                "| Active scope | `00 — Foundation` |",
                "| Active branch | `feat/00-foundation` |",
                "| Active goal | `IMP-00-01 — Test` |",
                "| Goal file | `docs/implementation/00/00.01.md` |",
                "| Scope migration ledger | `docs/LLD/00/migration.md` |",
            ]
        ),
    }


def test_item_and_code_impact_with_removed_baseline_edge():
    before = fixture_docs()
    old = impact.parse_graph(before)
    after = {
        **before,
        "docs/LLD/00/backend.md": before["docs/LLD/00/backend.md"].replace(
            '"depends_on": ["PROVIDER"]', '"depends_on": []'
        ),
    }
    new = impact.parse_graph(after)
    result = impact.impacts(
        old, new, ["src/core/provider.py", "src/core/unmapped.py"], before, after
    )
    assert result["direct"] == ["PROVIDER"]
    assert result["indirect"] == ["CONSUMER", "IMP-00-01"]
    assert result["explanations"]["IMP-00-01"] == [
        "PROVIDER",
        "depends_on:CONSUMER",
        "implements:IMP-00-01",
    ]
    assert result["mapping_gaps"] == ["src/core/unmapped.py"]
    revised = before["docs/LLD/00/backend.md"].replace("Provider text", "Revised behavior")
    assert impact.document_changes(
        "docs/LLD/00/backend.md", before["docs/LLD/00/backend.md"], revised, old, old
    ) == {"PROVIDER"}
    assert impact.document_changes(
        "docs/LLD/00/backend.md",
        before["docs/LLD/00/backend.md"],
        revised.replace("# Test", "# Revised"),
        old,
        old,
    ) == set(old) - {"IMP-00-01"}


def test_move_maps_both_paths_and_cycles_terminate():
    nodes = {
        "A": {
            "id": "A",
            "path": "docs/test.md",
            "anchor": None,
            "code_paths": ["src/old.py"],
            "depends_on": ["B"],
            "implements": [],
            "covers": [],
            "supersedes": [],
        },
        "B": {
            "id": "B",
            "path": "docs/test.md",
            "anchor": None,
            "code_paths": ["src/new.py"],
            "depends_on": ["A"],
            "implements": [],
            "covers": [],
            "supersedes": [],
        },
    }
    result = impact.impacts(nodes, nodes, ["src/old.py", "src/new.py"], {}, {})
    assert result["direct"] == ["A", "B"]
    assert result["indirect"] == []


@pytest.mark.parametrize(
    "mutation",
    [
        lambda docs: docs.update({"docs/LLD/00/migration.md": "- [x] **R00.01-A — PENDING:** bad"}),
        lambda docs: docs.update(
            {"docs/LLD/00/migration.md": docs["docs/LLD/00/migration.md"] * 2}
        ),
        lambda docs: docs.update({"docs/LLD/00/migration.md": "- [ ] **R0.01-A — PENDING:** bad"}),
        lambda docs: docs.update(
            {
                "docs/implementation/00/00.01.md": docs["docs/implementation/00/00.01.md"].replace(
                    '"queued"', '"working"'
                )
            }
        ),
        lambda docs: docs.update(
            {
                "docs/LLD/CONTINUE.md": docs["docs/LLD/CONTINUE.md"].replace(
                    "`IMP-00-01 — Test`", "`IMP-00-99 — Test`"
                )
            }
        ),
    ],
)
def test_continuation_and_migration_closure_fail_closed(tmp_path, mutation):
    docs = fixture_docs()
    impact.validate_state(tmp_path, docs, impact.parse_graph(docs), "feat/00-foundation")
    mutation(docs)
    with pytest.raises(ValueError):
        impact.validate_state(tmp_path, docs, impact.parse_graph(docs), "feat/00-foundation")


def test_accepted_two_lane_continuation_uses_implementation_lane(tmp_path):
    docs = fixture_docs()
    pointer = docs["docs/LLD/CONTINUE.md"]
    for old, new in [("Active scope", "Implementation scope"), ("Active branch", "Implementation branch"), ("Active goal", "Implementation goal"), ("Goal file", "Implementation goal file"), ("Scope migration ledger", "Implementation migration ledger")]:
        pointer = pointer.replace(old, new)
    docs["docs/LLD/CONTINUE.md"] = pointer + "\n| Design branch | `design/02-tickets-core` |\n"
    impact.validate_state(tmp_path, docs, impact.parse_graph(docs), "feat/00-foundation")
    docs["docs/LLD/CONTINUE.md"] = pointer.replace("`IMP-00-01", "`IMP-00-99")
    with pytest.raises(ValueError, match="does not resolve"):
        impact.validate_state(tmp_path, docs, impact.parse_graph(docs), "feat/00-foundation")


@pytest.mark.parametrize(
    "replacement",
    [
        ('"version": 1', '"version": true'),
        ('"scope": "00"', '"scope": "01"'),
        ('"id": "BACKEND"', '"id": "PROVIDER"'),
        ('"depends_on": ["PROVIDER"]', '"depends_on": ["MISSING"]'),
        ('"code_paths": ["src/core/provider.py"]', '"code_paths": ["../outside"]'),
        ('"scope": "00"', '"scope": "00", "unknown": 1'),
    ],
)
def test_metadata_rejects_invalid_graph(replacement):
    docs = fixture_docs()
    docs["docs/LLD/00/backend.md"] = docs["docs/LLD/00/backend.md"].replace(*replacement)
    with pytest.raises(ValueError):
        impact.parse_graph(docs)


def test_duplicate_metadata_keys_anchors_and_fenced_examples():
    docs = fixture_docs()
    original = docs["docs/LLD/00/backend.md"]
    docs["docs/LLD/00/backend.md"] = original + '\n<a id="provider"></a>\n'
    with pytest.raises(ValueError):
        impact.parse_graph(docs)
    docs["docs/LLD/00/backend.md"] = original + "\n~~~text\n" + original + "\n~~~\n"
    assert "PROVIDER" in impact.parse_graph(docs)
    docs["docs/LLD/00/backend.md"] = original.replace('"version": 1', '"version": 1, "version": 1')
    with pytest.raises(Exception):
        impact.parse_graph(docs)


def schema_fixture(tmp_path):
    source = ROOT / "docs/LLD/00/contracts/error-envelope-v1.schema.json"
    target = tmp_path / "docs/LLD/00/contracts/error-envelope-v1.schema.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(source.read_bytes())
    return target


def test_contract_both_plane_drift_and_authority_change(tmp_path):
    schema_path = schema_fixture(tmp_path)
    contracts.generate(tmp_path)
    contracts.generate(tmp_path, check=True)
    generated = tmp_path / "src/main/shared/api/generated/contracts.ts"
    generated.write_text("stale", encoding="utf-8")
    with pytest.raises(ValueError, match="drift"):
        contracts.generate(tmp_path, check=True)
    contracts.generate(tmp_path)
    provider = tmp_path / "src/core/soma/foundation/contracts.schemas.json"
    provider.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="drift"):
        contracts.generate(tmp_path, check=True)
    contracts.generate(tmp_path)
    schema = json.loads(schema_path.read_text())
    schema["properties"]["recoverability"]["enum"].append("wait")
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(ValueError, match="drift"):
        contracts.generate(tmp_path, check=True)
    contracts.generate(tmp_path)
    assert '"wait"' in generated.read_text()
    assert '"wait"' in provider.read_text()
    stale_response = {
        "code": "OK",
        "summary": "safe",
        "recoverability": "none",
        "safe_next_action": None,
        "correlation_id": "4d204e28-3a66-43cb-81ca-a31cc94c9b11",
    }
    schema["required"].append("new_field")
    schema["properties"]["new_field"] = {"type": "string", "maxLength": 10}
    assert not Draft202012Validator(schema).is_valid(stale_response)


def test_contract_local_reference_and_remote_rejection(tmp_path):
    schema_path = schema_fixture(tmp_path)
    schema = json.loads(schema_path.read_text())
    schema["$defs"] = {"Short": {"type": "string", "maxLength": 20}}
    schema["properties"]["summary"] = {"$ref": "#/$defs/Short"}
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    contracts.generate(tmp_path)
    schema["properties"]["summary"] = {"$ref": "https://example.invalid/schema"}
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(ValueError, match="Remote"):
        contracts.generate(tmp_path)


def test_build_generation_matches_both_planes(tmp_path):
    value = build_identity.generate(tmp_path)
    python = json.loads((tmp_path / "src/core/soma/foundation/build/identity.json").read_text())
    ts = (tmp_path / "src/main/shared/build/identity.ts").read_text()
    assert python == value
    assert json.dumps(value, indent=2) in ts
    assert value["source_commit"] is None
    assert value["dirty"] is None


def test_continuation_branch_case_and_working_path_validation(tmp_path):
    docs = fixture_docs()
    nodes = impact.parse_graph(docs)
    with pytest.raises(ValueError, match="branch"):
        impact.validate_state(tmp_path, docs, nodes, "main")
    (tmp_path / "src/core").mkdir(parents=True)
    (tmp_path / "src/core/Provider.py").write_text("fixture")
    with pytest.raises(ValueError, match="case"):
        impact.validate_state(tmp_path, docs, nodes, "feat/00-foundation")
    (tmp_path / "src/core/Provider.py").unlink()
    docs["docs/LLD/00/migration.md"] = "- [x] **R00.01-A — REWRITTEN:** closed"
    docs["docs/implementation/00/00.01.md"] = (
        docs["docs/implementation/00/00.01.md"]
        .replace('"queued"', '"working"')
        .replace('"code_paths": []', '"code_paths": ["src/missing.py"]')
    )
    with pytest.raises(ValueError, match="Missing working-goal path"):
        impact.validate_state(tmp_path, docs, impact.parse_graph(docs), "feat/00-foundation")


def test_two_item_ids_cannot_share_one_anchor():
    docs = fixture_docs()
    docs["docs/LLD/00/backend.md"] = docs["docs/LLD/00/backend.md"].replace(
        '"anchor": "consumer"', '"anchor": "provider"'
    )
    with pytest.raises(ValueError, match="share an anchor"):
        impact.parse_graph(docs)


def test_retired_provider_reaches_replacement_and_consumers():
    old = impact.parse_graph(fixture_docs())
    replacement = {
        **old["PROVIDER"],
        "id": "REPLACEMENT",
        "code_paths": [],
        "supersedes": ["PROVIDER"],
    }
    new = {
        **old,
        "REPLACEMENT": replacement,
        "CONSUMER": {**old["CONSUMER"], "depends_on": ["REPLACEMENT"]},
    }
    result = impact.impacts(old, new, ["src/core/provider.py"], {}, {})
    assert "REPLACEMENT" in result["indirect"]
    assert result["explanations"]["REPLACEMENT"] == ["PROVIDER", "supersedes:REPLACEMENT"]
    assert "IMP-00-01" in result["indirect"]
