"""Pinned Settings donor vectors rewritten for current strict contracts and UoW."""

from dataclasses import replace
import pytest

from soma.foundation.appearance import APPEARANCE_KEY, validate_appearance
from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.persistence.schema_verify import verify_schema, verify_fk_indexes
from soma.foundation.strict_json import loads_strict
from soma.foundation.transactions import UnitOfWork, _active
from soma.modules.reference.composition import compose
from soma.modules.reference.domain.settings import (
    SettingDefinition,
    SettingDefinitionRegistry,
    SettingUpgrade,
)
from soma.modules.reference.application import settings as application
from soma.modules.reference.adapters.persistence import settings as store
from .test_customer import read


def validate(value):
    if type(value) is not dict or set(value) != {"enabled"} or type(value["enabled"]) is not bool:
        raise ValidationError("Invalid synthetic setting.")
    return value


def definition(**kwargs):
    return SettingDefinition(
        "test.enabled",
        "synthetic",
        "EnabledV1",
        1,
        lambda: {"enabled": False},
        validate,
        lambda a, b: a == b,
        max_utf8_bytes=256,
        max_depth=2,
        max_collection_items=4,
        **kwargs,
    )


def settings(reference, *definitions):
    _, factory, _ = reference
    return compose(factory, setting_definitions=definitions or (definition(),)).settings


def request(**changes):
    return (
        dict(
            command_id=new_uuid4(),
            setting_key="test.enabled",
            semantic_owner="synthetic",
            contract_name="EnabledV1",
            contract_version=1,
            base_revision=None,
            value={"enabled": True},
        )
        | changes
    )


def state(factory):
    return [
        read(factory, "SELECT * FROM " + table)
        for table in (
            "setting_values",
            "command_receipts",
            "command_receipt_results",
            "audit_events",
            "audit_event_results",
        )
    ]


def test_defaults_multiple_owners_and_foundation_semantics_no_writes(reference):
    _, factory, _ = reference
    service = settings(reference)
    before = state(factory)
    with ReadSnapshot(factory) as snapshot:
        default = service.get(snapshot, "test.enabled")
        assert (
            default.value == {"enabled": False}
            and default.revision is None
            and default.source == "DEFAULT"
        )
        default.value["enabled"] = True
        assert service.get(snapshot, "test.enabled").value == {"enabled": False}
        appearance = service.get(snapshot, APPEARANCE_KEY)
        assert appearance.value == "core_dark" and appearance.semantic_owner == "foundation"
    assert state(factory) == before
    assert service.definitions_for_owner("synthetic") == (service.get_definition("test.enabled"),)
    assert service.definitions_for_owner("missing") == ()
    contract = service.get_definition(APPEARANCE_KEY)
    assert contract.validator is validate_appearance
    for mode in ("system", "light", "core_dark"):
        prior = read(
            factory, "SELECT revision FROM setting_values WHERE setting_key=?", (APPEARANCE_KEY,)
        )
        service.write(
            **request(
                setting_key=APPEARANCE_KEY,
                semantic_owner="foundation",
                contract_name="AppearancePreferenceV1",
                value=mode,
                base_revision=prior[0][0] if prior else None,
            )
        )
    with pytest.raises(SomaError):
        service.write(
            **request(
                setting_key=APPEARANCE_KEY,
                semantic_owner="foundation",
                contract_name="AppearancePreferenceV1",
                value="amber",
                base_revision=3,
            )
        )


