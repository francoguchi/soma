"""Selected Beta Contact/replay vectors plus current-contract adversarial evidence."""

import pytest

from soma.foundation.errors import SomaError
from soma.foundation.identity import new_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.persistence.schema_verify import verify_schema, verify_fk_indexes
from soma.foundation.transactions import UnitOfWork
from soma.modules.reference.application import contact as commands
from soma.modules.reference.adapters.persistence import contact as store
from soma.modules.reference.domain.channels import validate_email
from .test_customer import create as customer, read


def create(ref, **kwargs):
    return ref.contacts.create_contact(command_id=new_uuid4(), name="Private Contact", **kwargs)[
        "target_id"
    ]


def add(ref, identity, rev, value="first@example.com"):
    return ref.contacts.add_contact_channel(
        command_id=new_uuid4(),
        contact_id=identity,
        contact_base_revision=rev,
        channel_kind="email",
        value_text=value,
    )["target_id"]


def state(factory):
    return [
        read(factory, "SELECT * FROM " + table)
        for table in (
            "contacts",
            "contact_channels",
            "contact_affiliations",
            "reference_lifecycle_events",
            "audit_events",
        )
    ]


def test_optional_identity_equal_email_replay_and_privacy(reference):
    ref, factory, _ = reference
    empty = create(ref)
    assert read(factory, "SELECT * FROM contact_channels") == []
    request = dict(
        command_id=new_uuid4(), name="Private Contact", initial_email=" ops@example.com "
    )
    first = ref.contacts.create_contact(**request)
    assert ref.contacts.create_contact(**request) == first
    second = create(ref, initial_email="OPS@example.com")
    assert len({empty, first["target_id"], second}) == 3
    assert len(read(factory, "SELECT * FROM reference_lifecycle_events")) == 3
    with ReadSnapshot(factory) as snapshot:
        page = ref.communication.match_email_candidates(snapshot, " OPS@example.com ", limit=1)
        assert len(page.candidates) == 1 and page.continuation_after_id
        rest = ref.communication.match_email_candidates(
            snapshot, "ops@example.com", after_contact_id=page.continuation_after_id
        )
        assert {page.candidates[0].contact_id, rest.candidates[0].contact_id} == {
            first["target_id"],
            second,
        }
    payloads = str(read(factory, "SELECT payload_json FROM audit_events"))
    assert "Private Contact" not in payloads and "ops@example.com" not in payloads


def test_channel_revision_no_change_archive_and_original_replay(reference, monkeypatch):
    ref, factory, _ = reference
    identity = create(ref)
    channel = add(ref, identity, 1)
    request = dict(
        command_id=new_uuid4(),
        contact_id=identity,
        contact_base_revision=2,
        contact_channel_id=channel,
        channel_base_revision=1,
        value_text=" first@example.com ",
    )
    before = state(factory)
    original = ref.contacts.update_contact_channel(**request)
    assert original["outcome"] == "NO_CHANGE" and state(factory) == before
    with pytest.raises(SomaError, match="revision"):
        ref.contacts.update_contact_channel(
            **(request | dict(command_id=new_uuid4(), contact_base_revision=1))
        )
    applied = ref.contacts.update_contact_channel(
        **(request | dict(command_id=new_uuid4(), value_text="second@example.com"))
    )
    assert applied["revision"] == 2
    ref.contacts.archive_contact_channel(
        command_id=new_uuid4(),
        contact_id=identity,
        contact_base_revision=3,
        contact_channel_id=channel,
        channel_base_revision=2,
        reason_category="retired",
    )
    assert read(factory, "SELECT value_text,lifecycle_state,revision FROM contact_channels") == [
        ("second@example.com", "archived", 3)
    ]
    assert read(factory, "SELECT revision FROM contacts") == [(4,)]
    monkeypatch.setattr(store, "active_contact", lambda *args: pytest.fail("owner read on replay"))
    assert ref.contacts.update_contact_channel(**request) == original
    with ReadSnapshot(factory) as snapshot:
        assert (
            ref.communication.validate_channel_for_use(
                snapshot, identity, channel, "msg_recipient"
            ).state
            == "ARCHIVED"
        )
        assert (
            ref.communication.match_email_candidates(snapshot, "second@example.com").candidates
            == ()
        )


