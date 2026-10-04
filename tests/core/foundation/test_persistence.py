import copy
import hashlib
import json
import secrets
import sqlite3
import threading
from pathlib import Path
from importlib.resources import files

import pytest
import sqlcipher3

from soma.foundation.config import RuntimeConfig
from soma.foundation.development.database import SeedContributor, factory_for_lease, rebuild, seed
from soma.foundation.errors import SomaError
from soma.foundation.persistence.connections import ConnectionFactory
from soma.foundation.persistence.instance import InstanceLease
from soma.foundation.persistence.manifest import MigrationManifest
from soma.foundation.persistence.migrations import (
    MigrationRunner,
    apply_entries,
    iter_migration_statements,
)
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.persistence.schema_verify import schema_shape, verify_fk_indexes, verify_schema
from soma.foundation.persistence.snapshot import SnapshotProvider
from soma.foundation.security.dpapi import WindowsDpapiProvider
from soma.foundation.security.live_key import LiveDataKeyProvider
from soma.foundation.security.sqlcipher_provider import SqlCipherSecurity
from tools import schema_manifest


@pytest.fixture
def database(tmp_path):
    config = RuntimeConfig(tmp_path / "instance", tmp_path / "checkout", "test")
    with InstanceLease(config) as lease:
        factory = factory_for_lease(lease)
        manifest = MigrationManifest.load()
        assert MigrationRunner(factory, manifest).initialize_or_migrate() == manifest.generation
        yield config, lease, factory, manifest


def test_native_dpapi_roundtrip_binding_length_and_tamper():
    from soma.foundation.identity import new_uuid4

    provider = WindowsDpapiProvider()
    identity = new_uuid4()
    secret = secrets.token_bytes(32)
    protected = provider.protect_current_user(secret, "live_data_dek", identity)
    assert secret not in protected
    assert provider.unprotect_current_user(protected, "live_data_dek", identity) == secret
    for purpose, binding, blob in [
        ("run_control", identity, protected),
        ("live_data_dek", new_uuid4(), protected),
        ("live_data_dek", identity, protected[:-1]),
        ("live_data_dek", identity, protected[:-1] + bytes([protected[-1] ^ 1])),
    ]:
        with pytest.raises(SomaError):
            provider.unprotect_current_user(blob, purpose, binding)
    with pytest.raises(SomaError):
        provider.protect_current_user(b"short", "live_data_dek", identity)


def test_native_encrypted_bootstrap_profile_restart_and_wrong_key(database):
    config, lease, factory, manifest = database
    assert MigrationRunner(factory, manifest).initialize_or_migrate() == manifest.generation
    connection = factory.open()
    try:
        assert connection.execute("PRAGMA cipher_version").fetchone() == ("4.17.0 community",)
        verify_schema(connection, manifest, instance_id=lease.instance_id, deep=True)
        for name, expected in [
            ("foreign_keys", 1),
            ("busy_timeout", 5000),
            ("trusted_schema", 0),
            ("temp_store", 2),
            ("synchronous", 2),
            ("secure_delete", 2),
            ("read_uncommitted", 0),
            ("wal_autocheckpoint", 1000),
        ]:
            assert connection.execute(f"PRAGMA {name}").fetchone() == (expected,)
        identity = lease.instance_id
        key_file = config.path("data", "live-key.dpapi").read_bytes()
    finally:
        connection.close()
    assert not factory.database_path.read_bytes().startswith(b"SQLite format 3\0")
    plaintext = sqlite3.connect(str(factory.database_path))
    try:
        with pytest.raises(sqlite3.DatabaseError):
            plaintext.execute("SELECT * FROM schema_migrations").fetchall()
    finally:
        plaintext.close()

    class WrongKey:
        def unwrap_live_dek(self):
            return secrets.token_bytes(32)

    with pytest.raises(SomaError, match="Protected installation"):
        ConnectionFactory(lease, SqlCipherSecurity(WrongKey())).open()
    lease.__exit__()
    with InstanceLease(config) as reopened:
        assert reopened.instance_id == identity
        factory = factory_for_lease(reopened)
        assert config.path("data", "live-key.dpapi").read_bytes() == key_file
        assert MigrationRunner(factory).initialize_or_migrate() == MigrationManifest.load().generation


