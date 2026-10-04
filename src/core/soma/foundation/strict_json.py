"""Beta strict parsing/canonical encoding, with complete container validation."""

import hashlib
import json
import math
from typing import Any

from soma.foundation.errors import ValidationError


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("Duplicate JSON object key.")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValidationError("Non-finite JSON number is forbidden.")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValidationError("JSON number exceeds the finite numeric range.")
    return parsed


def _validate(
    value: Any, depth: int = 0, ancestors: frozenset[int] = frozenset()
) -> tuple[int, int]:
    if type(value) is str:
        value.encode("utf-8", errors="strict")
    elif value is None or type(value) in (bool, int):
        pass
    elif type(value) is float:
        if not math.isfinite(value):
            raise ValidationError("Non-finite JSON number is forbidden.")
    elif type(value) in (dict, list):
        if id(value) in ancestors:
            raise ValidationError("Cyclic JSON container.")
        ancestors = ancestors | {id(value)}
        items = len(value)
        max_depth = depth
        if type(value) is dict:
            for key in value:
                if type(key) is not str:
                    raise ValidationError("JSON object keys must be strings.")
                key.encode("utf-8", errors="strict")
            children = value.values()
        else:
            children = value
        for child in children:
            child_depth, child_items = _validate(child, depth + 1, ancestors)
            max_depth = max(max_depth, child_depth)
            items += child_items
        return max_depth, items
    else:
        raise ValidationError("Unsupported JSON value or collection.")
    return depth, 0


def loads_strict(text: str, *, max_bytes: int | None = None) -> Any:
    try:
        if max_bytes is not None and len(text.encode("utf-8")) > max_bytes:
            raise ValidationError("JSON input exceeds UTF-8 byte bound.")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_nonfinite,
            parse_float=_finite_float,
        )
        _validate(value)
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ValidationError("Malformed JSON.") from exc


def loads_strict_bytes(raw: bytes, *, max_bytes: int | None = None) -> Any:
    try:
        return loads_strict(raw.decode("utf-8", errors="strict"), max_bytes=max_bytes)
    except (UnicodeError, AttributeError) as exc:
        raise ValidationError("JSON input is not valid UTF-8.") from exc


def canonical_json_bytes(value: Any) -> bytes:
    try:
        _validate(value)
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ValidationError("Value cannot be canonicalized as JSON.") from exc


def sha256_canonical_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def canonical_json_bytes_bounded(
    value: Any, *, max_bytes: int, max_depth: int, max_collection_items: int
) -> bytes:
    encoded = canonical_json_bytes(value)
    depth, items = _validate(value)
    if len(encoded) > max_bytes or depth > max_depth or items > max_collection_items:
        raise ValidationError("JSON contract byte, depth, or collection bound exceeded.")
    return encoded


def loads_canonical_json(text: str, **bounds: int) -> Any:
    value = loads_strict(text, max_bytes=bounds.get("max_bytes"))
    if canonical_json_bytes_bounded(value, **bounds) != text.encode("utf-8"):
        raise ValidationError("JSON text is not canonical.")
    return value
