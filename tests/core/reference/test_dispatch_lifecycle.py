"""Current-contract rewrites of pinned Dispatch/lifecycle/dependency donor vectors."""

import pytest

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4
from soma.foundation.persistence.schema_verify import verify_schema, verify_fk_indexes
from soma.foundation.transactions import UnitOfWork, _active
from soma.modules.reference.application import dispatch as dispatch_commands
from soma.modules.reference.adapters.persistence import lifecycle as lifecycle_store
from soma.modules.reference.composition import compose
from soma.modules.reference.domain.dependencies import ReferenceDependencyRegistry
from soma.modules.reference.domain.dispatch import (
    validate_dispatch_name,
    validate_standalone_address,
)
from soma.modules.reference.ports.dependencies import (
    DependencyGuard,
    DependencyBlocker,
    DependencyPage,
)
from soma.modules.reference.ports.dispatch import DispatchCommandContext
from .test_customer import create as customer, read
from .test_contact import create as contact


def dispatch(ref, **kwargs):
    return ref.dispatch.create_standalone(
        command_id=new_uuid4(), name="Private Dispatch", address_text="Private address", **kwargs
    )["target_id"]


def request(identity, **kwargs):
    return (
        dict(
            command_id=new_uuid4(),
            target_type="contact",
            target_id=identity,
            base_revision=1,
            reason_category="operator_archive",
        )
        | kwargs
    )


def tables(factory):
    return [
        read(factory, "SELECT * FROM " + table)
        for table in (
            "command_receipts",
            "command_receipt_results",
            "contacts",
            "customer_organizations",
            "dispatch_locations",
            "reference_lifecycle_events",
            "audit_events",
            "audit_event_results",
        )
    ]


class Validator:
    validator_id = "synthetic"

    def __init__(self, state="CLEAR", count=0):
        self.state, self.count, self.calls = state, count, []

    def guard_archive(self, uow, target):
        assert _active.get()
        assert uow.connection.execute("SELECT 1").fetchone() == (1,)
        self.calls.append(("guard", uow, target))
        return DependencyGuard(self.state)

    guard_reactivate = guard_archive

    def count_archive_blockers(self, snapshot, target):
        assert not _active.get()
        self.calls.append(("count", snapshot, target))
        return self.count

    count_reactivation_blockers = count_archive_blockers

    def list_archive_blockers(self, snapshot, target, cursor, limit):
        assert not _active.get()
        self.calls.append(("list", snapshot, limit))
        start = int(cursor or 0)
        end = min(start + limit, self.count)
        return DependencyPage(
            tuple(
                DependencyBlocker(f"{i:08x}-0000-4000-8000-000000000000", "active_dependency")
                for i in range(start, end)
            ),
            str(end) if end < self.count else None,
        )

    list_reactivation_blockers = list_archive_blockers


def with_validator(factory, *validators):
    return compose(
        factory,
        dependency_validators=validators,
        required_validator_ids=tuple(v.validator_id for v in validators),
    )


def test_dispatch_identity_edit_no_change_replay_privacy(reference):
    ref, factory, _ = reference
    req = dict(command_id=new_uuid4(), name="Private Dispatch", address_text="Private\r\nAddress")
    original = ref.dispatch.create_standalone(**req)
    assert ref.dispatch.create_standalone(**req) == original
    identity = original["target_id"]
    assert dispatch(ref) != identity
    assert read(
        factory,
        "SELECT standalone_address_text FROM dispatch_locations WHERE dispatch_location_id=?",
        (identity,),
    ) == [("Private\nAddress",)]
    update = dict(
        command_id=new_uuid4(),
        dispatch_location_id=identity,
        base_revision=1,
        name="Private Dispatch",
        address_text="Private\rAddress",
    )
    before = tables(factory)
    unchanged = ref.dispatch.update_descriptive_data(**update)
    assert unchanged["outcome"] == "NO_CHANGE"
    assert tables(factory)[2:] == before[2:]
    applied = ref.dispatch.update_descriptive_data(
        **(update | dict(command_id=new_uuid4(), name="Renamed", address_text="New"))
    )
    assert applied["target_id"] == identity and applied["revision"] == 2
    assert ref.dispatch.update_descriptive_data(**update) == unchanged
    assert ref.dispatch.create_standalone(**req) == original
    with pytest.raises(SomaError) as exc:
        ref.dispatch.update_descriptive_data(**(update | dict(command_id=new_uuid4())))
    assert exc.value.code == "STALE_REVISION"
    with pytest.raises(SomaError):
        ref.dispatch.create_standalone(**(req | dict(name="Different")))
    payload = str(read(factory, "SELECT payload_json FROM audit_events"))
    assert all(
        text not in payload
        for text in ("Private Dispatch", "Private address", "Renamed", "Private\nAddress")
    )


