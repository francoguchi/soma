"""Only trusted, owner-authored messages belong in handled errors."""

from dataclasses import dataclass
from typing import Literal

from soma.foundation.context import current_correlation

Recoverability = Literal["correct_input", "retry", "refresh", "reauthenticate", "restart", "none"]


@dataclass(frozen=True, slots=True)
class FieldError:
    path: str
    code: str
    summary: str


class SomaError(Exception):
    def __init__(
        self,
        code: str,
        summary: str,
        recoverability: Recoverability = "none",
        safe_next_action: str | None = None,
        fields: tuple[FieldError, ...] | None = None,
    ) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary
        self.recoverability = recoverability
        self.safe_next_action = safe_next_action
        self.fields = fields


class ValidationError(SomaError):
    def __init__(self, summary: str = "Input does not satisfy the contract.") -> None:
        super().__init__("VALIDATION_FAILED", summary, "correct_input")


COMMON_ERRORS: dict[str, tuple[str, Recoverability]] = {
    "UNAUTHENTICATED": ("Authentication is required.", "reauthenticate"),
    "FORBIDDEN": ("This operation is not permitted.", "none"),
    "NOT_FOUND": ("The requested resource is unavailable.", "refresh"),
    "CONFLICT": ("The operation conflicts with current state.", "refresh"),
    "PERSISTENCE_FAILURE": ("Data storage is unavailable.", "restart"),
    "MIGRATION_FAILURE": ("Database initialization failed.", "restart"),
    "NOT_READY": ("The application is not ready.", "retry"),
    "BUSY": ("The operation is temporarily busy.", "retry"),
    "INTEGRITY_FAILURE": ("Integrity verification failed.", "none"),
    "INTERNAL_ERROR": ("The operation could not be completed.", "none"),
}


def error_envelope(error: Exception, correlation_id: str | None = None) -> dict:
    from soma.foundation.contracts import validate_contract

    if not isinstance(error, SomaError):
        error = SomaError("INTERNAL_ERROR", *COMMON_ERRORS["INTERNAL_ERROR"])
    value = {
        "code": error.code,
        "summary": error.summary,
        "recoverability": error.recoverability,
        "safe_next_action": error.safe_next_action,
        "correlation_id": correlation_id if correlation_id is not None else current_correlation(),
    }
    if error.fields is not None:
        value["fields"] = [
            {"path": field.path, "code": field.code, "summary": field.summary}
            for field in error.fields
        ]
    validate_contract("urn:soma:00:error-envelope:v1", value)
    return value