def test_affiliation_move_unbind_no_change_and_history(reference):
    ref, factory, manifest = reference
    a, b = customer(ref.customers, "A"), customer(ref.customers, "B")
    identity = create(ref, initial_customer_org_id=a)

    def change(rev, target, command=None):
        return ref.contacts.change_contact_affiliation(
            command_id=command or new_uuid4(),
            contact_id=identity,
            base_revision=rev,
            new_customer_org_id=target,
            reason_category="role_changed",
        )

    before = state(factory)
    assert change(1, a)["outcome"] == "NO_CHANGE" and state(factory) == before
    assert change(1, b)["revision"] == 2
    assert change(2, None)["revision"] == 3
    rows = read(
        factory, "SELECT customer_org_id,is_current,closed_command_id FROM contact_affiliations"
    )
    assert {row[0] for row in rows} == {a, b} and all(row[1] == 0 and row[2] for row in rows)
    before = state(factory)
    assert change(3, None)["outcome"] == "NO_CHANGE" and state(factory) == before
    connection = factory.open()
    try:
        verify_schema(connection, manifest, deep=True)
        verify_fk_indexes(connection)
        for sql in (
            "UPDATE contact_affiliations SET customer_org_id=customer_org_id",
            "DELETE FROM contact_affiliations",
            "DELETE FROM contacts",
        ):
            with pytest.raises(Exception):
                connection.execute(sql)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "local",
        "a@",
        "@example.com",
        "a@example.com,b@example.com",
        "Name <a@example.com>",
        "\ra@example.com",
        "a@example.com\n",
        "\ta@example.com",
        "a\x80@example.com",
        "a\x00@example.com",
        "\ud800",
    ],
)
def test_email_complete_syntax_and_controls(value):
    with pytest.raises(SomaError):
        validate_email(value)


def test_bound_before_trim_and_no_network(reference, monkeypatch):
    import socket

    monkeypatch.setattr(socket, "getaddrinfo", lambda *a: pytest.fail("DNS access"))
    assert validate_email(" ops@example.com ")[0] == "ops@example.com"
    with pytest.raises(SomaError) as exc:
        validate_email(" " * 2048 + "a@example.com")
    assert exc.value.code == "FIELD_BOUND_EXCEEDED"
    ref, factory, _ = reference
    for args in (dict(initial_email="bad\r\n"), dict(name="x" * 1025)):
        with pytest.raises(SomaError):
            ref.contacts.create_contact(**(dict(command_id=new_uuid4(), name="Valid") | args))
    assert read(factory, "SELECT * FROM command_receipts") == []


def test_applied_replay_original_revision_and_changed_hash(reference, monkeypatch):
    ref, factory, _ = reference
    identity = create(ref)
    channel = add(ref, identity, 1)
    request = dict(
        command_id=new_uuid4(),
        contact_id=identity,
        contact_base_revision=2,
        contact_channel_id=channel,
        channel_base_revision=1,
        value_text="second@example.com",
    )
    original = ref.contacts.update_contact_channel(**request)
    ref.contacts.archive_contact_channel(
        command_id=new_uuid4(),
        contact_id=identity,
        contact_base_revision=3,
        contact_channel_id=channel,
        channel_base_revision=2,
        reason_category="retired",
    )
    monkeypatch.setattr(commands, "validate_email", lambda *a: pytest.fail("preflight on replay"))
    monkeypatch.setattr(store, "active_contact", lambda *a: pytest.fail("owner read on replay"))
    assert ref.contacts.update_contact_channel(**request) == original
    assert original["revision"] == 2
    with pytest.raises(SomaError) as exc:
        ref.contacts.update_contact_channel(**(request | dict(value_text="changed@example.com")))
    assert exc.value.code == "COMMAND_ID_CONFLICT"


