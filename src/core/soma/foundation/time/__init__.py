import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from soma.foundation.errors import ValidationError

UtcClock = Callable[[], int]
MonotonicClock = Callable[[], int]


def utc_epoch_seconds() -> int:
    return time.time_ns() // 1_000_000_000


def monotonic_ns() -> int:
    return time.monotonic_ns()


def normalize_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValidationError("An explicit timestamp timezone is required.")
    try:
        return value.astimezone(UTC)
    except (ValueError, OverflowError) as exc:
        raise ValidationError("Invalid UTC instant.") from exc


@dataclass(frozen=True, slots=True)
class Deadline:
    expires_ns: int
    clock: MonotonicClock

    @classmethod
    def after_ms(cls, duration_ms: int, clock: MonotonicClock = monotonic_ns) -> "Deadline":
        if type(duration_ms) is not int or duration_ms < 0:
            raise ValidationError("Duration must be nonnegative integer milliseconds.")
        return cls(clock() + duration_ms * 1_000_000, clock)

    def expired(self) -> bool:
        return self.clock() >= self.expires_ns
