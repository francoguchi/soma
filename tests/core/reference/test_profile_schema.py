import pytest

from soma.foundation.errors import SomaError
from soma.foundation.identity import new_uuid4
from soma.foundation.persistence.schema_verify import verify_schema, verify_fk_indexes
from soma.foundation.security.auth import Authentication
from soma.foundation.security.sessions import Sessions
from soma.foundation.transactions import UnitOfWork, _active
from soma.modules.reference.composition import compose
from soma.modules.reference.application import customer as application
from .test_customer import read


class Log:
    def emit(self, *args):
        pass


def setup(ref, factory):
    sessions = Sessions(new_uuid4(), "http://127.0.0.1:12345")
    auth = Authentication(factory, sessions, Log(), profile_participant=ref.profile)
    auth.setup("abcdefghijklmnop", "abcdefghijklmnop")
    return auth, sessions


def test_same_uow_profile_setup_metadata_update_no_change_replay_and_privacy(reference):
    ref, factory, _ = reference
    auth, sessions = setup(ref, factory)
    profile = ref.profile.get_singleton()
    actor = auth.credential()[0]
    assert profile == {
        "local_user_profile_id": actor,
        "display_name": "Local Administrator",
        "revision": 1,
    }
    credential = auth.credential()
    session_state = dict(sessions.entries)
    request = dict(
        command_id=new_uuid4(), actor_id=actor, base_revision=1, display_name="Private Person"
    )
    assert ref.profile.update_display_name(**request)["revision"] == 2
    before = read(factory, "SELECT * FROM audit_events")
    no_change_request = request | {"command_id": new_uuid4(), "base_revision": 2}
    assert ref.profile.update_display_name(**no_change_request)["outcome"] == "NO_CHANGE"
    assert read(factory, "SELECT * FROM audit_events") == before
    ref.profile.update_display_name(
        **(request | {"command_id": new_uuid4(), "base_revision": 2, "display_name": "Later"})
    )
    assert ref.profile.update_display_name(**no_change_request)["revision"] == 2
    assert auth.credential() == credential and sessions.entries == session_state
    assert "Private Person" not in str(read(factory, "SELECT payload_json FROM audit_events"))
    with pytest.raises(SomaError) as exc:
        ref.profile.update_display_name(
            **(request | {"command_id": new_uuid4(), "display_name": "Private Person"})
        )
    assert exc.value.code == "STALE_REVISION"


def test_profile_participant_failure_rolls_back_credentials_profile_receipt_audit_sessions(
    reference, monkeypatch
):
    ref, factory, _ = reference
    sessions = Sessions(new_uuid4(), "http://127.0.0.1:12345")
    auth = Authentication(factory, sessions, Log(), profile_participant=ref.profile)
    monkeypatch.setattr(
        ref.profile.audit,
        "append",
        lambda *args: (_ for _ in ()).throw(SomaError("AUDIT_FAILED", "Injected failure.")),
    )
    with pytest.raises(SomaError):
        auth.setup("abcdefghijklmnop", "abcdefghijklmnop")
    for table in (
        "local_admin_credentials",
        "local_user_profiles",
        "command_receipts",
        "audit_events",
    ):
        assert read(factory, "SELECT * FROM " + table) == []
    assert not sessions.entries


def test_composition_requires_reset_for_preexisting_credentials_without_profile(reference):
    ref, factory, _ = reference
    auth = Authentication(factory, Sessions(new_uuid4(), "http://127.0.0.1:12345"), Log())
    auth.setup("abcdefghijklmnop", "abcdefghijklmnop")
    with pytest.raises(SomaError) as exc:
        compose(factory)
    assert exc.value.code == "PROFILE_SETUP_INCOMPLETE"
    assert ref.profile.get_singleton() is None