def test_dispatch_bounds_and_normalization():
    assert validate_standalone_address("x\r\ny\rz") == "x\ny\nz"
    assert validate_standalone_address("x" * 8192) == "x" * 8192
    assert validate_standalone_address("\n".join(["x"] * 32)).count("\n") == 31
    assert validate_dispatch_name("x" * 1024)[0] == "x" * 1024
    for value in (
        "",
        " ",
        "x\x00",
        "x" * 8193,
        "\u00e9" * 4097,
        "\n".join(["x"] * 33),
        "\ud800",
        None,
    ):
        with pytest.raises(SomaError):
            validate_standalone_address(value)
    for value in ("x" * 1025, "x\n", "x\r", "x\x00", "\ud800"):
        with pytest.raises(SomaError):
            validate_dispatch_name(value)


def participant(ref, uow, command):
    return ref.dispatch.create_dedicated_for_site(
        uow,
        parent_command_id=command,
        name="Site Dispatch",
        precomputed_name_match_key=validate_dispatch_name("Site Dispatch")[1],
        command_context=DispatchCommandContext(),
    )


def receipt(uow, command):
    uow.connection.execute(
        "INSERT INTO command_receipts VALUES (?, 'synthetic.site', ?, NULL, 0)", (command, "0" * 64)
    )


def test_site_participant_outer_uow_receipt_audit_and_rollback(reference):
    ref, factory, _ = reference
    before = tables(factory)
    with pytest.raises(RuntimeError):
        with UnitOfWork(factory) as uow:
            command = new_uuid4()
            receipt(uow, command)
            identity = participant(ref, uow, command)
            assert uow.connection.execute(
                "SELECT address_mode,standalone_address_text FROM dispatch_locations WHERE dispatch_location_id=?",
                (identity,),
            ).fetchone() == ("site_derived", None)
            raise RuntimeError("Site relation failure")
    assert tables(factory) == before
    with UnitOfWork(factory) as uow:
        command = new_uuid4()
        receipt(uow, command)
        identity = participant(ref, uow, command)
    assert len(read(factory, "SELECT * FROM command_receipts")) == 1
    assert read(factory, "SELECT command_id FROM audit_events") == [(command,)]
    with pytest.raises(ValidationError):
        ref.dispatch.update_descriptive_data(
            command_id=new_uuid4(),
            dispatch_location_id=identity,
            base_revision=1,
            name="Site Dispatch",
            address_text="Forbidden",
        )
    assert (
        ref.dispatch.update_descriptive_data(
            command_id=new_uuid4(),
            dispatch_location_id=identity,
            base_revision=1,
            name="Renamed Site",
        )["revision"]
        == 2
    )
    with pytest.raises(SomaError):
        with UnitOfWork(factory) as uow:
            participant(ref, uow, new_uuid4())
    with pytest.raises(ValidationError):
        with UnitOfWork(factory) as uow:
            ref.dispatch.create_dedicated_for_site(
                uow,
                parent_command_id=command,
                name="Site Dispatch",
                precomputed_name_match_key="wrong",
                command_context=DispatchCommandContext(),
            )


@pytest.mark.parametrize(
    "kind,create",
    [
        ("contact", contact),
        ("customer_organization", lambda ref: customer(ref.customers)),
        ("dispatch_location", dispatch),
    ],
)
def test_lifecycle_history_revision_replay_and_archived_edits(reference, monkeypatch, kind, create):
    ref, factory, _ = reference
    identity = create(ref)
    req = request(identity, target_type=kind)
    archived = ref.lifecycle.archive_reference(**req)
    assert archived["revision"] == 2
    with pytest.raises(SomaError) as exc:
        ref.lifecycle.archive_reference(**(req | dict(command_id=new_uuid4(), base_revision=2)))
    assert exc.value.code == "REFERENCE_ARCHIVED"
    with pytest.raises(SomaError) as exc:
        ref.lifecycle.reactivate_reference(**(req | dict(command_id=new_uuid4())))
    assert exc.value.code == "STALE_REVISION"
    assert (
        ref.lifecycle.reactivate_reference(**(req | dict(command_id=new_uuid4(), base_revision=2)))[
            "revision"
        ]
        == 3
    )
    assert (
        len(
            read(factory, "SELECT * FROM reference_lifecycle_events WHERE target_id=?", (identity,))
        )
        == 3
    )
    monkeypatch.setattr(
        lifecycle_store,
        "load",
        lambda *args: (_ for _ in ()).throw(AssertionError("owner replay read")),
    )
    assert ref.lifecycle.archive_reference(**req) == archived


