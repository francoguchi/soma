"""Canonical technical UUIDs, adapted from Beta identifiers.py."""

import uuid
from collections.abc import Callable


def new_uuid4() -> str:
    return str(uuid.uuid4())


def require_uuid4(value: str) -> str:
    from soma.foundation.errors import ValidationError

    try:
        parsed = uuid.UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError("Expected canonical lowercase UUIDv4.") from exc
    if parsed.version != 4 or str(parsed) != value:
        raise ValidationError("Expected canonical lowercase UUIDv4.")
    return value


UuidProvider = Callable[[], str]
