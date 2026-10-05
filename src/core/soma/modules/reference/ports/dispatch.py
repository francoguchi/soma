from dataclasses import dataclass
from typing import Protocol

from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.transactions import UnitOfWork


@dataclass(frozen=True)
class DispatchCommandContext:
    actor_id: str | None = None


@dataclass(frozen=True)
class SiteDispatchLink:
    site_id: str


class SiteDispatchParticipant(Protocol):
    def create_dedicated_for_site(
        self,
        uow: UnitOfWork,
        *,
        parent_command_id: str,
        name: str,
        precomputed_name_match_key: str,
        command_context: DispatchCommandContext,
    ) -> str: ...


class SiteAddressProvider(Protocol):
    def site_link_for(
        self, snapshot: ReadSnapshot, dispatch_location_id: str
    ) -> SiteDispatchLink | None: ...
    def current_site_address(self, snapshot: ReadSnapshot, site_id: str) -> str: ...
