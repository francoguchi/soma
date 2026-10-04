"""Boundary validation from generated authoritative schema resources."""

from functools import lru_cache
from importlib.resources import files

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from soma.foundation.errors import ValidationError
from soma.foundation.strict_json import canonical_json_bytes, loads_strict


@lru_cache
def _validators() -> dict[str, Draft202012Validator]:
    schemas = loads_strict(
        files("soma.foundation").joinpath("contracts.schemas.json").read_text(encoding="utf-8")
    )
    registry = Registry().with_resources(
        (key, Resource.from_contents(schema)) for key, schema in schemas.items()
    )
    return {key: Draft202012Validator(schema, registry=registry) for key, schema in schemas.items()}


def validate_contract(contract_id: str, value):
    canonical_json_bytes(value)
    validator = _validators().get(contract_id)
    if validator is None:
        raise ValidationError("Unsupported contract identity.")
    if not validator.is_valid(value):
        raise ValidationError("Value does not satisfy the declared contract.")
    return value
