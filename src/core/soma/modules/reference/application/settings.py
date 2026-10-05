"""Replay-first typed writes and explicit upgrades; reads never mutate."""

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import require_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.strict_json import canonical_json_bytes, loads_strict, loads_strict_bytes
from soma.foundation.time import utc_epoch_seconds
from soma.foundation.transactions import CommandBoundary, ResultContract
from soma.modules.reference.adapters.persistence import settings as store
from soma.modules.reference.domain.settings import (
    identifier,
    positive_version,
    strict_value,
    upgrade_bounds,
)
from soma.modules.reference.ports.settings import SettingValue
from .commands import event, revision


def mismatch():
    return SomaError(
        "SETTING_CONTRACT_MISMATCH",
        "Stored setting requires a compatible registered contract or explicit upgrade.",
        "none",
    )


def validate_result(value):
    if type(value) is not dict or set(value) != {
        "outcome",
        "setting_key",
        "semantic_owner",
        "contract_name",
        "contract_version",
        "value",
        "revision",
        "source",
    }:
        raise ValidationError("Invalid setting command result.")
    for key in ("setting_key", "semantic_owner", "contract_name"):
        identifier(value[key])
    positive_version(value["contract_version"])
    revision(value["revision"])
    if value["outcome"] not in {"APPLIED", "NO_CHANGE"} or value["source"] != "PERSISTED":
        raise ValidationError("Invalid setting result classification.")


RESULT = ResultContract("SettingMutationResultV1", 1, validate_result)