def test_explicit_default_insert_update_no_change_exact_replay_privacy(reference, monkeypatch):
    _, factory, _ = reference
    service = settings(reference)
    first = request(value={"enabled": False})
    original = service.write(**first)
    assert original["outcome"] == "APPLIED" and original["revision"] == 1
    same = request(base_revision=1, value={"enabled": False})
    before = state(factory)
    unchanged = service.write(**same)
    after = state(factory)
    assert unchanged["outcome"] == "NO_CHANGE" and unchanged["revision"] == 1
    assert after[0] == before[0] and after[3:] == before[3:]
    assert len(after[1]) == len(before[1]) + 1 and len(after[2]) == len(before[2]) + 1
    assert service.write(**request(base_revision=1))["revision"] == 2
    monkeypatch.setattr(
        service,
        "get_definition",
        lambda *args: (_ for _ in ()).throw(AssertionError("replay registry lookup")),
    )
    assert service.write(**same) == unchanged
    assert service.write(**first) == original
    with pytest.raises(SomaError) as exc:
        service.write(**(same | dict(value={"enabled": True})))
    assert exc.value.code == "COMMAND_ID_CONFLICT"
    payload = str(read(factory, "SELECT payload_json FROM audit_events"))
    assert '"value"' not in payload and '"enabled"' not in payload


@pytest.mark.parametrize(
    "changes",
    [
        dict(setting_key="unknown"),
        dict(semantic_owner="other"),
        dict(contract_name="WrongV1"),
        dict(contract_version=2),
        dict(base_revision=True),
        dict(value={"enabled": True, "unknown": 1}),
        dict(value={"enabled": 1}),
        dict(value=float("nan")),
        dict(value={"enabled": "private value"}),
    ],
)
def test_rejects_unknown_contract_stale_invalid_without_receipt(reference, changes):
    _, factory, _ = reference
    service = settings(reference)
    before = state(factory)
    with pytest.raises(SomaError):
        service.write(**request(**changes))
    assert state(factory) == before


def test_stale_absence_revision_precedes_semantic_no_change(reference):
    _, factory, _ = reference
    service = settings(reference)
    service.write(**request())
    before = state(factory)
    for rev in (None, 2):
        with pytest.raises(SomaError) as exc:
            service.write(**request(base_revision=rev))
        assert exc.value.code == "STALE_REVISION"
    assert state(factory) == before


@pytest.mark.parametrize(
    "changes",
    [
        dict(storage_class="secret"),
        dict(unknown_field_policy="quarantine"),
        dict(unknown_field_policy="preserve-readonly"),
        dict(current_version=True),
        dict(setting_key="bad key"),
        dict(max_utf8_bytes=0),
        dict(max_depth=8),
        dict(max_collection_items=501),
        dict(validator=None),
    ],
)
def test_closed_registry_rejects_unsafe_definitions(changes):
    registry = SettingDefinitionRegistry()
    with pytest.raises(SomaError):
        registry.register(replace(definition(), **changes))


def test_registry_finalize_duplicate_defaults_and_mutating_validator():
    registry = SettingDefinitionRegistry()
    registry.register(definition())
    with pytest.raises(SomaError):
        registry.register(definition())
    registry.finalize()
    with pytest.raises(SomaError):
        registry.register(replace(definition(), setting_key="other"))

    def strips(value):
        value.pop("extra", None)
        return value

    bad = replace(definition(), validator=strips)
    with pytest.raises(SomaError):
        bad.validate_value({"enabled": False, "extra": True})
    with pytest.raises(SomaError):
        replace(definition(), default_provider=lambda: {"enabled": "bad"}).validate_definition()


def test_json_bounds_and_malformed_bytes(reference):
    _, factory, _ = reference
    definition_text = SettingDefinition(
        "test.text",
        "synthetic",
        "TextV1",
        1,
        lambda: "",
        lambda value: value,
        lambda a, b: a == b,
        max_utf8_bytes=10,
        max_depth=2,
        max_collection_items=4,
    )
    service = settings(reference, definition_text)
    assert definition_text.validate_value("\u00e9" * 4) == "\u00e9" * 4
    before = state(factory)
    for value in ("\u00e9" * 5, [[[[1]]]], [1, 2, 3, 4, 5], float("inf"), "\ud800", {1: True}):
        with pytest.raises(SomaError):
            service.write(**request(setting_key="test.text", contract_name="TextV1", value=value))
    for raw in ('{"enabled":true,"enabled":false}', "{", "NaN", "1e9999"):
        with pytest.raises(SomaError):
            loads_strict(raw)
    assert state(factory) == before


