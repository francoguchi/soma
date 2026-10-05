from collections.abc import Iterable

from soma.foundation.errors import ValidationError
from soma.modules.reference.ports.dependencies import ReferenceDependencyValidator


class ReferenceDependencyRegistry:
    """Closed-at-runtime registry of owner-provided dependency validators.

    Scope 01 never inspects another packet's private tables. A composition root registers
    providers, declares its required owner set, and finalizes the registry before
    lifecycle services can be constructed.
    """

    def __init__(self) -> None:
        self._validators: dict[str, ReferenceDependencyValidator] = {}
        self._required_validator_ids: frozenset[str] = frozenset()
        self._finalized = False

    @staticmethod
    def _validated_id(value: object) -> str:
        if (
            type(value) is not str
            or not value
            or len(value.encode("utf-8", errors="replace")) > 128
            or any(ord(c) < 32 or ord(c) > 126 for c in value)
        ):
            raise ValidationError("dependency validator_id is invalid")
        return value

    def register(self, validator: ReferenceDependencyValidator) -> None:
        if self._finalized:
            raise ValidationError("dependency registry is already finalized")
        validator_id = self._validated_id(getattr(validator, "validator_id", None))
        if validator_id in self._validators:
            raise ValidationError("dependency validator already registered")
        if any(
            not callable(getattr(validator, method, None))
            for method in (
                "guard_archive",
                "guard_reactivate",
                "count_archive_blockers",
                "list_archive_blockers",
                "count_reactivation_blockers",
                "list_reactivation_blockers",
            )
        ):
            raise ValidationError("dependency validator contract is incomplete")
        self._validators[validator_id] = validator

    def finalize(self, *, required_validator_ids: Iterable[str]) -> None:
        if self._finalized:
            raise ValidationError("dependency registry is already finalized")
        required = frozenset(self._validated_id(value) for value in required_validator_ids)
        missing = required - self._validators.keys()
        if missing:
            raise ValidationError("required dependency validators are missing")
        self._required_validator_ids = required
        self._finalized = True

    @classmethod
    def isolated_for_tests(cls) -> "ReferenceDependencyRegistry":
        registry = cls()
        registry.finalize(required_validator_ids=())
        return registry

    def require_finalized(self) -> None:
        if not self._finalized:
            raise ValidationError("reference dependency registry is not finalized")
        missing = self._required_validator_ids - self._validators.keys()
        if missing:
            raise ValidationError("required dependency validators are missing")

    def ordered(self) -> tuple[ReferenceDependencyValidator, ...]:
        self.require_finalized()
        return tuple(self._validators[key] for key in sorted(self._validators))