def test_descriptive_no_change_then_lifecycle_and_guards(reference):
    ref, factory, _ = reference
    identity = create(ref)
    before = state(factory)
    request = dict(
        command_id=new_uuid4(), contact_id=identity, base_revision=1, name="Private Contact"
    )
    assert ref.contacts.update_descriptive_data(**request)["outcome"] == "NO_CHANGE"
    assert state(factory) == before
    assert (
        ref.contacts.update_descriptive_data(
            **(request | dict(command_id=new_uuid4(), name="Revised"))
        )["revision"]
        == 2
    )
    assert read(
        factory, "SELECT event_type FROM reference_lifecycle_events ORDER BY event_type"
    ) == [("created",), ("descriptive_corrected",)]
    assert ref.contacts.update_descriptive_data(**request)["outcome"] == "NO_CHANGE"


def test_inactive_customer_contact_and_stale_affiliation_fail_without_receipt(reference):
    ref, factory, _ = reference
    org = customer(ref.customers)
    identity = create(ref, initial_customer_org_id=org)
    connection = factory.open()
    try:
        connection.execute(
            "UPDATE customer_organizations SET lifecycle_state='archived' WHERE customer_org_id=?",
            (org,),
        )
    finally:
        connection.close()
    count = read(factory, "SELECT count(*) FROM command_receipts")
    with pytest.raises(SomaError) as exc:
        ref.contacts.change_contact_affiliation(
            command_id=new_uuid4(),
            contact_id=identity,
            base_revision=1,
            new_customer_org_id=org,
            reason_category="unchanged",
        )
    assert exc.value.code == "CUSTOMER_ORG_INACTIVE"
    with pytest.raises(SomaError) as exc:
        ref.contacts.change_contact_affiliation(
            command_id=new_uuid4(),
            contact_id=identity,
            base_revision=2,
            new_customer_org_id=None,
            reason_category="unbind",
        )
    assert exc.value.code == "STALE_REVISION"
    connection = factory.open()
    try:
        connection.execute(
            "UPDATE contacts SET lifecycle_state='archived' WHERE contact_id=?", (identity,)
        )
    finally:
        connection.close()
    with pytest.raises(SomaError) as exc:
        add(ref, identity, 1)
    assert exc.value.code == "REFERENCE_ARCHIVED"
    assert read(factory, "SELECT count(*) FROM command_receipts") == count
    with ReadSnapshot(factory) as snapshot:
        assert ref.communication.validate_contact(snapshot, identity, 1) == "ARCHIVED"
        assert ref.communication.validate_contact(snapshot, new_uuid4(), 1) == "MISSING"
        assert (
            ref.communication.validate_channel_for_use(
                snapshot, identity, "AUTO", "msg_recipient"
            ).state
            == "ARCHIVED"
        )


def test_schema_constraints_immutable_identity_and_closure(reference):
    ref, factory, manifest = reference
    org = customer(ref.customers)
    identity = create(ref, initial_customer_org_id=org)
    channel = add(ref, identity, 1)
    affiliation = read(factory, "SELECT contact_affiliation_id FROM contact_affiliations")[0][0]
    command = read(factory, "SELECT opened_command_id FROM contact_affiliations")[0][0]
    connection = factory.open()
    try:
        assert all(
            row[5] == 1
            for row in connection.execute("PRAGMA table_list")
            if row[1] in {"contacts", "contact_channels", "contact_affiliations"}
        )
        failures = [
            ("UPDATE contacts SET contact_id=?", (new_uuid4(),)),
            ("UPDATE contacts SET created_at_utc=created_at_utc+1", ()),
            ("UPDATE contact_channels SET channel_kind='phone',revision=revision+1", ()),
            ("UPDATE contact_channels SET contact_id=?,revision=revision+1", (new_uuid4(),)),
            (
                "UPDATE contact_channels SET contact_channel_id=?,revision=revision+1",
                (new_uuid4(),),
            ),
            ("UPDATE contact_channels SET created_at_utc=created_at_utc+1,revision=revision+1", ()),
            (
                "UPDATE contact_channels SET lifecycle_state='archived',value_text='replacement',revision=revision+1",
                (),
            ),
            ("UPDATE contact_affiliations SET opened_command_id=?", (new_uuid4(),)),
            ("UPDATE contact_affiliations SET customer_org_id=?", (new_uuid4(),)),
            (
                "INSERT INTO contact_affiliations VALUES (?,?,?,1,0,NULL,?,NULL)",
                (new_uuid4(), identity, org, command),
            ),
            ("DELETE FROM contact_channels", ()),
        ]
        for sql, args in failures:
            with pytest.raises(Exception):
                connection.execute(sql, args)
        verify_schema(connection, manifest, deep=True)
        connection.execute("DROP TRIGGER contact_affiliation_history_update_guard")
        with pytest.raises(SomaError) as exc:
            verify_schema(connection, manifest)
        assert exc.value.code == "PERSISTENCE_SCHEMA_MISMATCH"
    finally:
        connection.close()
    assert read(factory, "SELECT contact_channel_id FROM contact_channels") == [(channel,)]
    assert read(factory, "SELECT contact_affiliation_id FROM contact_affiliations") == [
        (affiliation,)
    ]


