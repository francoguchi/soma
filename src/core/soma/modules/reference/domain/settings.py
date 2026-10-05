"""Closed, pure setting contracts. Semantic validators belong to registering owners."""

from dataclasses import dataclass
from collections.abc import Callable
import inspect
import re

from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.strict_json import canonical_json_bytes_bounded, loads_strict_bytes
from soma.foundation.transactions import BOUNDS


def identifier(value):
    if type(value) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,255}", value) is None:
        raise ValidationError("Invalid setting contract identifier.")
    return value


def positive_version(value):
    if type(value) is not int or value < 1:
        raise ValidationError("Setting version must be a positive integer.")
    return value


@dataclass(frozen=True)
class SettingUpgrade:
    origin_contract: str
    origin_version: int
    validator: Callable
    convert: Callable
    max_utf8_bytes: int = 65536
    max_depth: int = 7
    max_collection_items: int = 500


@dataclass(frozen=True)
class SettingDefinition:
    setting_key: str
    semantic_owner: str
    contract_name: str
    current_version: int
    default_provider: Callable
    validator: Callable
    semantic_equals: Callable
    unknown_field_policy: str = "reject"
    storage_class: str = "ordinary_nonsecret"
    max_utf8_bytes: int = 65536
    max_depth: int = 7
    max_collection_items: int = 500
    state_validator: Callable | None = None
    upgrades: tuple[SettingUpgrade, ...] = ()

    @property
    def bounds(self):
        return dict(
            max_bytes=self.max_utf8_bytes,
            max_depth=self.max_depth,
            max_collection_items=self.max_collection_items,
        )

    def validate_value(self, value):
        return strict_value(value, self.validator, self.bounds)

    def validate_definition(self):
        for item in (self.setting_key, self.semantic_owner, self.contract_name):
            identifier(item)
        positive_version(self.current_version)
        if self.storage_class != "ordinary_nonsecret":
            raise SomaError(
                "SETTING_SECRET_FORBIDDEN",
                "Secret settings belong to their security owner.",
                "correct_input",
            )
        if self.unknown_field_policy != "reject":
            raise ValidationError("Settings accept only reject unknown-field policy.")
        validate_bounds(self.bounds)
        for callback in (self.default_provider, self.validator, self.semantic_equals):
            validate_callback(callback)
        if self.state_validator is not None:
            validate_callback(self.state_validator)
        if type(self.upgrades) is not tuple:
            raise ValidationError("Setting upgrades must be closed registrations.")
        origins = set()
        for upgrade in self.upgrades:
            if type(upgrade) is not SettingUpgrade:
                raise ValidationError("Invalid registered setting upgrade.")
            identifier(upgrade.origin_contract)
            positive_version(upgrade.origin_version)
            origin = (upgrade.origin_contract, upgrade.origin_version)
            if origin in origins or origin == (self.contract_name, self.current_version):
                raise ValidationError("Duplicate or current setting upgrade origin.")
            origins.add(origin)
            validate_callback(upgrade.validator)
            validate_callback(upgrade.convert)
            validate_bounds(upgrade_bounds(upgrade))
        self.validate_value(self.default_provider())


def upgrade_bounds(upgrade):
    return dict(
        max_bytes=upgrade.max_utf8_bytes,
        max_depth=upgrade.max_depth,
        max_collection_items=upgrade.max_collection_items,
    )


def validate_bounds(bounds):
    # Reserve room for the command/result envelope under Foundation ceilings.
    ceilings = dict(
        max_bytes=BOUNDS["max_bytes"] - 4096,
        max_depth=BOUNDS["max_depth"] - 1,
        max_collection_items=BOUNDS["max_collection_items"] - 12,
    )
    if any(
        type(value) is not int or not 1 <= value <= ceilings[key] for key, value in bounds.items()
    ):
        raise ValidationError("Setting bounds exceed the command contract ceiling.")


def validate_callback(callback):
    if not callable(callback) or inspect.iscoroutinefunction(callback):
        raise ValidationError("Setting callbacks must be synchronous owner code.")


def strict_value(value, validator, bounds):
    try:
        raw = canonical_json_bytes_bounded(value, **bounds)
    except ValidationError:
        raise SomaError(
            "FIELD_BOUND_EXCEEDED",
            "Setting JSON violates its accepted bounds or shape.",
            "correct_input",
        ) from None
    # Owner validation may not drop unknown fields, mutate input, or coerce values.
    candidate = loads_strict_bytes(raw, max_bytes=bounds["max_bytes"])
    try:
        accepted = validator(candidate)
        if (
            canonical_json_bytes_bounded(accepted, **bounds) != raw
            or canonical_json_bytes_bounded(candidate, **bounds) != raw
        ):
            raise ValueError()
    except Exception:
        raise ValidationError("Setting value does not satisfy its registered contract.") from None
    return loads_strict_bytes(raw)


class SettingDefinitionRegistry:
    def __init__(self):
        self._definitions = {}
        self._finalized = False

    def register(self, definition):
        if self._finalized or type(definition) is not SettingDefinition:
            raise ValidationError("Setting registration is closed or invalid.")
        definition.validate_definition()
        if definition.setting_key in self._definitions:
            raise ValidationError("Setting key is already registered.")
        self._definitions[definition.setting_key] = definition

    def finalize(self):
        if self._finalized:
            raise ValidationError("Setting registry is already finalized.")
        self._finalized = True

    def require_finalized(self):
        if not self._finalized:
            raise ValidationError("Setting registry must be finalized.")

    def require(self, key):
        self.require_finalized()
        identifier(key)
        definition = self._definitions.get(key)
        if definition is None:
            raise SomaError("SETTING_UNKNOWN", "Setting key is not registered.", "correct_input")
        return definition

    def all_for_owner(self, owner):
        self.require_finalized()
        identifier(owner)
        return tuple(
            self._definitions[key]
            for key in sorted(self._definitions)
            if self._definitions[key].semantic_owner == owner
        )

    def all_definitions(self):
        self.require_finalized()
        return tuple(self._definitions[key] for key in sorted(self._definitions))