def test_missing_key_never_regenerates_for_existing_database(database):
    config, lease, _, _ = database
    config.path("data", "live-key.dpapi").unlink()
    with pytest.raises(SomaError):
        LiveDataKeyProvider(lease).prepare()
    assert not config.path("data", "live-key.dpapi").exists()


@pytest.mark.parametrize(
    "pragma,unsafe",
    [
        ("foreign_keys", "OFF"),
        ("busy_timeout", "0"),
        ("trusted_schema", "ON"),
        ("temp_store", "FILE"),
        ("synchronous", "OFF"),
        ("secure_delete", "OFF"),
        ("read_uncommitted", "ON"),
        ("wal_autocheckpoint", "10"),
    ],
)
def test_ignored_safety_setting_blocks_and_closes(database, pragma, unsafe):
    _, lease, factory, _ = database
    opened = []

    class Wrapper:
        def __init__(self, raw):
            self.raw = raw

        def execute(self, sql, *args):
            if sql.startswith(f"PRAGMA {pragma}="):
                return self.raw.execute(f"PRAGMA {pragma}={unsafe}")
            return self.raw.execute(sql, *args)

        def __getattr__(self, name):
            return getattr(self.raw, name)

    def connect(*args, **kwargs):
        raw = sqlcipher3.connect(*args, **kwargs)
        opened.append(raw)
        return Wrapper(raw)

    with pytest.raises(SomaError):
        ConnectionFactory(lease, factory.security, connector=connect).open()
    with pytest.raises(sqlcipher3.ProgrammingError):
        opened[0].execute("SELECT 1")


def test_extension_disable_failure_is_safe_and_closes(database):
    _, lease, factory, _ = database
    opened = []

    class Wrapper:
        def __init__(self, raw):
            self.raw = raw

        def __getattr__(self, name):
            return getattr(self.raw, name)

        def enable_load_extension(self, enabled):
            raise NotImplementedError("secret provider detail")

    def connect(*args, **kwargs):
        raw = sqlcipher3.connect(*args, **kwargs)
        opened.append(raw)
        return Wrapper(raw)

    with pytest.raises(SomaError) as caught:
        ConnectionFactory(lease, factory.security, connector=connect).open()
    assert "secret provider detail" not in str(caught.value)
    with pytest.raises(sqlcipher3.ProgrammingError):
        opened[0].execute("SELECT 1")


def test_readonly_same_generation_and_thread_bound_connection(database):
    _, _, factory, _ = database
    with ReadSnapshot(factory, utc_clock=lambda: 100) as snapshot:
        before = snapshot.connection.execute(
            "SELECT application_version FROM schema_migrations"
        ).fetchone()
        writer = factory.open()
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("UPDATE schema_migrations SET application_version=?", ("synthetic-later",))
        writer.execute("COMMIT")
        writer.close()
        assert (
            snapshot.connection.execute(
                "SELECT application_version FROM schema_migrations"
            ).fetchone()
            == before
        )
        assert snapshot.as_of_utc_s == 100
        with pytest.raises(sqlcipher3.OperationalError):
            snapshot.connection.execute("CREATE TABLE forbidden(x)")
        errors = []

        def cross_thread():
            try:
                snapshot.connection.execute("SELECT 1")
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=cross_thread)
        thread.start()
        thread.join(5)
        assert len(errors) == 1 and isinstance(errors[0], sqlcipher3.ProgrammingError)
    with ReadSnapshot(factory) as snapshot:
        assert snapshot.connection.execute(
            "SELECT application_version FROM schema_migrations"
        ).fetchone() == ("synthetic-later",)


@pytest.mark.parametrize(
    "failure", ["BEGIN", "SELECT count(*) FROM sqlite_schema", "COMMIT", "body"]
)
def test_snapshot_failure_cleanup(database, failure):
    _, lease, factory, _ = database
    opened = []

    class Wrapper:
        def __init__(self, raw):
            self.raw = raw

        def __getattr__(self, name):
            return getattr(self.raw, name)

        def execute(self, sql, *args):
            if sql == failure:
                raise RuntimeError("private diagnostic")
            return self.raw.execute(sql, *args)

    def connect(*args, **kwargs):
        raw = sqlcipher3.connect(*args, **kwargs)
        opened.append(raw)
        return Wrapper(raw)

    faulty = ConnectionFactory(lease, factory.security, connector=connect)
    with pytest.raises(SomaError):
        with ReadSnapshot(faulty):
            if failure == "body":
                raise RuntimeError("private body")
    with pytest.raises(sqlcipher3.ProgrammingError):
        opened[0].execute("SELECT 1")


