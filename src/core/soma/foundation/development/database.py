from dataclasses import dataclass
from collections.abc import Callable

from soma.foundation.errors import SomaError
from soma.foundation.filesystem import OwnedArtifact, remove_owned
from soma.foundation.persistence.connections import ConnectionFactory
from soma.foundation.persistence.instance import InstanceLease
from soma.foundation.persistence.migrations import MigrationRunner
from soma.foundation.security.live_key import LiveDataKeyProvider
from soma.foundation.security.sqlcipher_provider import SqlCipherSecurity


@dataclass(frozen=True, slots=True)
class SeedContributor:
    seed_id: str
    depends_on: tuple[str, ...]
    load: Callable


def seed(connection, contributors: tuple[SeedContributor, ...] = ()) -> None:
    seen = set()
    for contributor in contributors:
        if (
            not contributor.seed_id
            or contributor.seed_id in seen
            or not set(contributor.depends_on) <= seen
        ):
            raise SomaError("DEV_SEED_INVALID", "Development seed registration is invalid.")
        seen.add(contributor.seed_id)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for contributor in contributors:
            contributor.load(connection)
        connection.execute("COMMIT")
    except BaseException as exc:
        if connection.in_transaction:
            connection.rollback()
        if not isinstance(exc, Exception):
            raise
        raise SomaError(
            "DEV_SEED_FAILED", "Development seed execution failed; reset is incomplete.", "restart"
        ) from None


def factory_for_lease(lease) -> ConnectionFactory:
    live_key = LiveDataKeyProvider(lease)
    live_key.prepare()
    return ConnectionFactory(lease, SqlCipherSecurity(live_key))


def rebuild(config, *, confirmation: str, contributors: tuple[SeedContributor, ...] = ()) -> str:
    if config.mode != "development" or confirmation != "RESET":
        raise SomaError(
            "DEV_RESET_REFUSED", "Explicit development target and RESET confirmation are required."
        )
    # A later runtime stopper must complete its verified shutdown before invoking this boundary.
    if config.path("runtime", "runtime.json").exists():
        raise SomaError(
            "DEV_RESET_RUNTIME_PRESENT",
            "Stop the configured runtime before resetting its database.",
        )
    with InstanceLease(config) as lease:
        factory = factory_for_lease(lease)
        database = factory.database_path
        if database.exists():
            connection = factory.open()
            try:
                if connection.execute(
                    "SELECT data_instance_id FROM instance_metadata WHERE singleton=1"
                ).fetchone() != (lease.instance_id,):
                    raise SomaError(
                        "DEV_RESET_IDENTITY_INVALID", "Reset database identity is incompatible."
                    )
            finally:
                connection.close()
        artifacts = [
            OwnedArtifact.capture(config.instance_root, path.relative_to(config.instance_root))
            for path in [
                database,
                *(
                    database.with_name(database.name + suffix)
                    for suffix in ("-wal", "-shm", "-journal")
                ),
            ]
            if path.exists()
        ]
        for artifact in artifacts:
            if not remove_owned(config.instance_root, artifact):
                raise SomaError(
                    "DEV_RESET_OWNERSHIP_CHANGED",
                    "Reset file ownership changed; reset is incomplete.",
                )
        MigrationRunner(factory).initialize_or_migrate()
        connection = factory.open()
        try:
            seed(connection, contributors)
        finally:
            connection.close()
        return lease.instance_id
