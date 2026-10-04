"""CurrentUser DPAPI framing adapted from Beta, bound to purpose and instance."""

import ctypes as C
import hashlib
import os
import struct
import uuid
from ctypes import wintypes as W

from soma.foundation.errors import SomaError
from soma.foundation.identity import require_uuid4

MAGIC = b"SOMA-DPAPI-V1\0"
PURPOSES = {"live_data_dek", "run_control"}
MAX_BLOB = 65536


def security_failure() -> SomaError:
    return SomaError(
        "SECURITY_NOT_READY", "Protected installation material is unavailable.", "restart"
    )


class Blob(C.Structure):
    _fields_ = [("size", W.DWORD), ("data", C.POINTER(C.c_ubyte))]


def _blob(value):
    buffer = (C.c_ubyte * len(value)).from_buffer_copy(value)
    return buffer, Blob(len(value), buffer)


class WindowsDpapiProvider:
    def _binding(self, purpose: str, instance_id: str) -> bytes:
        require_uuid4(instance_id)
        if purpose not in PURPOSES or os.name != "nt":
            raise security_failure()
        return hashlib.sha256(f"SOMA-DPAPI-V1\0{purpose}\0{instance_id}".encode()).digest()

    def _crypt(self, value, purpose, instance_id, *, protect):
        entropy = self._binding(purpose, instance_id)
        input_buffer, input_blob = _blob(value)
        entropy_buffer, entropy_blob = _blob(entropy)
        output = Blob()
        crypt = C.WinDLL("crypt32", use_last_error=True)
        kernel = C.WinDLL("kernel32", use_last_error=True)
        kernel.LocalFree.argtypes = [C.c_void_p]
        kernel.LocalFree.restype = C.c_void_p
        function = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
        function.argtypes = [
            C.POINTER(Blob),
            W.LPCWSTR if protect else C.c_void_p,
            C.POINTER(Blob),
            C.c_void_p,
            C.c_void_p,
            W.DWORD,
            C.POINTER(Blob),
        ]
        function.restype = W.BOOL
        try:
            if not function(
                C.byref(input_blob),
                f"SOMA {purpose}" if protect else None,
                C.byref(entropy_blob),
                None,
                None,
                1,
                C.byref(output),
            ):
                raise security_failure()
            if not 0 < output.size <= MAX_BLOB:
                raise security_failure()
            return C.string_at(output.data, output.size)
        finally:
            C.memset(input_buffer, 0, len(input_buffer))
            C.memset(entropy_buffer, 0, len(entropy_buffer))
            if output.data:
                C.memset(output.data, 0, output.size)
                kernel.LocalFree(output.data)

    def protect_current_user(self, secret: bytes, purpose: str, instance_id: str) -> bytes:
        self._binding(purpose, instance_id)
        if type(secret) is not bytes or len(secret) != 32:
            raise security_failure()
        encrypted = self._crypt(secret, purpose, instance_id, protect=True)
        purpose_bytes = purpose.encode("ascii")
        return (
            MAGIC
            + bytes([len(purpose_bytes)])
            + purpose_bytes
            + uuid.UUID(instance_id).bytes
            + struct.pack(">I", len(encrypted))
            + encrypted
        )

    def unprotect_current_user(self, blob: bytes, purpose: str, instance_id: str) -> bytes:
        self._binding(purpose, instance_id)
        try:
            if (
                type(blob) is not bytes
                or not len(MAGIC) + 22 <= len(blob) <= MAX_BLOB + 128
                or not blob.startswith(MAGIC)
            ):
                raise ValueError
            offset = len(MAGIC)
            size = blob[offset]
            offset += 1
            bound_purpose = blob[offset : offset + size].decode("ascii")
            offset += size
            bound_id = str(uuid.UUID(bytes=blob[offset : offset + 16]))
            offset += 16
            length = struct.unpack(">I", blob[offset : offset + 4])[0]
            offset += 4
            if (
                bound_purpose != purpose
                or bound_id != instance_id
                or not 0 < length <= MAX_BLOB
                or len(blob) != offset + length
            ):
                raise ValueError
        except (ValueError, UnicodeError, struct.error, IndexError):
            raise security_failure() from None
        secret = self._crypt(blob[offset:], purpose, instance_id, protect=False)
        if len(secret) != 32:
            raise security_failure()
        return secret
