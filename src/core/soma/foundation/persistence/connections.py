from pathlib import Path

from soma.foundation.errors import SomaError
from soma.foundation.filesystem import safe_path


def persistence_failure(exc: BaseException) -> SomaError:
    code = getattr(exc, "sqlite_errorcode", 0)
    if type(code) is int and code & 0xFF in (5, 6):
        return SomaError("PERSISTENCE_BUSY", "Data storage is temporarily busy.", "retry")
    return SomaError(
        "PERSISTENCE_FAILURE", "The database operation could not be completed.", "restart"
    )


def load_sqlcipher_driver():
    try:
        import sqlcipher3
    except ImportError:
        raise SomaError(
            "SECURITY_NOT_READY", "The protected database provider is unavailable.", "restart"
        ) from None
    return sqlcipher3


class ConnectionFactory:
    def __init__(self, lease, security, *, database_path: Path | None = None, connector=None):
        self.lease = lease
        self.security = security
        self.database_path = (
            database_path if database_path is not None else lease.config.path("data", "soma.db")
        )
        self.connector = connector

    def at(self, path: Path):
        return ConnectionFactory(
            self.lease, self.security, database_path=path, connector=self.connector
        )

    def open(self, *, read_only: bool = False, journal: str = "wal"):
        if journal not in ("wal", "delete"):
            raise SomaError("PERSISTENCE_CONNECTION_UNSAFE", "Unsupported database journal policy.")
        self.lease.require()
        root = self.lease.config.instance_root
        safe_path(root, self.database_path.relative_to(root))
        connection = None
        try:
            connector = (
                self.connector if self.connector is not None else load_sqlcipher_driver().connect
            )
            if read_only:
                if not self.database_path.is_file():
                    raise SomaError(
                        "PERSISTENCE_FAILURE", "The database is unavailable.", "restart"
                    )
                connection = connector(
                    self.database_path.as_uri() + "?mode=ro",
                    uri=True,
                    timeout=5.0,
                    check_same_thread=True,
                    isolation_level=None,
                )
            else:
                connection = connector(
                    str(self.database_path),
                    timeout=5.0,
                    check_same_thread=True,
                    isolation_level=None,
                )
            self.security.key_connection(connection)
            self.security.verify(connection)
            self._apply_settings(connection)
            mode = connection.execute(
                "PRAGMA journal_mode" if read_only else f"PRAGMA journal_mode={journal.upper()}"
            ).fetchone()
            if mode is None or str(mode[0]).lower() != journal:
                raise SomaError(
                    "PERSISTENCE_CONNECTION_UNSAFE",
                    "Database journal policy is incompatible.",
                    "restart",
                )
            if read_only:
                connection.execute("PRAGMA query_only=ON")
                if connection.execute("PRAGMA query_only").fetchone() != (1,):
                    raise SomaError(
                        "PERSISTENCE_CONNECTION_UNSAFE", "Read-only policy is incompatible."
                    )
            return connection
        except BaseException as exc:
            if connection is not None:
                connection.close()
            if isinstance(exc, SomaError) or not isinstance(exc, Exception):
                raise
            raise persistence_failure(exc) from None

    @staticmethod
    def _apply_settings(connection) -> None:
        for name, setting, expected in [
            ("foreign_keys", "ON", 1),
            ("busy_timeout", "5000", 5000),
            ("trusted_schema", "OFF", 0),
            ("temp_store", "MEMORY", 2),
            ("synchronous", "FULL", 2),
            ("secure_delete", "FAST", 2),
            ("read_uncommitted", "OFF", 0),
            ("wal_autocheckpoint", "1000", 1000),
        ]:
            connection.execute(f"PRAGMA {name}={setting}")
            if connection.execute(f"PRAGMA {name}").fetchone() != (expected,):
                raise SomaError(
                    "PERSISTENCE_CONNECTION_UNSAFE",
                    "Required database safety settings are unavailable.",
                    "restart",
                )
        connection.enable_load_extension(False)