def test_sql_parser_trigger_quotes_comments_and_multiple_statements():
    text = "-- comment;\nCREATE TABLE t(id INTEGER PRIMARY KEY, value INTEGER); CREATE TABLE u(id INTEGER);\nCREATE TRIGGER guard BEFORE UPDATE ON t BEGIN SELECT CASE WHEN NEW.value<0 THEN RAISE(ABORT,'negative; forbidden') END; END;\n-- tail;\n"
    statements = tuple(iter_migration_statements(text))
    assert len(statements) == 3
    assert "negative; forbidden" in statements[2]
    with pytest.raises(SomaError):
        tuple(iter_migration_statements("CREATE TABLE incomplete(x)"))


@pytest.mark.parametrize(
    "sql",
    [
        "CREATE TABLE unknown(x TEXT) STRICT",
        "DROP TABLE instance_metadata",
        "UPDATE schema_migrations SET content_sha256='0000000000000000000000000000000000000000000000000000000000000000'",
        "ALTER TABLE instance_metadata ADD COLUMN extra TEXT",
        "CREATE TRIGGER sqliteXunknown AFTER INSERT ON instance_metadata BEGIN SELECT 1; END",
    ],
)
def test_schema_and_ledger_drift_blocks(database, sql):
    _, lease, factory, manifest = database
    connection = factory.open()
    try:
        connection.execute(sql)
        with pytest.raises(SomaError):
            verify_schema(connection, manifest, instance_id=lease.instance_id)
    finally:
        connection.close()


def test_manifest_hash_dependencies_duplicate_and_unlisted_files(tmp_path):
    original = Path(str(MigrationManifest.load().directory))
    directory = tmp_path / "migrations"
    (directory / "00").mkdir(parents=True)
    sql = directory / "00/001_bootstrap.sql"
    sql.write_bytes((original / "00/001_bootstrap.sql").read_bytes())
    accepted = json.loads((original / "manifest.json").read_text())
    for mutation in [
        lambda value: value["migrations"][0].update(content_sha256="0" * 64),
        lambda value: value["migrations"][0].update(depends_on=["M00.002"]),
        lambda value: value["migrations"].append(copy.deepcopy(value["migrations"][0])),
    ]:
        value = copy.deepcopy(accepted)
        mutation(value)
        (directory / "manifest.json").write_text(json.dumps(value))
        with pytest.raises(SomaError):
            MigrationManifest.load(directory)
    (directory / "manifest.json").write_text(json.dumps(accepted))
    (directory / "00/999_unlisted.sql").write_text("SELECT 1;\n")
    with pytest.raises(SomaError):
        MigrationManifest.load(directory)


@pytest.mark.parametrize(
    "index,accepted",
    [
        ("CREATE INDEX idx ON child(a,b,c)", True),
        ("CREATE INDEX idx ON child(b,a)", False),
        ("CREATE INDEX idx ON child(a, lower(b))", False),
        ("CREATE INDEX idx ON child(a COLLATE NOCASE,b)", False),
        ("CREATE INDEX idx ON child(a,b) WHERE c>0", False),
        (None, False),
    ],
)
def test_fk_leading_prefix_indexes(index, accepted):
    connection = sqlcipher3.connect(":memory:", isolation_level=None)
    try:
        connection.execute("CREATE TABLE parent(a TEXT,b TEXT,PRIMARY KEY(a,b))")
        connection.execute(
            "CREATE TABLE child(a TEXT,b TEXT,c INTEGER,FOREIGN KEY(a,b) REFERENCES parent(a,b))"
        )
        if index:
            connection.execute(index)
        if accepted:
            verify_fk_indexes(connection)
        else:
            with pytest.raises(SomaError):
                verify_fk_indexes(connection)
    finally:
        connection.close()