@pytest.mark.parametrize(
    "state,code",
    [
        ("BLOCKED", "ARCHIVE_BLOCKED"),
        ("INDETERMINATE", "DEPENDENCY_VALIDATION_FAILED"),
        ("bad", "DEPENDENCY_VALIDATION_FAILED"),
    ],
)
def test_fail_closed_without_receipt_or_mutation(reference, state, code):
    ref, factory, _ = reference
    identity = contact(ref)
    validator = Validator(state)
    ref = with_validator(factory, validator)
    before = tables(factory)
    with pytest.raises(SomaError) as exc:
        ref.lifecycle.archive_reference(**request(identity))
    assert exc.value.code == code and tables(factory) == before
    assert len(validator.calls) == 1


def test_provider_exceptions_are_private_and_reactivation_blocks(reference):
    ref, factory, _ = reference
    identity = contact(ref)
    ref.lifecycle.archive_reference(**request(identity))
    validator = Validator("BLOCKED")
    ref = with_validator(factory, validator)
    with pytest.raises(SomaError) as exc:
        ref.lifecycle.reactivate_reference(**request(identity, base_revision=2))
    assert exc.value.code == "REACTIVATION_BLOCKED"

    def failure(*args):
        raise SomaError("PRIVATE_OWNER", "Secret provider text")

    validator.guard_reactivate = failure
    with pytest.raises(SomaError) as exc:
        ref.lifecycle.reactivate_reference(**request(identity, base_revision=2))
    assert exc.value.code == "DEPENDENCY_VALIDATION_FAILED" and "Secret" not in str(exc.value)


def test_registry_closed_required_complete_deterministic(reference):
    _, factory, _ = reference
    registry = ReferenceDependencyRegistry()
    with pytest.raises(ValidationError):
        registry.ordered()
    with pytest.raises(ValidationError):
        compose(factory, required_validator_ids=("missing",))

    class Partial:
        validator_id = "partial"

    with pytest.raises(ValidationError):
        registry.register(Partial())
    one, two = Validator(), Validator()
    one.validator_id, two.validator_id = "z", "a"
    registry.register(one)
    registry.register(two)
    with pytest.raises(ValidationError):
        registry.register(two)
    registry.finalize(required_validator_ids=("a", "z"))
    assert registry.ordered() == (two, one)
    with pytest.raises(ValidationError):
        registry.register(Validator())


def test_preview_bounded_cross_validator_pagination_signed_cursor_and_scale(reference):
    ref, factory, _ = reference
    identity = contact(ref)
    one, two = Validator("BLOCKED", 3), Validator("BLOCKED", 100000)
    one.validator_id, two.validator_id = "a", "z"
    ref = with_validator(factory, two, one)
    args = dict(
        operation="archive", target_type="contact", target_id=identity, base_revision=1, limit=2
    )
    before = tables(factory)
    first = ref.lifecycle.preview(**args)
    assert first.exact_blocker_count == 100003 and not first.would_be_eligible
    assert [b.validator_id for b in first.blockers] == ["a", "a"]
    second = ref.lifecycle.preview(**args, after=first.continuation)
    assert [b.validator_id for b in second.blockers] == ["a", "z"]
    assert tables(factory) == before
    assert all(call[2] <= 2 for v in (one, two) for call in v.calls if call[0] == "list")
    for changes in (
        dict(target_id=new_uuid4()),
        dict(operation="reactivate"),
        dict(base_revision=2),
    ):
        with pytest.raises(ValidationError):
            ref.lifecycle.preview(**(args | changes), after=first.continuation)
    with pytest.raises(ValidationError):
        ref.lifecycle.preview(**args, after=first.continuation[:-3] + "bad")
    one.calls.clear()
    two.calls.clear()
    with pytest.raises(SomaError):
        ref.lifecycle.archive_reference(**request(identity))
    assert [call[0] for call in one.calls] == ["guard"] and not two.calls