def test_preflight_outside_writer_receipt_precedes_writes_one_commit(reference, monkeypatch):
    ref, factory, _ = reference
    trace = []
    original_open = factory.open

    def opened(*args, **kwargs):
        connection = original_open(*args, **kwargs)
        connection.set_trace_callback(trace.append)
        return connection

    monkeypatch.setattr(factory, "open", opened)
    original_validation = commands.validate_email

    def validated(value):
        assert not any(statement == "BEGIN IMMEDIATE" for statement in trace)
        return original_validation(value)

    monkeypatch.setattr(commands, "validate_email", validated)
    create(ref, initial_email="private@example.com")
    starts = [i for i, sql in enumerate(trace) if sql == "BEGIN IMMEDIATE"]
    receipt = next(
        i for i, sql in enumerate(trace) if sql.startswith("INSERT INTO command_receipts")
    )
    contact = next(i for i, sql in enumerate(trace) if sql.startswith("INSERT INTO contacts"))
    audit = next(i for i, sql in enumerate(trace) if sql.startswith("INSERT INTO audit_events"))
    assert len(starts) == 1 and starts[0] < receipt < contact < audit
    assert trace[starts[0] :].count("COMMIT") == 1


@pytest.mark.parametrize("operation", ["channel", "affiliation"])
def test_partial_update_constraint_failure_preserves_prior_state(reference, monkeypatch, operation):
    ref, factory, _ = reference
    org = customer(ref.customers)
    other = customer(ref.customers, "Other")
    identity = create(ref, initial_customer_org_id=org)
    channel = add(ref, identity, 1)
    before = state(factory)
    count = read(factory, "SELECT count(*) FROM command_receipts")
    if operation == "affiliation":

        def invalid(connection, *args):
            connection.execute(
                "INSERT INTO contact_affiliations VALUES (?,?,?,1,0,NULL,?,NULL)",
                (new_uuid4(), identity, new_uuid4(), new_uuid4()),
            )

        monkeypatch.setattr(store, "insert_affiliation", invalid)

        def invoke():
            return ref.contacts.change_contact_affiliation(
                command_id=new_uuid4(),
                contact_id=identity,
                base_revision=2,
                new_customer_org_id=other,
                reason_category="move",
            )
    else:

        def invalid(connection, *args):
            connection.execute("UPDATE contacts SET revision=0 WHERE contact_id=?", (identity,))

        monkeypatch.setattr(store, "bump_revision", invalid)

        def invoke():
            return ref.contacts.update_contact_channel(
                command_id=new_uuid4(),
                contact_id=identity,
                contact_base_revision=2,
                contact_channel_id=channel,
                channel_base_revision=1,
                value_text="next@example.com",
            )

    with pytest.raises(SomaError) as exc:
        invoke()
    assert exc.value.code == "PERSISTENCE_FAILURE"
    assert (
        state(factory) == before and read(factory, "SELECT count(*) FROM command_receipts") == count
    )


