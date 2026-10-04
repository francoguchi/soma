"""Cross-process canonical instance ownership used by bootstrap and later runtime."""

import msvcrt
import os

from soma.foundation.config import RuntimeConfig
from soma.foundation.errors import SomaError
from soma.foundation.filesystem import atomic_write, safe_path
from soma.foundation.filesystem.windows_acl import protect_owner
from soma.foundation.identity import new_uuid4, require_uuid4
from soma.foundation.strict_json import canonical_json_bytes, loads_strict_bytes


class InstanceLease:
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self._handle = None
        self.instance_id = None

    @property
    def held(self) -> bool:
        return self._handle is not None and not self._handle.closed

    def require(self) -> None:
        if not self.held:
            raise SomaError(
                "INSTANCE_OWNERSHIP_REQUIRED", "Canonical instance ownership is required."
            )
        safe_path(self.config.instance_root, ".")

    def __enter__(self):
        if self.held:
            raise SomaError("INSTANCE_OWNED", "The instance is already owned.")
        root = self.config.instance_root
        root.mkdir(parents=True, exist_ok=True)
        safe_path(root, ".")
        protect_owner(root)
        for owner in ("data", "runtime", "diagnostics", "tmp", "backups"):
            directory = self.config.path(owner)
            directory.mkdir(exist_ok=True)
            protect_owner(directory)
        lock = self.config.path("data", "soma.instance.lock")
        fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
        handle = os.fdopen(fd, "r+b", buffering=0)
        try:
            if lock.stat().st_size == 0:
                handle.write(b"\0")
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            self._handle = handle
            protect_owner(lock)
            identity_path = self.config.path("data", "instance.json")
            if not identity_path.exists():
                if self.config.path("data", "soma.db").exists():
                    raise SomaError(
                        "INSTANCE_IDENTITY_MISSING", "Existing database identity is unavailable."
                    )
                atomic_write(
                    root,
                    "data/instance.json",
                    canonical_json_bytes({"version": 1, "data_instance_id": new_uuid4()}),
                    protect=protect_owner,
                )
            identity = loads_strict_bytes(identity_path.read_bytes(), max_bytes=1024)
            if (
                type(identity) is not dict
                or set(identity) != {"version", "data_instance_id"}
                or type(identity["version"]) is not int
                or identity["version"] != 1
            ):
                raise SomaError(
                    "INSTANCE_IDENTITY_INVALID", "Canonical instance identity is invalid."
                )
            self.instance_id = require_uuid4(identity["data_instance_id"])
            return self
        except BaseException as exc:
            handle.close()
            self._handle = None
            if isinstance(exc, OSError):
                raise SomaError(
                    "INSTANCE_OWNED",
                    "The instance is unavailable or owned by another process.",
                    "retry",
                ) from None
            raise

    def __exit__(self, *args):
        if self._handle is not None:
            try:
                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            finally:
                self._handle.close()
                self._handle = None
