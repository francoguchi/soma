"""Exact protected DACL for caller-declared security-sensitive files/directories."""

import ctypes
import os
from ctypes import wintypes
from pathlib import Path

from soma.foundation.errors import ValidationError


def protect_owner(path: Path) -> None:
    if os.name != "nt":
        raise ValidationError("Windows owner protection is unavailable.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    security.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    security.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    security.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
    security.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
    ]
    security.SetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    token = wintypes.HANDLE()
    sid_text = wintypes.LPWSTR()
    descriptor = ctypes.c_void_p()
    if not security.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise ValidationError("Owner protection could not resolve the current principal.")
    try:
        length = wintypes.DWORD()
        security.GetTokenInformation(token, 1, None, 0, ctypes.byref(length))
        if not length.value:
            raise ValidationError("Owner protection principal is unavailable.")
        buffer = ctypes.create_string_buffer(length.value)
        if not security.GetTokenInformation(token, 1, buffer, length, ctypes.byref(length)):
            raise ValidationError("Owner protection principal is unavailable.")
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        if not security.ConvertSidToStringSidW(sid, ctypes.byref(sid_text)):
            raise ValidationError("Owner protection principal is invalid.")
        # Protected DACL: current principal + SYSTEM, no inherited ACEs.
        dacl = f"D:P(A;OICI;FA;;;{sid_text.value})(A;OICI;FA;;;SY)"
        if not security.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            dacl, 1, ctypes.byref(descriptor), None
        ) or not security.SetFileSecurityW(str(path), 0x80000004, descriptor):
            raise ValidationError("Owner file protection failed.")
    finally:
        kernel.CloseHandle(token)
        if sid_text:
            kernel.LocalFree(ctypes.cast(sid_text, ctypes.c_void_p))
        if descriptor:
            kernel.LocalFree(descriptor)
