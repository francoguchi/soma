import ctypes
import os
import platform
import struct
import uuid
from dataclasses import dataclass
from pathlib import Path

from soma.foundation.errors import ValidationError
from soma.foundation.filesystem import safe_path


def local_app_data() -> Path:
    """Windows KnownFolder lookup, independent of environment/CWD."""
    if (
        os.name != "nt"
        or struct.calcsize("P") != 8
        or platform.python_implementation() != "CPython"
    ):
        raise ValidationError("Windows x64 is required for source runtime discovery.")
    folder_id = ctypes.create_string_buffer(
        uuid.UUID("f1b32785-6fba-4fcf-9d55-7b8e7f157091").bytes_le
    )
    result = ctypes.c_wchar_p()
    shell = ctypes.WinDLL("shell32")
    shell.SHGetKnownFolderPath.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_wchar_p),
    ]
    shell.SHGetKnownFolderPath.restype = ctypes.c_long
    status = shell.SHGetKnownFolderPath(folder_id, 0, None, ctypes.byref(result))
    if status != 0:
        raise ValidationError("Local application data folder is unavailable.")
    try:
        return Path(result.value)
    finally:
        ole = ctypes.WinDLL("ole32")
        ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        ole.CoTaskMemFree(ctypes.cast(result, ctypes.c_void_p))


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    instance_root: Path
    checkout_root: Path
    mode: str = "development"

    def __post_init__(self) -> None:
        if self.mode not in ("development", "test"):
            raise ValidationError("Unsupported runtime configuration mode.")
        for root in (self.instance_root, self.checkout_root):
            if not root.is_absolute() or ".." in root.parts:
                raise ValidationError("Configuration roots must be absolute canonical paths.")
            safe_path(root, ".")
            if root.exists() and not root.is_dir():
                raise ValidationError("Configuration roots must be directories.")
        instance = self.instance_root.resolve()
        checkout = self.checkout_root.resolve()
        if instance.is_relative_to(checkout) or checkout.is_relative_to(instance):
            raise ValidationError("Instance storage and checkout roots must be separate.")
        object.__setattr__(self, "instance_root", instance)
        object.__setattr__(self, "checkout_root", checkout)
        for owner in ("data", "runtime", "diagnostics", "tmp", "backups"):
            self.path(owner)

    def path(self, owner: str, relative: str = ".") -> Path:
        if owner not in ("data", "runtime", "diagnostics", "tmp", "backups"):
            raise ValidationError("Unknown instance path owner.")
        return safe_path(safe_path(self.instance_root, owner), relative)

    @classmethod
    def discover(
        cls,
        checkout_root: Path,
        *,
        instance_override: Path | None = None,
        mode: str = "development",
    ) -> "RuntimeConfig":
        default = local_app_data() / "SOMA" / "Development" / "instance-v1"
        if instance_override is not None and mode != "test" and default.exists():
            if instance_override.resolve() != default.resolve():
                raise ValidationError("An existing canonical instance cannot be redirected.")
        return cls(
            instance_override if instance_override is not None else default, checkout_root, mode
        )
