import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from soma.foundation.errors import SomaError
from soma.foundation.filesystem import OwnedArtifact, remove_owned
from soma.foundation.filesystem.windows_acl import protect_owner
from soma.foundation.persistence.connections import persistence_failure
from soma.foundation.persistence.manifest import MigrationManifest
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.persistence.schema_verify import verify_schema
from soma.foundation.time import Deadline, monotonic_ns


@dataclass(frozen=True, slots=True)
class SnapshotDescriptor:
    path: Path
    size_bytes: int
    sha256: str
    data_instance_id: str
    as_of_utc_s: int
    migration_generation: int


class SnapshotProvider:
    def __init__(self, factory, manifest=None, *, monotonic_clock=monotonic_ns):
        self.factory = factory
        self.manifest = manifest if manifest is not None else MigrationManifest.load()
        self.clock = monotonic_clock

    def create(self, relative: str, *, timeout_ms: int = 5000) -> SnapshotDescriptor:
        lease = self.factory.lease
        lease.require()
        config = lease.config
        if self.factory.database_path != config.path("data", "soma.db"):
            raise SomaError(
                "SNAPSHOT_IDENTITY_INVALID", "Snapshot source is not the canonical database."
            )
        target = config.path("backups", relative)
        if target.exists() or not target.parent.is_dir():
            raise SomaError(
                "SNAPSHOT_TARGET_INVALID", "Snapshot publication target is unavailable."
            )
        deadline = Deadline.after_ms(timeout_ms, self.clock)
        fd, name = tempfile.mkstemp(prefix=".soma-snapshot-", suffix=".db", dir=target.parent)
        created = os.fstat(fd)
        os.close(fd)
        stage = target.parent / os.path.basename(name)
        destination = None
        try:
            destination = self.factory.at(stage).open(journal="delete")
            with ReadSnapshot(self.factory) as source:
                row = source.connection.execute(
                    "SELECT data_instance_id FROM instance_metadata WHERE singleton=1"
                ).fetchone()
                if row != (lease.instance_id,):
                    raise SomaError(
                        "SNAPSHOT_IDENTITY_INVALID", "Snapshot data identity is incompatible."
                    )
                as_of = source.as_of_utc_s

                def progress(status, remaining, total):
                    if deadline.expired() or status in (5, 6):
                        raise SomaError(
                            "PERSISTENCE_BUSY",
                            "Snapshot acquisition exceeded its bounded budget.",
                            "retry",
                        )

                source.connection.backup(destination, pages=128, progress=progress, sleep=0.01)
            # Consistency read is now closed. Verification/hash/publication hold no source snapshot.
            verify_schema(destination, self.manifest, instance_id=lease.instance_id, deep=True)
            mode = destination.execute("PRAGMA journal_mode=DELETE").fetchone()
            if mode != ("delete",):
                raise SomaError(
                    "SNAPSHOT_INTEGRITY_FAILURE", "Snapshot journal verification failed."
                )
            destination.close()
            destination = None
            if any(
                stage.with_name(stage.name + suffix).exists()
                for suffix in ("-wal", "-shm", "-journal")
            ):
                raise SomaError(
                    "SNAPSHOT_INTEGRITY_FAILURE", "Snapshot staging state is incomplete."
                )
            protect_owner(stage)
            staged = OwnedArtifact.capture(
                config.instance_root, stage.relative_to(config.instance_root)
            )
            if (staged.device, staged.inode) != (created.st_dev, created.st_ino):
                raise SomaError("SNAPSHOT_OWNERSHIP_CHANGED", "Snapshot stage ownership changed.")
            with stage.open("r+b") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
                os.fsync(stream.fileno())
            size = stage.stat().st_size
            config.path("backups", relative)
            if not staged.matches(config.instance_root):
                raise SomaError("SNAPSHOT_OWNERSHIP_CHANGED", "Snapshot stage ownership changed.")
            if os.name != "nt":
                raise SomaError(
                    "SNAPSHOT_PLATFORM_UNSUPPORTED", "Snapshot publication requires Windows."
                )
            os.rename(stage, target)
            return SnapshotDescriptor(
                target, size, digest, lease.instance_id, as_of, self.manifest.generation
            )
        except BaseException as exc:
            if isinstance(exc, SomaError) or not isinstance(exc, Exception):
                raise
            raise persistence_failure(exc) from None
        finally:
            if destination is not None:
                destination.close()
            if stage.exists():
                artifact = OwnedArtifact.capture(
                    config.instance_root, stage.relative_to(config.instance_root)
                )
                if (artifact.device, artifact.inode) == (created.st_dev, created.st_ino):
                    remove_owned(config.instance_root, artifact)
