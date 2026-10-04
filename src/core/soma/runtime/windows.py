"""Selected native process/ACL donor helpers, adapted to Foundation ownership."""

import ctypes as C
import os
from ctypes import wintypes as W
from pathlib import Path
from dataclasses import dataclass
from soma.foundation.errors import SomaError


def SecurityNotReady(summary):
    return SomaError("RUNTIME_TRUST_FAILED", summary, "restart")


def api(dll, name, result, arguments):
    if os.name != "nt":
        raise SecurityNotReady("Windows security provider requires Windows")
    function = getattr(C.WinDLL(dll, use_last_error=True), name)
    function.restype = result
    function.argtypes = arguments
    return function


def checked(result):
    if not result:
        raise SecurityNotReady("Windows security operation failed")
    return result


def local_free(pointer):
    if pointer:
        api("kernel32", "LocalFree", C.c_void_p, [C.c_void_p])(pointer)


def current_user_sid() -> str:
    token = W.HANDLE()
    process = api("kernel32", "GetCurrentProcess", W.HANDLE, [])()
    checked(
        api("advapi32", "OpenProcessToken", W.BOOL, [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)])(
            process, 8, C.byref(token)
        )
    )
    try:
        size = W.DWORD()
        query = api(
            "advapi32",
            "GetTokenInformation",
            W.BOOL,
            [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)],
        )
        query(token, 1, None, 0, C.byref(size))
        if not 0 < size.value <= 65536:
            raise SecurityNotReady("Windows token size is invalid")
        buffer = C.create_string_buffer(size.value)
        checked(query(token, 1, buffer, size, C.byref(size)))
        return sid_string(C.cast(buffer, C.POINTER(C.c_void_p))[0])
    finally:
        api("kernel32", "CloseHandle", W.BOOL, [W.HANDLE])(token)


def sid_string(pointer) -> str:
    result = W.LPWSTR()
    checked(
        api("advapi32", "ConvertSidToStringSidW", W.BOOL, [C.c_void_p, C.POINTER(W.LPWSTR)])(
            pointer, C.byref(result)
        )
    )
    try:
        return result.value
    finally:
        local_free(C.cast(result, C.c_void_p))


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    process_birth_id: str
    image: Path


def process_identity(pid: int) -> ProcessIdentity:
    if type(pid) is not int or not 0 < pid <= 0xFFFFFFFF:
        raise SecurityNotReady("process PID is invalid")
    handle = api("kernel32", "OpenProcess", W.HANDLE, [W.DWORD, W.BOOL, W.DWORD])(
        0x101000, False, pid
    )
    if not handle and C.get_last_error() == 87:
        raise SomaError("RUNTIME_PROCESS_STALE", "The prior host process has exited.", "restart")
    checked(handle)
    try:
        if api("kernel32", "WaitForSingleObject", W.DWORD, [W.HANDLE, W.DWORD])(handle, 0) != 258:
            raise SomaError("RUNTIME_PROCESS_STALE", "The prior host process has exited.", "restart")
        times = [W.FILETIME() for _ in range(4)]
        checked(
            api("kernel32", "GetProcessTimes", W.BOOL, [W.HANDLE, *[C.POINTER(W.FILETIME)] * 4])(
                handle, *[C.byref(item) for item in times]
            )
        )
        size = W.DWORD(32768)
        image = C.create_unicode_buffer(size.value)
        checked(
            api(
                "kernel32",
                "QueryFullProcessImageNameW",
                W.BOOL,
                [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)],
            )(handle, 0, image, C.byref(size))
        )
        birth = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        return ProcessIdentity(pid, str(birth), Path(image.value).resolve(strict=True))
    finally:
        api("kernel32", "CloseHandle", W.BOOL, [W.HANDLE])(handle)


