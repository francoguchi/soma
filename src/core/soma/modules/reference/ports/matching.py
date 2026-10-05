from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CandidateResult:
    state: str
    explanation: str
    candidate_count: int
    candidate_ids: tuple[str, ...]
    continuation: str | None
    matching_profile_id: str
    normalized_keys: dict[str, str | None]
    scope: str


class MatchingProvider(Protocol):
    def match_customer_organization(self, snapshot, input: dict) -> CandidateResult: ...
    def match_contact(self, snapshot, input: dict) -> CandidateResult: ...
    def preview_customer_account_code_conflict(self, snapshot, input: dict) -> dict: ...
    def validate_customer_account_code_review(
        self, uow, input: dict, review_snapshot_hash: str
    ) -> dict: ...