def test_native_consistent_encrypted_snapshot_and_later_mutation(database):
    config, lease, factory, manifest = database
    snapshot = SnapshotProvider(factory, manifest).create("synthetic-snapshot.db")
    writer = factory.open()
    writer.execute("BEGIN IMMEDIATE")
    writer.execute("UPDATE schema_migrations SET application_version='later-synthetic'")
    writer.execute("COMMIT")
    writer.close()
    assert snapshot.path.parent == config.path("backups")
    assert snapshot.data_instance_id == lease.instance_id
    assert snapshot.sha256 == hashlib.sha256(snapshot.path.read_bytes()).hexdigest()
    assert not snapshot.path.read_bytes().startswith(b"SQLite format 3\0")
    connection = factory.at(snapshot.path).open(read_only=True, journal="delete")
    try:
        verify_schema(connection, manifest, instance_id=lease.instance_id, deep=True)
        assert connection.execute(
            "SELECT application_version FROM schema_migrations"
        ).fetchone() != ("later-synthetic",)
    finally:
        connection.close()


def test_snapshot_budget_and_integrity_failure_never_publish(database):
    config, _, factory, manifest = database
    with pytest.raises(SomaError):
        SnapshotProvider(factory, manifest, monotonic_clock=lambda: 10).create(
            "timed-out.db", timeout_ms=0
        )
    assert list(config.path("backups").iterdir()) == []
    connection = factory.open()
    connection.execute("CREATE TABLE unwanted(x INTEGER)")
    connection.close()
    with pytest.raises(SomaError):
        SnapshotProvider(factory, manifest).create("invalid.db")
    assert list(config.path("backups").iterdir()) == []


def test_reset_is_explicit_preserves_ordinary_data_and_requires_quiescence(tmp_path):
    config = RuntimeConfig(tmp_path / "instance", tmp_path / "checkout", "development")
    identity = rebuild(config, confirmation="RESET")
    with InstanceLease(config) as lease:
        factory = factory_for_lease(lease)
        connection = factory.open()
        connection.execute("UPDATE schema_migrations SET application_version='synthetic-preserved'")
        connection.close()
        MigrationRunner(factory).initialize_or_migrate()
        connection = factory.open()
        assert connection.execute(
            "SELECT application_version FROM schema_migrations"
        ).fetchone() == ("synthetic-preserved",)
        connection.close()
        with pytest.raises(SomaError):
            rebuild(config, confirmation="RESET")
    with pytest.raises(SomaError):
        rebuild(config, confirmation="yes")
    config.path("runtime", "runtime.json").write_text("unverified record")
    with pytest.raises(SomaError):
        rebuild(config, confirmation="RESET")
    config.path("runtime", "runtime.json").unlink()
    assert rebuild(config, confirmation="RESET") == identity
    with InstanceLease(config) as lease:
        connection = factory_for_lease(lease).open()
        assert connection.execute(
            "SELECT application_version FROM schema_migrations"
        ).fetchone() == ("0.1.0.dev0",)
        connection.close()


def test_seed_failure_rolls_back_and_order_is_explicit(database):
    _, _, factory, _ = database
    connection = factory.open()

    def fail(conn):
        conn.execute("UPDATE schema_migrations SET application_version='uncommitted'")
        raise RuntimeError("seed failed")

    try:
        with pytest.raises(SomaError, match="incomplete"):
            seed(connection, (SeedContributor("synthetic", (), fail),))
        assert connection.execute(
            "SELECT application_version FROM schema_migrations"
        ).fetchone() == ("0.1.0.dev0",)
        with pytest.raises(SomaError):
            seed(connection, (SeedContributor("second", ("missing",), lambda conn: None),))
    finally:
        connection.close()


def test_schema_manifest_offline_sync():
    schema_manifest.generate(check=True)


def test_unsupported_journal_rejected_before_driver(database):
    _, _, factory, _ = database
    with pytest.raises(SomaError):
        factory.open(journal="DELETE; DROP TABLE schema_migrations")


