import os
import re
import sqlite3
import tempfile

from soma.foundation.build import current_build
from soma.foundation.errors import SomaError
from soma.foundation.filesystem import OwnedArtifact, remove_owned
from soma.foundation.filesystem.windows_acl import protect_owner
from soma.foundation.persistence.connections import persistence_failure
from soma.foundation.persistence.manifest import MigrationManifest, migration_error
from soma.foundation.persistence.schema_verify import reconcile_ledger, verify_schema
from soma.foundation.time import utc_epoch_seconds


def iter_migration_statements(text):
    buffer = ""
    for char in text:
        buffer += char
        if char == ";" and sqlite3.complete_statement(buffer):
            yield buffer.strip()
            buffer = ""
    tail = re.sub(r"/\*.*?\*/|--[^\n]*", "", buffer, flags=re.S).strip()
    if tail:
        raise migration_error("MIGRATION_SQL_INCOMPLETE")


def apply_entries(connection, manifest, *, start=0, instance_id=None, utc_clock=utc_epoch_seconds):
    # Freeze all accepted SQL before acquiring writer authority.
    entries = [
        (entry, tuple(iter_migration_statements(manifest.raw_bytes(entry).decode())))
        for entry in manifest.entries[start:]
    ]
    for entry, statements in entries:
        try:
            connection.execute("BEGIN IMMEDIATE")
            for sql in statements:
                token = (
                    re.sub(r"/\*.*?\*/|--[^\n]*", "", sql, flags=re.S).lstrip().split()[0].upper()
                )
                if token not in {"CREATE", "ALTER", "DROP", "INSERT", "UPDATE", "DELETE"}:
                    raise migration_error("MIGRATION_SQL_UNSAFE")
                connection.execute(sql)
            if entry.migration_id == "M00.001":
                connection.execute(
                    "INSERT INTO instance_metadata(singleton,data_instance_id,created_at_utc) VALUES (1,?,?)",
                    (instance_id, utc_clock()),
                )
            connection.execute(
                "INSERT INTO schema_migrations(migration_id,owner_scope,content_sha256,applied_at_utc,application_version) VALUES (?,?,?,?,?)",
                (
                    entry.migration_id,
                    entry.owner_scope,
                    entry.content_sha256,
                    utc_clock(),
                    current_build().application_version,
                ),
            )
            connection.execute("COMMIT")
        except BaseException as exc:
            if connection.in_transaction:
                connection.rollback()
            if isinstance(exc, SomaError) or not isinstance(exc, Exception):
                raise
            raise persistence_failure(exc) from None


class MigrationRunner:
    def __init__(self, factory, manifest=None, *, utc_clock=utc_epoch_seconds):
        self.factory = factory
        self.manifest = manifest if manifest is not None else MigrationManifest.load()
        self.utc_clock = utc_clock

    def initialize_or_migrate(self):
        self.factory.lease.require()
        self.manifest.validate()
        path = self.factory.database_path
        if path.exists():
            connection = self.factory.open()
            try:
                start = reconcile_ledger(connection, self.manifest, complete=False)
                apply_entries(
                    connection,
                    self.manifest,
                    start=start,
                    instance_id=self.factory.lease.instance_id,
                    utc_clock=self.utc_clock,
                )
                verify_schema(connection, self.manifest, instance_id=self.factory.lease.instance_id)
            finally:
                connection.close()
        else:
            fd, name = tempfile.mkstemp(prefix=".soma-init-", suffix=".db", dir=path.parent)
            created = os.fstat(fd)
            os.close(fd)
            stage = path.parent / os.path.basename(name)
            try:
                connection = self.factory.at(stage).open(journal="delete")
                try:
                    apply_entries(
                        connection,
                        self.manifest,
                        instance_id=self.factory.lease.instance_id,
                        utc_clock=self.utc_clock,
                    )
                    verify_schema(
                        connection, self.manifest, instance_id=self.factory.lease.instance_id
                    )
                finally:
                    connection.close()
                protect_owner(stage)
                staged = OwnedArtifact.capture(
                    self.factory.lease.config.instance_root,
                    stage.relative_to(self.factory.lease.config.instance_root),
                )
                if (staged.device, staged.inode) != (created.st_dev, created.st_ino):
                    raise migration_error("MIGRATION_STAGE_OWNERSHIP_CHANGED")
                with stage.open("r+b") as stream:
                    os.fsync(stream.fileno())
                if os.name != "nt":
                    raise migration_error("MIGRATION_PLATFORM_UNSUPPORTED")
                os.rename(stage, path)  # Never overwrite a concurrently published database.
                connection = self.factory.open()  # Establish and verify persisted WAL policy.
                connection.close()
            except BaseException:
                if stage.exists():
                    artifact = OwnedArtifact.capture(
                        self.factory.lease.config.instance_root,
                        stage.relative_to(self.factory.lease.config.instance_root),
                    )
                    if (artifact.device, artifact.inode) == (created.st_dev, created.st_ino):
                        remove_owned(self.factory.lease.config.instance_root, artifact)
                raise
        return self.manifest.generation
