from dataclasses import dataclass
from typing import Any, Protocol

from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.modules.reference.domain.settings import SettingDefinition


@dataclass(frozen=True)
class SettingValue:
    setting_key: str
    semantic_owner: str
    contract_name: str
    contract_version: int
    value: Any
    revision: int | None
    source: str


class SettingProvider(Protocol):
    def get_definition(self, key: str) -> SettingDefinition: ...
    def definitions_for_owner(self, owner: str) -> tuple[SettingDefinition, ...]: ...
    def get(self, snapshot: ReadSnapshot, key: str) -> SettingValue: ...
    def write(
        self,
        *,
        command_id: str,
        setting_key: str,
        semantic_owner: str,
        contract_name: str,
        contract_version: int,
        base_revision: int | None,
        value: Any,
        actor_id: str | None = None,
    ) -> dict: ...

    def upgrade(
        self,
        *,
        command_id: str,
        setting_key: str,
        semantic_owner: str,
        contract_name: str,
        contract_version: int,
        origin_contract: str,
        origin_version: int,
        base_revision: int,
        actor_id: str | None = None,
    ) -> dict: ...