class Settings:
    def __init__(self, factory, audit_writer, registry):
        registry.require_finalized()
        self.factory, self.registry = factory, registry
        self.boundary = CommandBoundary(factory, [RESULT], audit_writer)

    def get_definition(self, key):
        return self.registry.require(key)

    def definitions_for_owner(self, owner):
        return self.registry.all_for_owner(owner)

    @staticmethod
    def _parse(definition, row):
        if tuple(row[:2]) != (definition.contract_name, definition.current_version):
            raise mismatch()
        try:
            return definition.validate_value(
                loads_strict(row[2], max_bytes=definition.max_utf8_bytes)
            )
        except Exception:
            raise mismatch() from None

    def get(self, snapshot, key):
        definition = self.get_definition(key)
        row = store.load(snapshot.connection, key)
        if row is None:
            value = definition.validate_value(definition.default_provider())
            rev, source = None, "DEFAULT"
        else:
            value = self._parse(definition, row)
            rev, source = row[3], "PERSISTED"
        return SettingValue(
            key,
            definition.semantic_owner,
            definition.contract_name,
            definition.current_version,
            value,
            rev,
            source,
        )

    @staticmethod
    def _contract(definition, owner, contract, version):
        if (owner, contract, version) != (
            definition.semantic_owner,
            definition.contract_name,
            definition.current_version,
        ):
            raise SomaError(
                "SETTING_CONTRACT_MISMATCH",
                "Requested setting owner/contract does not match its registration.",
                "none",
            )

    @staticmethod
    def _state(definition, uow, value):
        if definition.state_validator is not None:
            raw = canonical_json_bytes(value)
            candidate = loads_strict_bytes(raw)
            try:
                outcome = definition.state_validator(store.StateReader(uow.connection), candidate)
                if outcome is not None or canonical_json_bytes(candidate) != raw:
                    raise ValueError()
            except Exception:
                raise ValidationError("Setting owner state validation failed.") from None

    @staticmethod
    def _result(definition, value, rev, changed=True):
        return dict(
            outcome="APPLIED" if changed else "NO_CHANGE",
            setting_key=definition.setting_key,
            semantic_owner=definition.semantic_owner,
            contract_name=definition.contract_name,
            contract_version=definition.current_version,
            value=value,
            revision=rev,
            source="PERSISTED",
        )

    def _apply(self, definition, command_id, value, prior, change_kind, actor_id):
        rev = 1 if prior is None else prior + 1
        raw, now = canonical_json_bytes(value).decode(), utc_epoch_seconds()
        audit = event(
            "setting.written",
            command_id,
            definition.setting_key,
            dict(
                setting_key=definition.setting_key,
                semantic_owner=definition.semantic_owner,
                contract_name=definition.contract_name,
                contract_version=definition.current_version,
                prior_revision=prior,
                new_revision=rev,
                change_kind=change_kind,
            ),
            actor_id,
            target_type="setting",
            results=(("setting", definition.setting_key),),
        )

        def apply(uow):
            if prior is None:
                store.insert(
                    uow.connection,
                    definition.setting_key,
                    definition.contract_name,
                    definition.current_version,
                    raw,
                    now,
                    command_id,
                )
            else:
                store.update(
                    uow.connection,
                    definition.setting_key,
                    definition.contract_name,
                    definition.current_version,
                    raw,
                    prior,
                    now,
                    command_id,
                )
            return self._result(definition, value, rev), [audit]

        return apply

    def write(
        self,
        *,
        command_id,
        setting_key,
        semantic_owner,
        contract_name,
        contract_version,
        base_revision,
        value,
        actor_id=None,
    ):
        data = {}

        def preflight():
            definition = self.get_definition(setting_key)
            identifier(semantic_owner)
            identifier(contract_name)
            positive_version(contract_version)
            self._contract(definition, semantic_owner, contract_name, contract_version)
            if base_revision is not None:
                revision(base_revision)
            if actor_id is not None:
                require_uuid4(actor_id)
            data["definition"], data["value"] = definition, definition.validate_value(value)

        def prepare(uow):
            definition, accepted = data["definition"], data["value"]
            row = store.load(uow.connection, setting_key)
            if (row is None and base_revision is not None) or (
                row is not None and row[3] != base_revision
            ):
                raise SomaError("STALE_REVISION", "Setting revision or absence changed.", "refresh")
            current = None if row is None else self._parse(definition, row)
            self._state(definition, uow, accepted)
            if row is not None:
                left, right = canonical_json_bytes(current), canonical_json_bytes(accepted)
                try:
                    equal = definition.semantic_equals(current, accepted)
                    if (
                        type(equal) is not bool
                        or canonical_json_bytes(current) != left
                        or canonical_json_bytes(accepted) != right
                    ):
                        raise ValueError()
                except Exception:
                    raise ValidationError("Setting equality contract failed.") from None
                if equal:
                    return lambda inner: (
                        self._result(definition, current, base_revision, False),
                        [],
                        False,
                    )
            return self._apply(
                definition,
                command_id,
                accepted,
                base_revision,
                "CREATE" if row is None else "UPDATE",
                actor_id,
            )

        return self.boundary.execute(
            command_id,
            "setting.write",
            dict(
                setting_key=setting_key,
                semantic_owner=semantic_owner,
                contract_name=contract_name,
                contract_version=contract_version,
                base_revision=base_revision,
                value=value,
                actor_id=actor_id,
            ),
            (RESULT.schema, RESULT.version),
            None,
            preflight=preflight,
            prepare=prepare,
        )

    def upgrade(
        self,
        *,
        command_id,
        setting_key,
        semantic_owner,
        contract_name,
        contract_version,
        origin_contract,
        origin_version,
        base_revision,
        actor_id=None,
    ):
        data = {}

        def preflight():
            definition = self.get_definition(setting_key)
            self._contract(
                definition, semantic_owner, contract_name, positive_version(contract_version)
            )
            identifier(origin_contract)
            positive_version(origin_version)
            revision(base_revision)
            if actor_id is not None:
                require_uuid4(actor_id)
            upgrade = next(
                (
                    item
                    for item in definition.upgrades
                    if (item.origin_contract, item.origin_version)
                    == (origin_contract, origin_version)
                ),
                None,
            )
            if upgrade is None:
                raise mismatch()
            with ReadSnapshot(self.factory) as snapshot:
                row = store.load(snapshot.connection, setting_key)
                if row is None or row[3] != base_revision:
                    raise SomaError("STALE_REVISION", "Setting revision changed.", "refresh")
                if tuple(row[:2]) != (origin_contract, origin_version):
                    raise mismatch()
                try:
                    old = strict_value(
                        loads_strict(row[2], max_bytes=upgrade.max_utf8_bytes),
                        upgrade.validator,
                        upgrade_bounds(upgrade),
                    )
                    value = definition.validate_value(upgrade.convert(old))
                except Exception:
                    raise mismatch() from None
            data.update(definition=definition, value=value, row=row)

        def prepare(uow):
            definition = data["definition"]
            if store.load(uow.connection, setting_key) != data["row"]:
                raise SomaError("STALE_REVISION", "Setting upgrade source changed.", "refresh")
            self._state(definition, uow, data["value"])
            return self._apply(
                definition, command_id, data["value"], base_revision, "UPGRADE", actor_id
            )

        return self.boundary.execute(
            command_id,
            "setting.upgrade",
            dict(
                setting_key=setting_key,
                semantic_owner=semantic_owner,
                contract_name=contract_name,
                contract_version=contract_version,
                origin_contract=origin_contract,
                origin_version=origin_version,
                base_revision=base_revision,
                actor_id=actor_id,
            ),
            (RESULT.schema, RESULT.version),
            None,
            preflight=preflight,
            prepare=prepare,
        )
