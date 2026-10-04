from soma.foundation.errors import SomaError
from soma.foundation.persistence.connections import persistence_failure
from soma.foundation.time import utc_epoch_seconds


class ReadSnapshot:
    def __init__(self, factory, *, utc_clock=utc_epoch_seconds):
        self.factory = factory
        self.utc_clock = utc_clock
        self._connection = None
        self.as_of_utc_s = None

    @property
    def connection(self):
        if self._connection is None:
            raise RuntimeError("Read snapshot is not active.")
        return self._connection

    def __enter__(self):
        try:
            self._connection = self.factory.open(read_only=True)
            self._connection.execute("BEGIN")
            # Establish the WAL snapshot now, before any owner readers run.
            self._connection.execute("SELECT count(*) FROM sqlite_schema").fetchone()
            self.as_of_utc_s = self.utc_clock()
            return self
        except BaseException as exc:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
            if isinstance(exc, SomaError) or not isinstance(exc, Exception):
                raise
            raise persistence_failure(exc) from None

    def __exit__(self, exc_type, exc, tb):
        pending = exc
        try:
            self.connection.execute("COMMIT" if exc is None else "ROLLBACK")
        except BaseException as cleanup:
            pending = cleanup
        finally:
            self.connection.close()
            self._connection = None
        if isinstance(pending, Exception) and not isinstance(pending, SomaError):
            raise persistence_failure(pending) from None
        if pending is not exc:
            raise pending
        return False
