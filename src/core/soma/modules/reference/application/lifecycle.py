"""Same-UoW lifecycle guards and snapshot-only bounded blocker previews."""

from dataclasses import dataclass

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.query import CursorCodec
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import CommandBoundary
from soma.modules.reference.adapters.persistence import lifecycle as store
from soma.modules.reference.domain.validation import validate_reason_category
from soma.modules.reference.ports.dependencies import (
    ReferenceTarget,
    DependencyGuard,
    DependencyPage,
    DependencyBlocker,
)
from .commands import RESULT, event, result, revision


@dataclass(frozen=True)
class PreviewBlocker:
    validator_id: str
    blocker_id: str
    reason_code: str


@dataclass(frozen=True)
class LifecyclePreview:
    target_type: str
    target_id: str
    operation: str
    revision: int
    exact_blocker_count: int
    blockers: tuple[PreviewBlocker, ...]
    continuation: str | None
    would_be_eligible: bool


def unavailable():
    return SomaError(
        "DEPENDENCY_VALIDATION_FAILED", "Dependency validation is unavailable.", "retry"
    )


class ReferenceLifecycle:
    def __init__(self, factory, audit_writer, dependency_registry, cursor_codec=None):
        dependency_registry.require_finalized()
        self.factory = factory
        self.dependencies = dependency_registry
        self.cursor = cursor_codec or CursorCodec()
        self.boundary = CommandBoundary(factory, [RESULT], audit_writer)

    @staticmethod
    def _preconditions(operation, target_type, target_id, base_revision):
        if operation not in {"archive", "reactivate"}:
            raise ValidationError("Invalid lifecycle operation.")
        store.validate_type(target_type)
        require_uuid4(target_id)
        revision(base_revision)

    @staticmethod
    def _state(connection, target, base_revision, operation):
        state, current = store.load(connection, target)
        if current != base_revision:
            raise SomaError("STALE_REVISION", "Reference revision changed.", "refresh")
        if operation == "archive" and state != "active":
            raise SomaError("REFERENCE_ARCHIVED", "Reference is already archived.", "refresh")
        if operation == "reactivate" and state != "archived":
            raise ValidationError("Reference must be archived before reactivation.")
        return state

    def _guard(self, uow, target, operation):
        for validator in self.dependencies.ordered():
            try:
                guard = getattr(validator, "guard_" + operation)(uow, target)
                if type(guard) is not DependencyGuard or guard.state not in {
                    "CLEAR",
                    "BLOCKED",
                    "INDETERMINATE",
                }:
                    raise ValueError()
                if guard.reason_code is not None:
                    validate_reason_category(guard.reason_code)
            except Exception:
                raise unavailable() from None
            if guard.state == "BLOCKED":
                code = "ARCHIVE_BLOCKED" if operation == "archive" else "REACTIVATION_BLOCKED"
                raise SomaError(code, "Reference lifecycle change is blocked.", "refresh")
            if guard.state != "CLEAR":
                raise unavailable()

    def _change(
        self,
        operation,
        *,
        command_id,
        target_type,
        target_id,
        base_revision,
        reason_category,
        actor_id=None,
    ):
        data = {}

        def preflight():
            self._preconditions(operation, target_type, target_id, base_revision)
            if actor_id is not None:
                require_uuid4(actor_id)
            data["reason"] = validate_reason_category(reason_category)
            if data["reason"] is None:
                raise ValidationError("Lifecycle reason category is required.")

        def prepare(uow):
            target = ReferenceTarget(target_type, target_id)
            prior = self._state(uow.connection, target, base_revision, operation)
            self._guard(uow, target, operation)
            lifecycle, now = new_uuid4(), utc_epoch_seconds()
            state, kind = (
                ("archived", "archived") if operation == "archive" else ("active", "reactivated")
            )
            audit = event(
                "reference." + kind,
                command_id,
                target_id,
                dict(
                    target_type=target_type,
                    target_id=target_id,
                    prior_state=prior,
                    new_state=state,
                    prior_revision=base_revision,
                    new_revision=base_revision + 1,
                    lifecycle_event_id=lifecycle,
                    reason_category=data["reason"],
                ),
                actor_id,
                target_type=target_type,
                results=((target_type, target_id), ("reference_lifecycle_event", lifecycle)),
            )

            def apply(inner):
                store.transition(
                    inner.connection,
                    target,
                    state,
                    now,
                    lifecycle,
                    kind,
                    command_id,
                    data["reason"],
                )
                return result(target_id, base_revision + 1), [audit]

            return apply

        return self.boundary.execute(
            command_id,
            "reference." + operation,
            dict(
                target_type=target_type,
                target_id=target_id,
                base_revision=base_revision,
                reason_category=reason_category,
                actor_id=actor_id,
            ),
            (RESULT.schema, RESULT.version),
            None,
            preflight=preflight,
            prepare=prepare,
        )

    def archive_reference(self, **request):
        return self._change("archive", **request)

    def reactivate_reference(self, **request):
        return self._change("reactivate", **request)

    def preview(self, *, operation, target_type, target_id, base_revision, after=None, limit=50):
        self._preconditions(operation, target_type, target_id, base_revision)
        limit = self.cursor.limit(limit)
        target = ReferenceTarget(target_type, target_id)
        validators = self.dependencies.ordered()
        ids = [v.validator_id for v in validators]
        filters = dict(
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            revision=base_revision,
            validators=ids,
        )
        order = ["validator_id", "owner_cursor"]
        index, inner_cursor, offset, as_of = 0, None, 0, utc_epoch_seconds()
        if after is not None:
            position, as_of = self.cursor.decode(
                after, "ReferenceLifecycleBlockersV1", filters, order
            )
            if type(position) is not dict or set(position) != {"validator", "cursor", "offset"}:
                raise ValidationError("Invalid lifecycle cursor position.")
            if (
                position["validator"] not in ids
                or type(position["offset"]) is not int
                or position["offset"] < 0
            ):
                raise ValidationError("Invalid lifecycle cursor position.")
            inner_cursor = position["cursor"]
            if inner_cursor is not None and (
                type(inner_cursor) is not str or len(inner_cursor.encode("utf-8")) > 2048
            ):
                raise ValidationError("Invalid lifecycle owner cursor.")
            index, offset = ids.index(position["validator"]), position["offset"]
        with ReadSnapshot(self.factory) as snapshot:
            self._state(snapshot.connection, target, base_revision, operation)
            counts = []
            suffix = "archive" if operation == "archive" else "reactivation"
            for validator in validators:
                try:
                    count = getattr(validator, "count_" + suffix + "_blockers")(snapshot, target)
                    if type(count) is not int or count < 0:
                        raise ValueError()
                    counts.append(count)
                except Exception:
                    raise unavailable() from None
            items, continuation = [], None
            while index < len(validators) and len(items) < limit:
                count = counts[index]
                if offset > count or (offset == count and inner_cursor is not None):
                    raise ValidationError("Lifecycle blocker cursor is stale.")
                if count == 0:
                    index += 1
                    offset, inner_cursor = 0, None
                    continue
                remaining = limit - len(items)
                try:
                    page = getattr(validators[index], "list_" + suffix + "_blockers")(
                        snapshot, target, inner_cursor, remaining
                    )
                    if type(page) is not DependencyPage or type(page.blockers) is not tuple:
                        raise ValueError()
                    expected = min(remaining, count - offset)
                    if len(page.blockers) != expected or not page.blockers:
                        raise ValueError()
                    more = offset + len(page.blockers) < count
                    if more != (page.continuation is not None):
                        raise ValueError()
                    if more and (
                        type(page.continuation) is not str
                        or not page.continuation
                        or len(page.continuation.encode("utf-8")) > 2048
                        or page.continuation == inner_cursor
                    ):
                        raise ValueError()
                    seen = set()
                    for blocker in page.blockers:
                        if type(blocker) is not DependencyBlocker:
                            raise ValueError()
                        require_uuid4(blocker.blocker_id)
                        if (
                            validate_reason_category(blocker.reason_code) is None
                            or blocker.blocker_id in seen
                        ):
                            raise ValueError()
                        seen.add(blocker.blocker_id)
                except Exception:
                    raise unavailable() from None
                items.extend(
                    PreviewBlocker(ids[index], b.blocker_id, b.reason_code) for b in page.blockers
                )
                if more:
                    offset += len(page.blockers)
                    inner_cursor = page.continuation
                else:
                    index += 1
                    offset, inner_cursor = 0, None
                    while index < len(validators) and counts[index] == 0:
                        index += 1
                if len(items) == limit and index < len(validators):
                    continuation = self.cursor.encode(
                        "ReferenceLifecycleBlockersV1",
                        filters,
                        order,
                        dict(validator=ids[index], cursor=inner_cursor, offset=offset),
                        as_of,
                    )
                    break
        return LifecyclePreview(
            target_type,
            target_id,
            operation,
            base_revision,
            sum(counts),
            tuple(items),
            continuation,
            sum(counts) == 0,
        )