def test_state_guard_before_no_change_read_only_and_one_commit(reference, monkeypatch):
    _, factory, _ = reference
    calls = []
    permitted = [True]

    def state_check(reader, value):
        assert _active.get()
        assert reader.execute("SELECT 1").fetchone() == (1,)
        calls.append(value.copy())
        if not permitted[0]:
            raise ValidationError("private owner state")

    service = settings(reference, definition(state_validator=state_check))
    service.write(**request())
    before = state(factory)
    permitted[0] = False
    with pytest.raises(SomaError):
        service.write(**request(base_revision=1))
    assert state(factory) == before and len(calls) == 2

    def unsafe(reader, value):
        reader.execute("DELETE FROM setting_values")

    unsafe_service = settings(reference, definition(state_validator=unsafe))
    with pytest.raises(SomaError):
        unsafe_service.write(**request(base_revision=1))
    assert state(factory) == before
    permitted[0] = True
    trace = []
    original = factory.open

    def opened(*args, **kwargs):
        connection = original(*args, **kwargs)
        connection.set_trace_callback(trace.append)
        return connection

    monkeypatch.setattr(factory, "open", opened)
    service.write(**request(base_revision=1, value={"enabled": False}))
    start = trace.index("BEGIN IMMEDIATE")
    receipt = next(i for i, s in enumerate(trace) if s.startswith("INSERT INTO command_receipts"))
    update = next(i for i, s in enumerate(trace) if s.startswith("UPDATE setting_values"))
    audit = next(i for i, s in enumerate(trace) if s.startswith("INSERT INTO audit_events"))
    assert trace.count("BEGIN IMMEDIATE") == 1 and start < receipt < update < audit
    assert trace[start:].count("COMMIT") == 1
    assert not any("REPLACE" in sql for sql in trace)


@pytest.mark.parametrize("operation", ["insert", "update", "audit"])
def test_partial_sql_and_audit_failure_roll_back_all_evidence(reference, monkeypatch, operation):
    _, factory, _ = reference
    service = settings(reference)
    rev = None
    if operation != "insert":
        service.write(**request())
        rev = 1
    before = state(factory)
    if operation == "audit":

        def failure(*args):
            raise SomaError("INJECTED", "Injected audit failure.")

        monkeypatch.setattr(service.boundary.audit, "append", failure)
    else:
        original = getattr(store, operation)

        def failure(*args):
            original(*args)
            raise SomaError("INJECTED", "Injected SQL failure.")

        monkeypatch.setattr(store, operation, failure)
    with pytest.raises(SomaError):
        service.write(**request(base_revision=rev, value={"enabled": False}))
    assert state(factory) == before


def seed_old(factory, raw='{"enabled":1}', version=1, contract="LegacyEnabled"):
    with UnitOfWork(factory) as uow:
        command = new_uuid4()
        uow.connection.execute(
            "INSERT INTO command_receipts VALUES (?, 'synthetic.seed', ?, NULL, 0)",
            (command, "0" * 64),
        )
        uow.connection.execute(
            "INSERT INTO setting_values VALUES ('test.enabled',?,?,?,1,0,?)",
            (contract, version, raw, command),
        )


def old_validate(value):
    if (
        type(value) is not dict
        or set(value) != {"enabled"}
        or type(value["enabled"]) is not int
        or value["enabled"] not in (0, 1)
    ):
        raise ValidationError("Invalid old setting.")
    return value


def upgraded_definition(convert=lambda old: {"enabled": bool(old["enabled"])}):
    return definition(
        upgrades=(
            SettingUpgrade(
                "LegacyEnabled",
                1,
                old_validate,
                convert,
                max_utf8_bytes=256,
                max_depth=2,
                max_collection_items=4,
            ),
        )
    )


def upgrade_request(**kwargs):
    req = request(origin_contract="LegacyEnabled", origin_version=1, base_revision=1)
    req.pop("value")
    return req | kwargs


