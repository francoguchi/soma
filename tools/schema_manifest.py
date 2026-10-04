"""Generate expected truth only from accepted migration bytes, never a live database."""

import argparse
import json
import secrets
from pathlib import Path

from soma.foundation.persistence.connections import load_sqlcipher_driver
from soma.foundation.persistence.manifest import MigrationManifest
from soma.foundation.persistence.migrations import apply_entries
from soma.foundation.persistence.schema_verify import schema_shape

ROOT = Path(__file__).resolve().parents[1]


def audit_probes():
    command = "81818181-8181-4181-8181-818181818181"
    event = "82828282-8282-4282-8282-828282828282"
    return [
        {
            "setup": [
                [
                    "INSERT INTO command_receipts VALUES (?,?,?,?,?)",
                    [command, "probe", "0" * 64, None, 0],
                ],
                [
                    "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [
                        event,
                        "probe",
                        1,
                        "system",
                        None,
                        "probe",
                        None,
                        command,
                        None,
                        None,
                        "ProbeV1",
                        1,
                        "{}",
                        "0" * 64,
                        2,
                        0,
                    ],
                ],
                ["INSERT INTO audit_event_results VALUES (?,?,?,?)", [event, 0, "probe", "probe"]],
            ],
            "reject": [
                ["UPDATE audit_events SET action_type='changed' WHERE audit_event_id=?", [event]],
                ["DELETE FROM audit_events WHERE audit_event_id=?", [event]],
                [
                    "UPDATE audit_event_results SET result_id='changed' WHERE audit_event_id=?",
                    [event],
                ],
                ["DELETE FROM audit_event_results WHERE audit_event_id=?", [event]],
            ],
        }
    ]


def generate(root=ROOT, *, check=False):
    manifest = MigrationManifest.load(root / "src/core/soma/db/migrations")
    connection = load_sqlcipher_driver().connect(":memory:", isolation_level=None)
    try:
        connection.execute("PRAGMA key = \"x'" + secrets.token_bytes(32).hex() + "'\"")
        connection.execute("PRAGMA foreign_keys=ON")
        apply_entries(
            connection,
            manifest,
            instance_id="4d204e28-3a66-43cb-81ca-a31cc94c9b11",
            utc_clock=lambda: 0,
        )
        value = {
            "version": 1,
            "generation": manifest.generation,
            "lineage": manifest.lineage(),
            "shape": schema_shape(connection),
            "append_only_probes": audit_probes()
            if any(entry.migration_id == "M00.003" for entry in manifest.entries)
            else [],
        }
    finally:
        connection.close()
    path = root / "src/core/soma/db/schema_manifest.json"
    content = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError("Committed schema manifest differs from accepted migrations")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    generate(check=parser.parse_args().check)
