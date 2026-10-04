from __future__ import annotations

from typing import Protocol


class LocalAdminProfileParticipant(Protocol):
    def create_for_local_admin(
        self,
        uow,
        *,
        parent_command_id: str,
        actor_id: str,
        display_name: str = "Local Administrator",
    ) -> str: ...
