from __future__ import annotations

import re

from soma.foundation.errors import SomaError

from .matching import normalize_match_key


def _invalid(summary: str) -> SomaError:
    return SomaError("MATCH_INPUT_INVALID", summary, "correct_input")


def validate_single_line_text(value: str, *, field: str, max_utf8_bytes: int) -> str:
    if not isinstance(value, str):
        raise _invalid(f"{field} must be a string.")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise _invalid(f"{field} is not valid Unicode text.") from exc
    if not encoded:
        raise _invalid(f"{field} cannot be empty.")
    if len(encoded) > max_utf8_bytes:
        raise SomaError(
            "FIELD_BOUND_EXCEEDED",
            f"{field} exceeds its UTF-8 byte bound.",
            "correct_input",
        )
    if "\x00" in value or "\r" in value or "\n" in value:
        raise _invalid(f"{field} contains a forbidden control/newline.")
    return value


def validate_display_name(value: str) -> str:
    stored = validate_single_line_text(value, field="display_name", max_utf8_bytes=512)
    if not stored.strip():
        raise _invalid("display_name cannot be blank.")
    return stored


def validate_customer_name(value: str) -> tuple[str, str]:
    stored = validate_single_line_text(
        value, field="customer_organization.name", max_utf8_bytes=1024
    )
    return stored, normalize_match_key(stored, raw_max_utf8_bytes=1024)


def validate_account_code(value: str) -> tuple[str, str]:
    stored = validate_single_line_text(value, field="customer_account_code", max_utf8_bytes=512)
    return stored, normalize_match_key(stored, raw_max_utf8_bytes=512)


def validate_reason_category(value: str | None) -> str | None:
    if value is None:
        return None
    stored = validate_single_line_text(value, field="reason_category", max_utf8_bytes=128)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", stored) is None:
        raise _invalid("reason_category must be a category code.")
    return stored


def validate_review_context_id(value: str | None) -> str | None:
    if value is None:
        return None
    return validate_single_line_text(value, field="review_context_id", max_utf8_bytes=256)
