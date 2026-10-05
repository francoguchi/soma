"""Read-only communication identity boundary consumed through a caller snapshot."""

from dataclasses import dataclass
from typing import Protocol

from soma.modules.reference.domain.channels import ChannelUseValidation


@dataclass(frozen=True)
class ContactIdentity:
    contact_id: str
    revision: int


@dataclass(frozen=True)
class ContactCandidatePage:
    candidates: tuple[ContactIdentity, ...]
    continuation_after_id: str | None


class ContactCommunicationProvider(Protocol):
    def match_email_candidates(
        self, snapshot, raw_address, *, limit=50, after_contact_id=None
    ) -> ContactCandidatePage: ...
    def validate_contact(self, snapshot, contact_id, revision) -> str: ...
    def validate_channel_for_use(
        self, snapshot, contact_id, channel_or_auto, purpose, *, limit=50, after_channel_id=None
    ) -> ChannelUseValidation: ...