@pytest.mark.parametrize(
    "bad",
    [
        None,
        DependencyPage((), None),
        DependencyPage((DependencyBlocker("bad", "reason"),), None),
        DependencyPage((DependencyBlocker(new_uuid4(), "secret narrative"),), None),
    ],
)
def test_malformed_preview_fails_closed(reference, bad):
    ref, factory, _ = reference
    identity = contact(ref)
    validator = Validator(count=1)
    validator.list_archive_blockers = lambda *args: bad
    ref = with_validator(factory, validator)
    with pytest.raises(SomaError) as exc:
        ref.lifecycle.preview(
            operation="archive", target_type="contact", target_id=identity, base_revision=1
        )
    assert exc.value.code == "DEPENDENCY_VALIDATION_FAILED"


def test_preflight_guard_receipt_order_and_atomic_audit_failure(reference, monkeypatch):
    ref, factory, _ = reference
    identity = contact(ref)
    validator = Validator()

    def guard(uow, target):
        assert _active.get()
        assert (
            uow.connection.execute(
                "SELECT 1 FROM command_receipts WHERE command_id=?", (req["command_id"],)
            ).fetchone()
            is None
        )
        return DependencyGuard("CLEAR")

    validator.guard_archive = guard
    ref = with_validator(factory, validator)
    req = request(identity)
    before = tables(factory)
    original = lifecycle_store.transition

    def transition(connection, *args):
        assert connection.execute(
            "SELECT 1 FROM command_receipts WHERE command_id=?", (req["command_id"],)
        ).fetchone() == (1,)
        return original(connection, *args)

    monkeypatch.setattr(lifecycle_store, "transition", transition)

    def failure(*args):
        raise SomaError("AUDIT_FAILED", "Injected audit failure.")

    monkeypatch.setattr(ref.lifecycle.boundary.audit, "append", failure)
    with pytest.raises(SomaError):
        ref.lifecycle.archive_reference(**req)
    assert tables(factory) == before
    original_validate = dispatch_commands.validate_dispatch_name

    def validate(value):
        assert not _active.get()
        return original_validate(value)

    monkeypatch.setattr(dispatch_commands, "validate_dispatch_name", validate)
    # restore composed audit writer after failure injection
    ref = compose(factory)
    assert dispatch(ref)


def test_dispatch_schema_protection_and_exact_manifest(reference):
    ref, factory, manifest = reference
    identity = dispatch(ref)
    assert manifest.generation == 9
    connection = factory.open()
    try:
        verify_schema(connection, manifest)
        verify_fk_indexes(connection)
    finally:
        connection.close()
    for sql in (
        "UPDATE dispatch_locations SET dispatch_location_id='changed'",
        "UPDATE dispatch_locations SET address_mode='site_derived',standalone_address_text=NULL",
        "UPDATE dispatch_locations SET created_at_utc=created_at_utc+1,updated_at_utc=updated_at_utc+1",
        "DELETE FROM dispatch_locations",
    ):
        with pytest.raises(SomaError):
            with UnitOfWork(factory) as uow:
                uow.connection.execute(sql)
    assert read(factory, "SELECT dispatch_location_id FROM dispatch_locations") == [(identity,)]


def test_invalid_target_operation_reason_and_stale_preview(reference):
    ref, factory, _ = reference
    identity = contact(ref)
    for changes in (
        dict(target_type="contacts; DROP TABLE contacts"),
        dict(target_id="bad"),
        dict(base_revision=True),
        dict(reason_category="free narrative"),
        dict(reason_category=None),
    ):
        before = tables(factory)
        with pytest.raises(SomaError):
            ref.lifecycle.archive_reference(**request(identity, **changes))
        assert tables(factory) == before
    preview = ref.lifecycle.preview(
        operation="archive", target_type="contact", target_id=identity, base_revision=1
    )
    assert preview.exact_blocker_count == 0 and preview.would_be_eligible and not preview.blockers
    ref.lifecycle.archive_reference(**request(identity))
    with pytest.raises(SomaError) as exc:
        ref.lifecycle.preview(
            operation="archive", target_type="contact", target_id=identity, base_revision=1
        )
    assert exc.value.code == "STALE_REVISION"


