from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.transactions import UnitOfWork

ReferenceType = Literal["customer_organization", "contact", "dispatch_location"]
GuardState = Literal["CLEAR", "BLOCKED", "INDETERMINATE"]


@dataclass(frozen=True, slots=True)
class ReferenceTarget:
    target_type: ReferenceType
    target_id: str


@dataclass(frozen=True, slots=True)
class DependencyGuard:
    state: GuardState
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class DependencyBlocker:
    blocker_id: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class DependencyPage:
    blockers: tuple[DependencyBlocker, ...]
    continuation: str | None


class ReferenceDependencyValidator(Protocol):
    validator_id: str

    def guard_archive(self, uow: UnitOfWork, target: ReferenceTarget) -> DependencyGuard: ...

    def guard_reactivate(self, uow: UnitOfWork, target: ReferenceTarget) -> DependencyGuard: ...

    def count_archive_blockers(self, snapshot: ReadSnapshot, target: ReferenceTarget) -> int: ...

    def list_archive_blockers(
        self, snapshot: ReadSnapshot, target: ReferenceTarget, cursor: str | None, limit: int
    ) -> DependencyPage: ...

    def count_reactivation_blockers(
        self, snapshot: ReadSnapshot, target: ReferenceTarget
    ) -> int: ...

    def list_reactivation_blockers(
        self, snapshot: ReadSnapshot, target: ReferenceTarget, cursor: str | None, limit: int
    ) -> DependencyPage: ...
