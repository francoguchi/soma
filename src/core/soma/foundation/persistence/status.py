"""Read-only migration inspection: never bootstrap, checkpoint, repair or log."""

import msvcrt

from soma.foundation.identity import require_uuid4
from soma.foundation.persistence.connections import load_sqlcipher_driver
from soma.foundation.persistence.manifest import MigrationManifest
from soma.foundation.persistence.schema_verify import verify_schema
from soma.foundation.security.live_key import LiveDataKeyProvider
from soma.foundation.security.sqlcipher_provider import SqlCipherSecurity
from soma.foundation.strict_json import loads_strict_bytes


class InspectionLease:
    def __init__(self, config, instance_id):
        self.config, self.instance_id, self.held = config, instance_id, True

    def require(self):
        if not self.held:
            raise ValueError("Inspection ownership was released")


def migration_status(config):
    try:
        if config.path("runtime", "runtime.json").exists():
            from soma.runtime.control import verify_current

            verified = verify_current(config, allow_starting=True)
            return {
                "status": "verified_live_current"
                if verified and verified[0]
                else "locked_unverified"
            }
        database = config.path("data", "soma.db")
        if not database.exists():
            return {"status": "not_initialized"}
        lock = config.path("data", "soma.instance.lock")
        if not lock.is_file():
            return {"status": "invalid_layout"}
        # Opening an existing lock does not create files or rewrite its bytes.
        with lock.open("r+b") as handle:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                return {"status": "locked_unverified"}
            try:
                if any(
                    database.with_name(database.name + suffix).exists()
                    for suffix in ("-wal", "-shm")
                ):
                    return {"status": "unsafe_sidecars"}
                identity = loads_strict_bytes(
                    config.path("data", "instance.json").read_bytes(), max_bytes=4096
                )
                lease = InspectionLease(config, require_uuid4(identity["data_instance_id"]))
                security = SqlCipherSecurity(LiveDataKeyProvider(lease))
                connection = load_sqlcipher_driver().connect(
                    database.as_uri() + "?mode=ro&immutable=1", uri=True, isolation_level=None
                )
                try:
                    security.key_connection(connection)
                    security.verify(connection)
                    connection.execute("PRAGMA foreign_keys=ON")
                    connection.execute("PRAGMA query_only=ON")
                    manifest = MigrationManifest.load()
                    rows = connection.execute(
                        "SELECT migration_id,owner_scope,content_sha256 FROM schema_migrations"
                    ).fetchall()
                    expected = manifest.lineage()
                    ids = {r[0] for r in rows}
                    if ids - {r[0] for r in expected}:
                        return {"status": "unsupported_future_schema"}
                    if ids != {r[0] for r in expected[: len(rows)]} or len(rows) != len(ids):
                        return {"status": "ledger_mismatch"}
                    actual = {r[0]: list(r) for r in rows}
                    if any(actual[r[0]] != r for r in expected[: len(rows)]):
                        return {"status": "drift"}
                    if (
                        connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]
                        or connection.execute("PRAGMA foreign_key_check").fetchall()
                    ):
                        return {"status": "integrity_failure"}
                    if len(rows) < len(expected):
                        return {"status": "pending"}
                    try:
                        verify_schema(connection, manifest, instance_id=lease.instance_id)
                    except Exception:
                        return {"status": "drift"}
                    return {"status": "current"}
                finally:
                    lease.held = False
                    connection.close()
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    except Exception:
        return {"status": "inspection_failure"}