@pytest.mark.parametrize("operation", ["dispatch", "archive"])
def test_single_writer_commit_and_receipt_before_owner_writes(reference, monkeypatch, operation):
    ref, factory, _ = reference
    identity = contact(ref)
    trace = []
    original = factory.open

    def opened(*args, **kwargs):
        connection = original(*args, **kwargs)
        connection.set_trace_callback(trace.append)
        return connection

    monkeypatch.setattr(factory, "open", opened)
    if operation == "dispatch":
        dispatch(ref)
        prefix = "INSERT INTO dispatch_locations"
    else:
        ref.lifecycle.archive_reference(**request(identity))
        prefix = "UPDATE contacts"
    start = trace.index("BEGIN IMMEDIATE")
    receipt_index = next(
        i for i, sql in enumerate(trace) if sql.startswith("INSERT INTO command_receipts")
    )
    owner = next(i for i, sql in enumerate(trace) if sql.startswith(prefix))
    audit = next(i for i, sql in enumerate(trace) if sql.startswith("INSERT INTO audit_events"))
    assert trace.count("BEGIN IMMEDIATE") == 1 and start < receipt_index < owner < audit
    assert trace[start:].count("COMMIT") == 1


@pytest.mark.parametrize("operation", ["create", "site", "update"])
def test_dispatch_partial_sql_or_audit_failure_rolls_back(reference, monkeypatch, operation):
    ref, factory, _ = reference
    identity = dispatch(ref)
    before = tables(factory)

    def failure(*args):
        raise SomaError("INJECTED", "Injected failure.")

    if operation == "site":
        monkeypatch.setattr(ref.dispatch.audit, "append", failure)
        with pytest.raises(SomaError):
            with UnitOfWork(factory) as uow:
                command = new_uuid4()
                receipt(uow, command)
                participant(ref, uow, command)
    else:
        monkeypatch.setattr(dispatch_commands.store, "lifecycle_event", failure)
        with pytest.raises(SomaError):
            if operation == "create":
                dispatch(ref)
            else:
                ref.dispatch.update_descriptive_data(
                    command_id=new_uuid4(),
                    dispatch_location_id=identity,
                    base_revision=1,
                    name="New",
                    address_text="New",
                )
    assert tables(factory) == before


def test_indexed_100000_blocker_guard_preview_and_freshness(reference):
    ref, factory, _ = reference
    identity = contact(ref)
    connection = factory.open()
    try:
        connection.execute(
            "CREATE TABLE synthetic_dependencies(target_id TEXT NOT NULL, blocker_id TEXT PRIMARY KEY) STRICT"
        )
        connection.execute(
            "CREATE INDEX synthetic_dependencies_target ON synthetic_dependencies(target_id,blocker_id)"
        )
    finally:
        connection.close()

    class IndexedValidator(Validator):
        def guard_archive(self, uow, target):
            self.calls.append("guard")
            row = uow.connection.execute(
                "SELECT 1 FROM synthetic_dependencies WHERE target_id=? LIMIT 1",
                (target.target_id,),
            ).fetchone()
            return DependencyGuard("BLOCKED" if row else "CLEAR")

        guard_reactivate = guard_archive

        def count_archive_blockers(self, snapshot, target):
            self.calls.append("count")
            return snapshot.connection.execute(
                "SELECT count(*) FROM synthetic_dependencies WHERE target_id=?", (target.target_id,)
            ).fetchone()[0]

        count_reactivation_blockers = count_archive_blockers

        def list_archive_blockers(self, snapshot, target, cursor, limit):
            self.calls.append("list")
            rows = snapshot.connection.execute(
                "SELECT blocker_id FROM synthetic_dependencies WHERE target_id=? AND blocker_id>? ORDER BY blocker_id LIMIT ?",
                (target.target_id, cursor or "", limit + 1),
            ).fetchall()
            return DependencyPage(
                tuple(DependencyBlocker(r[0], "active_dependency") for r in rows[:limit]),
                rows[limit - 1][0] if len(rows) > limit else None,
            )

        list_reactivation_blockers = list_archive_blockers

    validator = IndexedValidator()
    ref = with_validator(factory, validator)
    args = dict(
        operation="archive", target_type="contact", target_id=identity, base_revision=1, limit=7
    )
    assert ref.lifecycle.preview(**args).would_be_eligible
    # Change dependency state after a clear preview; the writer must revalidate.
    connection = factory.open()
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.executemany(
            "INSERT INTO synthetic_dependencies VALUES (?,?)",
            ((identity, f"{i:08x}-0000-4000-8000-000000000000") for i in range(100000)),
        )
        connection.execute("COMMIT")
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT 1 FROM synthetic_dependencies WHERE target_id=? LIMIT 1",
            (identity,),
        ).fetchall()
        assert any("SEARCH" in row[3] and "synthetic_dependencies_target" in row[3] for row in plan)
    finally:
        connection.close()
    first = ref.lifecycle.preview(**args)
    second = ref.lifecycle.preview(**args, after=first.continuation)
    assert first.exact_blocker_count == 100000 and len(first.blockers) == len(second.blockers) == 7
    assert first.blockers[-1].blocker_id < second.blockers[0].blocker_id
    validator.calls.clear()
    before = tables(factory)
    with pytest.raises(SomaError) as exc:
        ref.lifecycle.archive_reference(**request(identity))
    assert exc.value.code == "ARCHIVE_BLOCKED" and validator.calls == ["guard"]
    assert tables(factory) == before
    assert read(factory, "SELECT count(*) FROM synthetic_dependencies") == [(100000,)]