def test_future_ledger_and_identity_mismatch_block(database):
    _, lease, factory, manifest = database
    connection = factory.open()
    try:
        connection.execute(
            "INSERT INTO schema_migrations VALUES (?,?,?,?,?)",
            ("M99.001", "99", "0" * 64, 0, "synthetic"),
        )
        with pytest.raises(SomaError):
            verify_schema(connection, manifest, instance_id=lease.instance_id)
        connection.execute("DELETE FROM schema_migrations WHERE migration_id=?", ("M99.001",))
        connection.execute(
            "UPDATE instance_metadata SET data_instance_id=?",
            ("4d204e28-3a66-43cb-81ca-a31cc94c9b11",),
        )
        with pytest.raises(SomaError):
            verify_schema(connection, manifest, instance_id=lease.instance_id)
    finally:
        connection.close()


def test_writer_busy_maps_to_retry_without_partial_write(database):
    _, lease, factory, manifest = database
    holder = factory.open()
    contender = factory.open()
    try:
        holder.execute("BEGIN IMMEDIATE")
        with pytest.raises(SomaError) as caught:
            apply_entries(contender, manifest, instance_id=lease.instance_id)
        assert caught.value.code == "PERSISTENCE_BUSY"
        assert caught.value.recoverability == "retry"
        assert not contender.in_transaction
        holder.execute("ROLLBACK")
        verify_schema(contender, manifest, instance_id=lease.instance_id)
    finally:
        contender.close()
        holder.close()


@pytest.mark.parametrize("failure", ["cipher", "publication"])
def test_snapshot_provider_failure_preserves_foreign_output_and_cleans_stage(database, failure):
    config, lease, factory, manifest = database
    target = config.path("backups", "result.db")

    class Wrapper:
        def __init__(self, raw):
            self.raw = raw

        def __getattr__(self, name):
            return getattr(self.raw, name)

        def backup(self, destination, **kwargs):
            if failure == "cipher":
                raise RuntimeError("private cipher/provider failure")
            self.raw.backup(destination.raw, **kwargs)
            target.write_bytes(b"foreign publication")

    def connect(*args, **kwargs):
        return Wrapper(sqlcipher3.connect(*args, **kwargs))

    faulty = ConnectionFactory(lease, factory.security, connector=connect)
    with pytest.raises(SomaError) as caught:
        SnapshotProvider(faulty, manifest).create("result.db")
    assert "private cipher" not in str(caught.value)
    assert not any(
        path.name.startswith(".soma-snapshot-") for path in config.path("backups").iterdir()
    )
    if failure == "publication":
        assert target.read_bytes() == b"foreign publication"
    else:
        assert not target.exists()


def test_schema_append_only_probes_roll_back_and_reject_weakened_behavior(database):
    _, lease, factory, manifest = database
    connection = factory.open()
    try:
        connection.execute(
            "CREATE TABLE synthetic_evidence(id INTEGER PRIMARY KEY,value TEXT) STRICT"
        )
        connection.execute(
            "CREATE TRIGGER synthetic_immutable BEFORE UPDATE ON synthetic_evidence BEGIN SELECT RAISE(ABORT,'immutable'); END"
        )
        expected = json.loads(files("soma.db").joinpath("schema_manifest.json").read_text())
        expected["shape"] = schema_shape(connection)
        expected["append_only_probes"] = [
            {
                "setup": [
                    ["INSERT INTO synthetic_evidence(id,value) VALUES (?,?)", [1, "synthetic"]]
                ],
                "reject": [["UPDATE synthetic_evidence SET value=? WHERE id=?", ["changed", 1]]],
            }
        ]
        verify_schema(connection, manifest, instance_id=lease.instance_id, expected=expected)
        assert connection.execute("SELECT * FROM synthetic_evidence").fetchall() == []
        connection.execute("DROP TRIGGER synthetic_immutable")
        connection.execute(
            "CREATE TRIGGER synthetic_immutable BEFORE UPDATE ON synthetic_evidence BEGIN SELECT 1; END"
        )
        with pytest.raises(SomaError):
            verify_schema(connection, manifest, instance_id=lease.instance_id, expected=expected)
        # Independently isolate the behavioral probe even when structural truth is supplied.
        expected["shape"] = schema_shape(connection)
        with pytest.raises(SomaError):
            verify_schema(connection, manifest, instance_id=lease.instance_id, expected=expected)
        assert connection.execute("SELECT * FROM synthetic_evidence").fetchall() == []
    finally:
        connection.close()
