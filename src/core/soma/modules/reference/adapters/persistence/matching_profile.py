from __future__ import annotations

from soma.foundation.errors import SomaError
from soma.modules.reference.domain.matching import PROFILE_ID


def require_persisted_matching_profile(connection) -> None:
    row = connection.execute(
        "SELECT matching_profile_id FROM reference_metadata WHERE singleton_guard=1"
    ).fetchone()
    if row is None or str(row[0]) != PROFILE_ID:
        raise SomaError(
            "MATCH_PROFILE_UNSUPPORTED",
            "Stored reference matching profile is unsupported by this build.",
            "none",
        )