def test_preflight_outside_writer_state_before_receipt_and_writes_after_receipt(
    reference, monkeypatch
):
    ref, factory, _ = reference
    command = new_uuid4()
    original_validate = application.validate_customer_name
    original_insert = application.store.insert_customer
    original_profile = application.require_persisted_matching_profile

    def validate(value):
        assert not _active.get()
        return original_validate(value)

    def guard(connection):
        assert _active.get()
        assert (
            connection.execute(
                "SELECT 1 FROM command_receipts WHERE command_id=?", (command,)
            ).fetchone()
            is None
        )
        return original_profile(connection)

    def insert(connection, *args):
        assert connection.execute(
            "SELECT 1 FROM command_receipts WHERE command_id=?", (command,)
        ).fetchone() == (1,)
        original_insert(connection, *args)

    monkeypatch.setattr(application, "validate_customer_name", validate)
    monkeypatch.setattr(application, "require_persisted_matching_profile", guard)
    monkeypatch.setattr(application.store, "insert_customer", insert)
    ref.customers.create_customer_organization(command_id=command, name="Ordered")


def test_exact_schema_strict_fk_indexes_profile_identity_and_immutable_history(reference):
    ref, factory, manifest = reference
    setup(ref, factory)
    customer = ref.customers.create_customer_organization(
        command_id=new_uuid4(), name="Schema", account_code="CODE"
    )["target_id"]
    connection = factory.open()
    try:
        verify_schema(connection, manifest, deep=True)
        verify_fk_indexes(connection)
        tables = {row[1]: row[5] for row in connection.execute("PRAGMA table_list")}
        assert all(
            tables[name] == 1
            for name in (
                "reference_metadata",
                "local_user_profiles",
                "customer_organizations",
                "customer_org_identifiers",
                "reference_lifecycle_events",
            )
        )
        assert not {"dispatch_locations", "setting_values"} & tables.keys()
        rejected = (
            ("UPDATE local_user_profiles SET local_user_profile_id=?", (new_uuid4(),)),
            ("DELETE FROM local_user_profiles", ()),
            ("UPDATE local_user_profiles SET created_at_utc=1", ()),
            ("UPDATE customer_organizations SET customer_org_id=?", (new_uuid4(),)),
            ("DELETE FROM customer_organizations", ()),
            ("UPDATE customer_organizations SET created_at_utc=1", ()),
            ("UPDATE customer_org_identifiers SET value_text='rewrite'", ()),
            ("DELETE FROM customer_org_identifiers", ()),
            ("UPDATE reference_lifecycle_events SET event_type='archived'", ()),
            ("DELETE FROM reference_lifecycle_events", ()),
            ("DELETE FROM reference_metadata", ()),
        )
        for sql, parameters in rejected:
            with pytest.raises(Exception):
                connection.execute(sql, parameters)
        assert read(factory, "SELECT customer_org_id FROM customer_organizations") == [(customer,)]
    finally:
        connection.close()


@pytest.mark.parametrize(
    "tamper",
    [
        "DROP INDEX idx_customer_identifier_superseded_command",
        "DROP TRIGGER reference_lifecycle_events_update_forbidden",
        "UPDATE reference_metadata SET matching_profile_id='unsupported'",
    ],
)
def test_schema_tamper_fails_readiness(reference, tamper):
    _, factory, manifest = reference
    connection = factory.open()
    try:
        connection.execute(tamper)
        with pytest.raises(SomaError) as exc:
            verify_schema(connection, manifest)
        assert exc.value.code == "PERSISTENCE_SCHEMA_MISMATCH"
    finally:
        connection.close()


@pytest.mark.parametrize(
    "field,value",
    [("name", "x" * 1025), ("name", "bad\nname"), ("name", " "), ("account_code", "x" * 513)],
)
def test_field_errors_before_receipt(reference, field, value):
    ref, factory, _ = reference
    request = dict(command_id=new_uuid4(), name="Valid") | {field: value}
    with pytest.raises(SomaError) as exc:
        ref.customers.create_customer_organization(**request)
    assert exc.value.recoverability == "correct_input"
    assert read(factory, "SELECT * FROM command_receipts") == []


def test_profile_fk_rejects_identity_not_in_credentials(reference):
    _, factory, _ = reference
    with pytest.raises(SomaError):
        with UnitOfWork(factory) as uow:
            uow.connection.execute(
                "INSERT INTO local_user_profiles VALUES (?,1,'Invalid',1,0,0)", (new_uuid4(),)
            )
