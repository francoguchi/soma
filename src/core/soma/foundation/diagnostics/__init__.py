"""Allowlisted, bounded diagnostics with no raw-message fallback."""

import re
import threading
from collections import deque

from soma.foundation.filesystem import OwnedArtifact, remove_owned
from soma.foundation.filesystem.windows_acl import protect_owner
from soma.foundation.identity import require_uuid4
from soma.foundation.strict_json import canonical_json_bytes
from soma.foundation.time import utc_epoch_seconds

MAX_BYTES = 10 * 1024 * 1024


class RunLog:
    def __init__(self, config, run_id, *, console=False):
        require_uuid4(run_id)
        self.path = config.path("diagnostics", f"run-{run_id}.jsonl")
        self.run_id, self.console = run_id, console
        self.errors = deque(maxlen=20)
        self.events = deque(maxlen=20)
        self.lock = threading.Lock()
        self.available = True
        try:
            self.path.touch(exist_ok=False)
            protect_owner(self.path)
            self.artifact = OwnedArtifact.capture(
                config.instance_root, self.path.relative_to(config.instance_root)
            )
            # Runtime-exclusive instance means no other runtime log is active.
            logs = sorted(
                (
                    p
                    for p in self.path.parent.glob("run-*.jsonl")
                    if re.fullmatch(r"run-[0-9a-f-]{36}\.jsonl", p.name) and p != self.path
                ),
                key=lambda p: p.stat().st_mtime_ns,
            )
            for path in logs[: max(0, len(logs) - 19)]:
                remove_owned(
                    config.instance_root,
                    OwnedArtifact.capture(
                        config.instance_root, path.relative_to(config.instance_root)
                    ),
                )
        except Exception:
            self.available = False
        self.emit("RUNTIME_BOOTSTRAPPING", state="BOOTSTRAPPING")

    def snapshot(self):
        with self.lock:
            return {"recent_codes": list(self.errors), "runtime_events": list(self.events)}

    def emit(self, code, *, state=None, kind="error"):
        if type(code) is not str or re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code) is None:
            return
        document = {"run_id": self.run_id, "recorded_at_utc_s": utc_epoch_seconds(), "code": code}
        if state in {
            "BOOTSTRAPPING",
            "MIGRATING",
            "BINDING",
            "SERVING_NOT_READY",
            "READY",
            "QUIESCING",
            "EXITING",
            "FAILED",
        }:
            document["state"] = state
        normal = kind == "event" or (state is not None and state != "FAILED")
        document["kind"] = "event" if normal else "warning" if kind == "warning" else "error"
        line = canonical_json_bytes(document) + b"\n"
        with self.lock:
            if normal:
                self.events.append({key: document[key] for key in ("recorded_at_utc_s", "code")})
            else:
                self.errors.append(code)
            if self.console or not self.available:
                print(line.decode().rstrip(), flush=True)
            if self.available:
                try:
                    # Recheck retained inode; diagnostic write never touches replacements.
                    current = self.path.stat()
                    if (current.st_dev, current.st_ino) != (
                        self.artifact.device,
                        self.artifact.inode,
                    ):
                        raise ValueError()
                    if current.st_size + len(line) <= MAX_BYTES:
                        with self.path.open("ab") as handle:
                            handle.write(line)
                except Exception:
                    self.available = False