def test_bounded_auto_paging_current_validation_and_profile_guard(reference):
    ref, factory, _ = reference
    identity = create(ref)
    with UnitOfWork(factory) as uow:
        for i in range(205):
            store.insert_channel(
                uow.connection, new_uuid4(), identity, "ops@example.com", "ops@example.com", 0
            )
    with ReadSnapshot(factory) as snapshot:
        first = ref.communication.validate_channel_for_use(
            snapshot, identity, "AUTO", "msg_recipient", limit=200
        )
        second = ref.communication.validate_channel_for_use(
            snapshot,
            identity,
            "AUTO",
            "msg_recipient",
            limit=200,
            after_channel_id=first.continuation_after_id,
        )
        assert first.usable_count == 205 and len(first.candidate_channel_ids) == 200
        assert len(second.candidate_channel_ids) == 5 and second.continuation_after_id is None
        assert not set(first.candidate_channel_ids) & set(second.candidate_channel_ids)
        with pytest.raises(SomaError):
            ref.communication.match_email_candidates(snapshot, "ops@example.com", limit=201)
        with pytest.raises(SomaError):
            ref.communication.validate_contact(snapshot, identity, 2)
        assert (
            ref.communication.validate_channel_for_use(
                snapshot, identity, new_uuid4(), "msg_recipient"
            ).state
            == "MISSING"
        )
        plan = snapshot.connection.execute(
            "EXPLAIN QUERY PLAN SELECT contact_id FROM contact_channels WHERE channel_kind='email' AND lifecycle_state='active' AND match_key=?",
            ("ops@example.com",),
        ).fetchall()
        assert any("idx_contact_channels_match" in row[3] for row in plan)
    connection = factory.open()
    try:
        connection.execute("UPDATE reference_metadata SET matching_profile_id='unsupported'")
    finally:
        connection.close()
    with ReadSnapshot(factory) as snapshot:
        with pytest.raises(SomaError) as exc:
            ref.communication.match_email_candidates(snapshot, "ops@example.com")
        assert exc.value.code == "MATCH_PROFILE_UNSUPPORTED"


def test_auto_channels_and_at_use_corruption_ownership(reference):
    ref, factory, _ = reference
    identity = create(ref)
    with ReadSnapshot(factory) as snapshot:
        assert (
            ref.communication.validate_channel_for_use(
                snapshot, identity, "AUTO", "msg_recipient"
            ).state
            == "MISSING"
        )
    channel = add(ref, identity, 1)
    with ReadSnapshot(factory) as snapshot:
        use = ref.communication.validate_channel_for_use(
            snapshot, identity, "AUTO", "msg_recipient"
        )
        assert (use.state, use.contact_channel_id) == ("USABLE", channel)
    second = add(ref, identity, 2)
    other = create(ref)
    with ReadSnapshot(factory) as snapshot:
        use = ref.communication.validate_channel_for_use(
            snapshot, identity, "AUTO", "msg_recipient", limit=1
        )
        assert (
            use.state == "MULTIPLE_USABLE"
            and use.contact_channel_id is None
            and use.value_text is None
        )
        assert (
            use.usable_count == 2
            and len(use.candidate_channel_ids) == 1
            and use.continuation_after_id
        )
        with pytest.raises(SomaError) as exc:
            ref.communication.validate_channel_for_use(snapshot, other, channel, "msg_recipient")
        assert exc.value.code == "CHANNEL_NOT_OWNED"
    connection = factory.open()
    try:
        connection.execute(
            "UPDATE contact_channels SET value_text='invalid',revision=revision+1 WHERE contact_channel_id=?",
            (second,),
        )
    finally:
        connection.close()
    with ReadSnapshot(factory) as snapshot:
        assert (
            ref.communication.validate_channel_for_use(
                snapshot, identity, second, "msg_recipient"
            ).state
            == "INVALID"
        )
        assert (
            ref.communication.validate_channel_for_use(
                snapshot, identity, "AUTO", "msg_recipient"
            ).contact_channel_id
            == channel
        )


@pytest.mark.parametrize("failure", ["repository", "audit"])
def test_command_failure_rolls_back_receipt_and_partial_owner_history(
    reference, monkeypatch, failure
):
    ref, factory, _ = reference

    def fail(*args):
        raise RuntimeError("injected failure")

    if failure == "repository":
        monkeypatch.setattr(store, "lifecycle_event", fail)
    else:
        monkeypatch.setattr(ref.contacts.boundary.audit, "append", fail)
    with pytest.raises(RuntimeError):
        create(ref, initial_email="private@example.com")
    assert all(not rows for rows in state(factory))
    assert read(factory, "SELECT * FROM command_receipts") == []
