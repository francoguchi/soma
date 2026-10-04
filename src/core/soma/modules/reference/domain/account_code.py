from __future__ import annotations

import hmac
import string
from dataclasses import dataclass
from typing import Literal

from soma.foundation.errors import SomaError
from soma.foundation.identity import require_uuid4
from soma.foundation.strict_json import sha256_canonical_json

from .matching import PROFILE_ID

ProposedAction = Literal["CONFIRM_SHARED_CLAIM", "REASSIGN_CLAIM"]


@dataclass(frozen=True, slots=True)
class CustomerCodeState:
    customer_org_id: str
    revision: int
    current_code_key: str | None

    def validate(self) -> None:
        require_uuid4(self.customer_org_id)
        if type(self.revision) is not int or self.revision < 1:
            raise SomaError(
                "MATCH_INPUT_INVALID",
                "Customer review revision is invalid.",
                "correct_input",
            )
        if self.current_code_key is not None and not self.current_code_key:
            raise SomaError(
                "MATCH_INPUT_INVALID",
                "Customer review claim state is invalid.",
                "correct_input",
            )


@dataclass(frozen=True, slots=True)
class AccountCodeReviewContext:
    matching_profile_id: str
    customer_reference_generation: int
    normalized_code_key: str
    proposed_action: ProposedAction
    target: CustomerCodeState
    source: CustomerCodeState | None
    claimant_count: int

    def validate(self) -> None:
        if self.matching_profile_id != PROFILE_ID:
            raise SomaError(
                "MATCH_PROFILE_UNSUPPORTED",
                "Stored reference matching profile is unsupported by this build.",
                "none",
            )
        if (
            type(self.customer_reference_generation) is not int
            or self.customer_reference_generation < 0
            or type(self.claimant_count) is not int
            or self.claimant_count < 0
            or not self.normalized_code_key
        ):
            raise SomaError(
                "MATCH_INPUT_INVALID",
                "Customer Account Code review context is invalid.",
                "correct_input",
            )
        self.target.validate()
        if self.proposed_action == "CONFIRM_SHARED_CLAIM":
            if self.source is not None:
                raise SomaError(
                    "ACCOUNT_CODE_SHARED_CONTEXT_REQUIRED",
                    "Shared-claim review cannot include a reassignment source.",
                    "correct_input",
                )
        elif self.proposed_action == "REASSIGN_CLAIM":
            if self.source is None:
                raise SomaError(
                    "ACCOUNT_CODE_SHARED_CONTEXT_REQUIRED",
                    "Account Code reassignment requires a source Customer.",
                    "correct_input",
                )
            self.source.validate()
            if self.source.customer_org_id == self.target.customer_org_id:
                raise SomaError(
                    "ACCOUNT_CODE_SHARED_CONTEXT_REQUIRED",
                    "Account Code reassignment requires distinct Customers.",
                    "correct_input",
                )
            if self.source.current_code_key != self.normalized_code_key:
                raise SomaError(
                    "ACCOUNT_CODE_SOURCE_NOT_OWNER",
                    "The reviewed source Customer no longer owns the Account Code.",
                    "refresh",
                )
        else:
            raise SomaError(
                "MATCH_INPUT_INVALID",
                "Unsupported Customer Account Code review action.",
                "correct_input",
            )


def review_document(context: AccountCodeReviewContext) -> dict[str, object]:
    context.validate()
    source = (
        None
        if context.source is None
        else {
            "customer_org_id": context.source.customer_org_id,
            "revision": context.source.revision,
        }
    )
    return {
        "schema": "REVIEW_ACCOUNT_CODE_V1",
        "matching_profile_id": context.matching_profile_id,
        "customer_reference_generation": context.customer_reference_generation,
        "normalized_code_key": context.normalized_code_key,
        "proposed_action": context.proposed_action,
        "target": {
            "customer_org_id": context.target.customer_org_id,
            "revision": context.target.revision,
            "current_code_key": context.target.current_code_key,
        },
        "source": source,
        "claimant_count": context.claimant_count,
    }


def review_fingerprint(context: AccountCodeReviewContext) -> str:
    return sha256_canonical_json(review_document(context))


def require_fresh_review(
    context: AccountCodeReviewContext,
    expected_fingerprint: str,
) -> str:
    if (
        type(expected_fingerprint) is not str
        or len(expected_fingerprint) != 64
        or any(character not in string.hexdigits for character in expected_fingerprint)
    ):
        raise SomaError(
            "MATCH_INPUT_INVALID",
            "Customer Account Code review fingerprint is invalid.",
            "correct_input",
        )
    current = review_fingerprint(context)
    if not hmac.compare_digest(current, expected_fingerprint.lower()):
        raise SomaError(
            "REVIEW_CONTEXT_STALE",
            "Customer Account Code review context changed.",
            "refresh",
        )
    return current