class VerifiedProcessWait:
    """Retain an exact verified process handle before sending shutdown."""

    def __init__(self, identity):
        self.handle = api("kernel32", "OpenProcess", W.HANDLE, [W.DWORD, W.BOOL, W.DWORD])(
            0x101000, False, identity.pid
        )
        checked(self.handle)
        try:
            times = [W.FILETIME() for _ in range(4)]
            checked(
                api(
                    "kernel32", "GetProcessTimes", W.BOOL, [W.HANDLE, *[C.POINTER(W.FILETIME)] * 4]
                )(self.handle, *[C.byref(item) for item in times])
            )
            birth = str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
            size = W.DWORD(32768)
            image = C.create_unicode_buffer(size.value)
            checked(
                api(
                    "kernel32",
                    "QueryFullProcessImageNameW",
                    W.BOOL,
                    [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)],
                )(self.handle, 0, image, C.byref(size))
            )
            if (
                birth != identity.process_birth_id
                or Path(image.value).resolve(strict=True) != identity.image
            ):
                raise SecurityNotReady("shutdown process identity changed")
        except BaseException:
            self.close()
            raise

    def wait(self, seconds):
        result = api("kernel32", "WaitForSingleObject", W.DWORD, [W.HANDLE, W.DWORD])(
            self.handle, max(0, int(seconds * 1000))
        )
        if result not in {0, 258}:
            raise SecurityNotReady("shutdown process wait failed")
        return result == 0

    def close(self):
        if self.handle:
            api("kernel32", "CloseHandle", W.BOOL, [W.HANDLE])(self.handle)
            self.handle = None


def verify_owner(path):
    sid = current_user_sid()
    target = Path(path)
    from soma.foundation.filesystem import safe_path

    safe_path(Path(target.anchor), target.relative_to(target.anchor))
    owner, dacl, descriptor = C.c_void_p(), C.c_void_p(), C.c_void_p()
    result = api(
        "advapi32",
        "GetNamedSecurityInfoW",
        W.DWORD,
        [
            W.LPCWSTR,
            C.c_int,
            W.DWORD,
            C.POINTER(C.c_void_p),
            C.c_void_p,
            C.POINTER(C.c_void_p),
            C.c_void_p,
            C.POINTER(C.c_void_p),
        ],
    )(str(target), 1, 5, C.byref(owner), None, C.byref(dacl), None, C.byref(descriptor))
    if result:
        raise SecurityNotReady("security path ACL cannot be read")
    try:
        control, revision = W.WORD(), W.DWORD()
        checked(
            api(
                "advapi32",
                "GetSecurityDescriptorControl",
                W.BOOL,
                [C.c_void_p, C.POINTER(W.WORD), C.POINTER(W.DWORD)],
            )(descriptor, C.byref(control), C.byref(revision))
        )
        if sid_string(owner) != sid or not control.value & 0x1000 or not dacl.value:
            raise SecurityNotReady("security path owner/inheritance is unsafe")
        # ACL header is eight bytes, with WORD AceCount at offset four.
        count = C.c_ushort.from_address(dacl.value + 4).value
        if count != 2:
            raise SecurityNotReady("security path must grant only user and SYSTEM")
        principals = set()
        for index in range(count):
            ace = C.c_void_p()
            checked(
                api("advapi32", "GetAce", W.BOOL, [C.c_void_p, W.DWORD, C.POINTER(C.c_void_p)])(
                    dacl, index, C.byref(ace)
                )
            )
            kind = C.c_ubyte.from_address(ace.value).value
            flags = C.c_ubyte.from_address(ace.value + 1).value
            mask = C.c_uint32.from_address(ace.value + 4).value
            if kind != 0 or flags & ~3 or mask != 0x1F01FF:
                raise SecurityNotReady("security path ACE is unsafe")
            principals.add(sid_string(ace.value + 8))
        if principals != {sid, "S-1-5-18"}:
            raise SecurityNotReady("security path principals are unsafe")
    finally:
        local_free(descriptor)
