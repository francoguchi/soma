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


def reference_probes():
    command = "83838383-8383-4383-8383-838383838383"
    customer = "84848484-8484-4484-8484-848484848484"
    claim = "85858585-8585-4585-8585-858585858585"
    event = "86868686-8686-4686-8686-868686868686"
    actor = "87878787-8787-4787-8787-878787878787"
    return [
        {
            "observe": [
                [
                    "SELECT singleton_guard,matching_profile_id FROM reference_metadata",
                    [],
                    [[1, "UNICODE_MATCH_V1"]],
                ]
            ],
            "setup": [
                [
                    "INSERT INTO command_receipts VALUES (?,?,?,?,?)",
                    [command, "reference.probe", "0" * 64, None, 0],
                ],
                [
                    "INSERT OR IGNORE INTO local_admin_credentials VALUES (1,?,'probe',1,0,0)",
                    [actor],
                ],
                [
                    "INSERT INTO local_user_profiles SELECT actor_id,1,'probe',1,0,0 FROM local_admin_credentials WHERE NOT EXISTS(SELECT 1 FROM local_user_profiles)",
                    [],
                ],
                [
                    "INSERT INTO customer_organizations VALUES (?,'probe','probe','active',1,0,0)",
                    [customer],
                ],
                [
                    "INSERT INTO customer_org_identifiers VALUES (?,?,'customer_account_code','probe','probe','active',0,NULL,?,NULL)",
                    [claim, customer, command],
                ],
                [
                    "INSERT INTO reference_lifecycle_events VALUES (?,'customer_organization',?,'created',0,?,NULL)",
                    [event, customer, command],
                ],
                [
                    "UPDATE customer_org_identifiers SET lifecycle_state='superseded',superseded_at_utc=0,superseded_command_id=? WHERE customer_org_identifier_id=?",
                    [command, claim],
                ],
            ],
            "reject": [
                ["DELETE FROM reference_metadata", []],
                [
                    "UPDATE local_user_profiles SET local_user_profile_id=? WHERE singleton_guard=1",
                    [customer],
                ],
                ["DELETE FROM local_user_profiles", []],
                [
                    "UPDATE customer_organizations SET customer_org_id=? WHERE customer_org_id=?",
                    [actor, customer],
                ],
                ["DELETE FROM customer_organizations WHERE customer_org_id=?", [customer]],
                [
                    "UPDATE customer_org_identifiers SET value_text='changed' WHERE customer_org_identifier_id=?",
                    [claim],
                ],
                [
                    "DELETE FROM customer_org_identifiers WHERE customer_org_identifier_id=?",
                    [claim],
                ],
                [
                    "UPDATE reference_lifecycle_events SET event_type='archived' WHERE reference_lifecycle_event_id=?",
                    [event],
                ],
                [
                    "DELETE FROM reference_lifecycle_events WHERE reference_lifecycle_event_id=?",
                    [event],
                ],
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
        if any(entry.migration_id == "M01.001" for entry in manifest.entries):
            value["append_only_probes"] += reference_probes()
        if any(entry.migration_id == "M01.002" for entry in manifest.entries):
            value["append_only_probes"] += contact_probes()
        if any(entry.migration_id == "M01.003" for entry in manifest.entries):
            value["append_only_probes"] += dispatch_probes()
    finally:
        connection.close()
    path = root / "src/core/soma/db/schema_manifest.json"
    content = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise ValueError("Committed schema manifest differs from accepted migrations")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")


def contact_probes():
    command = "91919191-9191-4191-8191-919191919191"
    customer = "92929292-9292-4292-8292-929292929292"
    contact = "93939393-9393-4393-8393-939393939393"
    channel = "94949494-9494-4494-8494-949494949494"
    affiliation = "95959595-9595-4595-8595-959595959595"
    return [
        {
            "setup": [
                [
                    "INSERT INTO command_receipts VALUES (?,?,?,?,?)",
                    [command, "reference.probe", "0" * 64, None, 0],
                ],
                [
                    "INSERT INTO customer_organizations VALUES (?,'probe','probe','active',1,0,0)",
                    [customer],
                ],
                ["INSERT INTO contacts VALUES (?,'probe','probe','active',1,0,0)", [contact]],
                [
                    "INSERT INTO contact_channels VALUES (?,?,'email','probe@example.com','probe@example.com','active',1,0,0)",
                    [channel, contact],
                ],
                [
                    "INSERT INTO contact_affiliations VALUES (?,?,?,1,0,NULL,?,NULL)",
                    [affiliation, contact, customer, command],
                ],
                [
                    "UPDATE contact_channels SET lifecycle_state='archived',revision=2 WHERE contact_channel_id=?",
                    [channel],
                ],
                [
                    "UPDATE contact_affiliations SET is_current=0,closed_at_utc=0,closed_command_id=? WHERE contact_affiliation_id=?",
                    [command, affiliation],
                ],
            ],
            "reject": [
                ["UPDATE contacts SET contact_id=? WHERE contact_id=?", [customer, contact]],
                ["DELETE FROM contacts WHERE contact_id=?", [contact]],
                [
                    "UPDATE contact_channels SET value_text='changed',revision=3 WHERE contact_channel_id=?",
                    [channel],
                ],
                ["DELETE FROM contact_channels WHERE contact_channel_id=?", [channel]],
                [
                    "UPDATE contact_affiliations SET customer_org_id=? WHERE contact_affiliation_id=?",
                    [customer, affiliation],
                ],
                ["DELETE FROM contact_affiliations WHERE contact_affiliation_id=?", [affiliation]],
            ],
        }
    ]


def dispatch_probes():
    standalone = "96969696-9696-4696-8696-969696969696"
    derived = "97979797-9797-4797-8797-979797979797"
    return [
        {
            "setup": [
                [
                    "INSERT INTO dispatch_locations VALUES (?,'probe','probe','standalone','address','active',1,0,0)",
                    [standalone],
                ],
                [
                    "INSERT INTO dispatch_locations VALUES (?,'probe','probe','site_derived',NULL,'active',1,0,0)",
                    [derived],
                ],
            ],
            "reject": [
                [
                    "UPDATE dispatch_locations SET dispatch_location_id=? WHERE dispatch_location_id=?",
                    [derived, standalone],
                ],
                [
                    "UPDATE dispatch_locations SET address_mode='site_derived',standalone_address_text=NULL WHERE dispatch_location_id=?",
                    [standalone],
                ],
                [
                    "UPDATE dispatch_locations SET created_at_utc=1,updated_at_utc=1 WHERE dispatch_location_id=?",
                    [standalone],
                ],
                [
                    "UPDATE dispatch_locations SET standalone_address_text='address' WHERE dispatch_location_id=?",
                    [derived],
                ],
                ["DELETE FROM dispatch_locations WHERE dispatch_location_id=?", [standalone]],
                ["DELETE FROM dispatch_locations WHERE dispatch_location_id=?", [derived]],
            ],
        }
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    generate(check=parser.parse_args().check)
