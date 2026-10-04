import pytest

from soma.foundation.errors import SomaError
from soma.modules.reference.domain.account_code import (
    AccountCodeReviewContext,
    CustomerCodeState,
    require_fresh_review,
    review_document,
    review_fingerprint,
)
from soma.modules.reference.domain.matching import PROFILE_ID

TARGET = "00000000-0000-4000-8000-000000000001"
SOURCE = "00000000-0000-4000-8000-000000000002"


def context(*, action="CONFIRM_SHARED_CLAIM", generation=7, claimant_count=2):
    key = "acc-123"
    return AccountCodeReviewContext(
        matching_profile_id=PROFILE_ID,
        customer_reference_generation=generation,
        normalized_code_key=key,
        proposed_action=action,
        target=CustomerCodeState(TARGET, 3, None),
        source=None
        if action == "CONFIRM_SHARED_CLAIM"
        else CustomerCodeState(SOURCE, 5, key),
        claimant_count=claimant_count,
    )


def test_review_document_preserves_beta_v1_fingerprint_shape_without_sql():
    value = review_document(context())
    assert value == {
        "schema": "REVIEW_ACCOUNT_CODE_V1",
        "matching_profile_id": "UNICODE_MATCH_V1",
        "customer_reference_generation": 7,
        "normalized_code_key": "acc-123",
        "proposed_action": "CONFIRM_SHARED_CLAIM",
        "target": {
            "customer_org_id": TARGET,
            "revision": 3,
            "current_code_key": None,
        },
        "source": None,
        "claimant_count": 2,
    }
    assert len(review_fingerprint(context())) == 64


def test_review_fingerprint_changes_when_authoritative_context_changes():
    original = review_fingerprint(context())
    assert review_fingerprint(context(generation=8)) != original
    assert review_fingerprint(context(claimant_count=3)) != original


def test_review_freshness_uses_exact_current_context():
    current = context(action="REASSIGN_CLAIM")
    fingerprint = review_fingerprint(current)
    assert require_fresh_review(current, fingerprint.upper()) == fingerprint

    with pytest.raises(SomaError) as caught:
        require_fresh_review(context(action="REASSIGN_CLAIM", generation=8), fingerprint)
    assert caught.value.code == "REVIEW_CONTEXT_STALE"


def test_reassignment_requires_source_to_still_own_reviewed_code():
    bad = AccountCodeReviewContext(
        matching_profile_id=PROFILE_ID,
        customer_reference_generation=1,
        normalized_code_key="acc-123",
        proposed_action="REASSIGN_CLAIM",
        target=CustomerCodeState(TARGET, 1, None),
        source=CustomerCodeState(SOURCE, 1, "other-code"),
        claimant_count=1,
    )
    with pytest.raises(SomaError) as caught:
        review_fingerprint(bad)
    assert caught.value.code == "ACCOUNT_CODE_SOURCE_NOT_OWNER"
