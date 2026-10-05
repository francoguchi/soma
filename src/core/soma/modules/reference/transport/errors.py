"""Closed Reference failures projected onto Foundation's safe error envelope."""

from soma.foundation.errors import SomaError, error_envelope

ERRORS = {
    "CUSTOMER_ORG_INACTIVE": ("Customer is inactive.", "refresh"),
    "ACCOUNT_CODE_CONFLICT_REVIEW": ("Account Code requires conflict review.", "refresh"),
    "ACCOUNT_CODE_SOURCE_NOT_OWNER": ("Source no longer owns the Account Code.", "refresh"),
    "ACCOUNT_CODE_SHARED_CONTEXT_REQUIRED": (
        "Account Code review context is required.",
        "correct_input",
    ),
    "REVIEW_CONTEXT_STALE": ("Account Code review context changed.", "refresh"),
    "MATCH_PROFILE_UNSUPPORTED": ("Stored matching profile requires a compatible build.", "none"),
    "MATCH_INPUT_INVALID": ("Reference input does not satisfy the contract.", "correct_input"),
    "SINGLETON_PROFILE_EXISTS": ("Local User Profile already exists.", "refresh"),
    "FIELD_BOUND_EXCEEDED": ("Reference field exceeds its accepted bound.", "correct_input"),
    "PROFILE_SETUP_INCOMPLETE": (
        "Configured development instance requires explicit profile setup reset.",
        "restart",
    ),
    "STALE_REVISION": ("Reference metadata revision changed.", "refresh"),
}


def reference_error_envelope(error, *, correlation_id=None):
    if isinstance(error, SomaError) and error.code in ERRORS:
        summary, recoverability = ERRORS[error.code]
        error = SomaError(error.code, summary, recoverability)
    return error_envelope(error, correlation_id)
