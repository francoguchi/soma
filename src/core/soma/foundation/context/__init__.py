from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from soma.foundation.identity import UuidProvider, new_uuid4, require_uuid4

_correlation: ContextVar[str | None] = ContextVar("soma_correlation", default=None)


def current_correlation() -> str:
    value = _correlation.get()
    if value is None:
        raise RuntimeError("An operation correlation context is required.")
    return value


@contextmanager
def correlation_scope(
    inbound: str | None = None, *, uuid_provider: UuidProvider = new_uuid4
) -> Iterator[str]:
    # Nested calls inherit the operation unless an explicit boundary ID is supplied.
    value = require_uuid4(inbound if inbound is not None else _correlation.get() or uuid_provider())
    token = _correlation.set(value)
    try:
        yield value
    finally:
        _correlation.reset(token)