def test_exact_registered_upgrade_pure_read_atomic_write_and_replay(reference, monkeypatch):
    _, factory, _ = reference
    seed_old(factory)
    service = settings(reference, upgraded_definition())
    before = state(factory)
    with ReadSnapshot(factory) as snapshot:
        with pytest.raises(SomaError) as exc:
            service.get(snapshot, "test.enabled")
        assert exc.value.code == "SETTING_CONTRACT_MISMATCH"
    assert state(factory) == before
    req = upgrade_request()
    upgraded = service.upgrade(**req)
    assert upgraded["value"] == {"enabled": True} and upgraded["revision"] == 2
    with ReadSnapshot(factory) as snapshot:
        assert service.get(snapshot, "test.enabled").value == {"enabled": True}
    service.write(**request(base_revision=2, value={"enabled": False}))
    monkeypatch.setattr(
        service,
        "get_definition",
        lambda *args: (_ for _ in ()).throw(AssertionError("upgrade replay lookup")),
    )
    assert service.upgrade(**req) == upgraded


@pytest.mark.parametrize(
    "raw,contract,version",
    [
        ('{"enabled":1,"unknown":0}', "LegacyEnabled", 1),
        ('{"enabled":1,"enabled":0}', "LegacyEnabled", 1),
        ('{"enabled":1}', "Wrong", 1),
        ('{"enabled":1}', "LegacyEnabled", 2),
    ],
)
def test_unsupported_old_bytes_and_versions_fail_closed(reference, raw, contract, version):
    _, factory, _ = reference
    seed_old(factory, raw, version, contract)
    service = settings(reference, upgraded_definition())
    before = state(factory)
    with pytest.raises(SomaError) as exc:
        service.upgrade(**upgrade_request())
    assert exc.value.code == "SETTING_CONTRACT_MISMATCH" and state(factory) == before


@pytest.mark.parametrize("failure", ["convert", "new_contract", "audit"])
def test_upgrade_failure_preserves_prior_bytes_and_receipts(reference, monkeypatch, failure):
    _, factory, _ = reference
    seed_old(factory)

    def convert(old):
        assert not _active.get()
        if failure == "convert":
            raise RuntimeError("private old bytes")
        return {"enabled": "bad"} if failure == "new_contract" else {"enabled": True}

    service = settings(reference, upgraded_definition(convert))
    if failure == "audit":
        monkeypatch.setattr(
            service.boundary.audit,
            "append",
            lambda *args: (_ for _ in ()).throw(ValidationError("injected")),
        )
    before = state(factory)
    with pytest.raises(SomaError):
        service.upgrade(**upgrade_request())
    assert state(factory) == before


def test_upgrade_source_revalidated_after_preflight(reference, monkeypatch):
    _, factory, _ = reference
    seed_old(factory)
    service = settings(reference, upgraded_definition())
    original = application.store.load
    changed = [False]

    def loaded(connection, key):
        row = original(connection, key)
        if _active.get() and not changed[0]:
            changed[0] = True
            return row[:2] + ('{"enabled":0}',) + row[3:]
        return row

    monkeypatch.setattr(application.store, "load", loaded)
    before = state(factory)
    with pytest.raises(SomaError) as exc:
        service.upgrade(**upgrade_request())
    assert exc.value.code == "STALE_REVISION" and state(factory) == before


def test_schema_key_provenance_index_protection_and_tamper(reference):
    _, factory, manifest = reference
    service = settings(reference)
    service.write(**request())
    connection = factory.open()
    try:
        verify_schema(connection, manifest, deep=True)
        verify_fk_indexes(connection)
        assert manifest.generation == 10
        with pytest.raises(Exception):
            connection.execute("UPDATE setting_values SET setting_key='changed'")
        with pytest.raises(Exception):
            connection.execute("UPDATE setting_values SET command_id=?", (new_uuid4(),))
        assert read(factory, "SELECT setting_key FROM setting_values") == [("test.enabled",)]
        connection.execute("DROP TRIGGER setting_key_update_guard")
        with pytest.raises(SomaError):
            verify_schema(connection, manifest)
    finally:
        connection.close()