@pytest.mark.parametrize(
    "tamper",
    [
        "DROP INDEX idx_dispatch_active_name_match",
        "DROP TRIGGER reference_dispatch_locations_update_guard",
        "DROP TRIGGER reference_dispatch_locations_delete_forbidden",
    ],
)
def test_dispatch_tamper_fails_readiness(reference, tamper):
    _, factory, manifest = reference
    connection = factory.open()
    try:
        connection.execute(tamper)
        with pytest.raises(SomaError) as exc:
            verify_schema(connection, manifest)
        assert exc.value.code == "PERSISTENCE_SCHEMA_MISMATCH"
    finally:
        connection.close()


def test_multiple_guards_share_uow_and_archive_preserves_relationships(reference):
    ref, factory, _ = reference
    org = customer(ref.customers, code="CODE")
    identity = ref.contacts.create_contact(
        command_id=new_uuid4(),
        name="Contact",
        initial_email="private@example.com",
        initial_customer_org_id=org,
    )["target_id"]
    relations = [
        read(factory, "SELECT * FROM " + table)
        for table in ("contact_channels", "contact_affiliations", "customer_org_identifiers")
    ]
    a, z = Validator(), Validator()
    a.validator_id, z.validator_id = "a", "z"
    ref = with_validator(factory, z, a)
    req = request(identity)
    ref.lifecycle.archive_reference(**req)
    assert a.calls[0][1] is z.calls[0][1]
    assert [
        read(factory, "SELECT * FROM " + table)
        for table in ("contact_channels", "contact_affiliations", "customer_org_identifiers")
    ] == relations
    with pytest.raises(SomaError) as exc:
        ref.contacts.update_descriptive_data(
            command_id=new_uuid4(), contact_id=identity, base_revision=2, name="Changed"
        )
    assert exc.value.code == "REFERENCE_ARCHIVED"
    ref.lifecycle.reactivate_reference(**(req | dict(command_id=new_uuid4(), base_revision=2)))
    assert a.calls[1][1] is z.calls[1][1]
    preview = ref.lifecycle.preview(
        operation="archive", target_type="contact", target_id=identity, base_revision=3
    )
    assert preview.would_be_eligible and a.calls[-1][1] is z.calls[-1][1]
    ref.lifecycle.archive_reference(**request(org, target_type="customer_organization"))
    assert read(factory, "SELECT * FROM customer_org_identifiers") == relations[2]


def test_site_derived_and_standalone_dispatch_archive_edit_guard(reference):
    ref, factory, _ = reference
    standalone = dispatch(ref)
    with UnitOfWork(factory) as uow:
        command = new_uuid4()
        receipt(uow, command)
        derived = participant(ref, uow, command)
    for identity in (standalone, derived):
        ref.lifecycle.archive_reference(**request(identity, target_type="dispatch_location"))
        with pytest.raises(SomaError) as exc:
            ref.dispatch.update_descriptive_data(
                command_id=new_uuid4(),
                dispatch_location_id=identity,
                base_revision=2,
                name="Changed",
                address_text="New",
            )
        assert exc.value.code == "REFERENCE_ARCHIVED"
