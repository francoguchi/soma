"""Fresh controller observations; only exact-run verification authorizes control."""

from dataclasses import dataclass, field

from soma.foundation.errors import SomaError
from soma.runtime.control import inspect_candidate, verify_candidate


@dataclass(frozen=True)
class Observation:
    state: str
    # Secret/control material is never included in diagnostic reprs.
    verified: tuple | None = field(default=None, repr=False)
    host_state: str | None = None


def observe(config, *, verify=True):
    """Inspection-only candidate mode cannot authorize Open, Stop, or reuse."""
    try:
        candidate = inspect_candidate(config)
        if candidate is None:
            return Observation("absent")
        if not verify:
            return Observation("candidate")
        verified, health = verify_candidate(config, candidate)
        state = "verified_ready" if health["host_state"] == "READY" else "verified_not_ready"
        return Observation(state, verified, health["host_state"])
    except SomaError as exc:
        state = {"RUNTIME_PROCESS_STALE": "stale", "RUNTIME_UNREACHABLE": "unreachable", "RUNTIME_CANDIDATE": "candidate"}.get(
            exc.code, "untrusted"
        )
        return Observation(state)
    except Exception:
        return Observation("untrusted")
