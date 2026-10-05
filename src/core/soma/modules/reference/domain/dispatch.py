"""Bounded Dispatch values; no persistence or Site ownership."""

from soma.foundation.errors import SomaError
from .matching import normalize_match_key
from .validation import validate_single_line_text


def validate_dispatch_name(value):
    stored = validate_single_line_text(value, field="dispatch_location.name", max_utf8_bytes=1024)
    return stored, normalize_match_key(stored, raw_max_utf8_bytes=1024)


def validate_standalone_address(value):
    if type(value) is not str:
        raise SomaError("MATCH_INPUT_INVALID", "Address must be text.", "correct_input")
    stored = value.replace("\r\n", "\n").replace("\r", "\n")
    try:
        size = len(stored.encode("utf-8", errors="strict"))
    except UnicodeError:
        raise SomaError(
            "MATCH_INPUT_INVALID", "Address is not valid Unicode.", "correct_input"
        ) from None
    if size > 8192 or stored.count("\n") + 1 > 32:
        raise SomaError("FIELD_BOUND_EXCEEDED", "Address exceeds its bound.", "correct_input")
    if not stored.strip() or "\x00" in stored:
        raise SomaError(
            "MATCH_INPUT_INVALID", "Address must be nonblank and contain no NUL.", "correct_input"
        )
    return stored
