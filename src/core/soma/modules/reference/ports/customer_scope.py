from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CustomerScopeResolution:
    kind: str
    customer_org_id: str | None
    display_name: str | None
    lifecycle_state: str | None


class CustomerScopeProvider(Protocol):
    def resolve_scope(self, snapshot, input: dict) -> CustomerScopeResolution: ...
