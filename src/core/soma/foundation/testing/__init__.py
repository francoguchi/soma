"""Explicit deterministic providers; never selected by runtime configuration."""

from dataclasses import dataclass

from soma.foundation.identity import require_uuid4


@dataclass
class ManualClocks:
    utc_s: int = 0
    elapsed_ns: int = 0

    def utc(self) -> int:
        return self.utc_s

    def monotonic(self) -> int:
        return self.elapsed_ns

    def advance_ms(self, amount: int) -> None:
        if type(amount) is not int or amount < 0:
            raise ValueError("Monotonic time cannot move backwards.")
        self.elapsed_ns += amount * 1_000_000


class SequenceUuids:
    def __init__(self, values: list[str]) -> None:
        self._values = iter(tuple(require_uuid4(value) for value in values))

    def __call__(self) -> str:
        return next(self._values)
