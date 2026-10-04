"""Native notification icon with an invisible message window and trusted controls."""

import ctypes as C
from ctypes import wintypes as W
import os
import threading
import webbrowser

from soma.runtime.control import stop_current, verify_current
from soma.runtime.windows import api

WNDPROC = C.WINFUNCTYPE(C.c_ssize_t, W.HWND, W.UINT, W.WPARAM, W.LPARAM)


class WndClass(C.Structure):
    _fields_ = [
        ("style", W.UINT),
        ("proc", WNDPROC),
        ("cls_extra", C.c_int),
        ("wnd_extra", C.c_int),
        ("instance", W.HINSTANCE),
        ("icon", W.HICON),
        ("cursor", W.HANDLE),
        ("background", W.HBRUSH),
        ("menu", W.LPCWSTR),
        ("name", W.LPCWSTR),
    ]


class Guid(C.Structure):
    _fields_ = [("data", C.c_byte * 16)]


class NotifyData(C.Structure):
    _fields_ = [
        ("size", W.DWORD),
        ("window", W.HWND),
        ("id", W.UINT),
        ("flags", W.UINT),
        ("callback", W.UINT),
        ("icon", W.HICON),
        ("tip", W.WCHAR * 128),
        ("state", W.DWORD),
        ("state_mask", W.DWORD),
        ("info", W.WCHAR * 256),
        ("version", W.UINT),
        ("title", W.WCHAR * 64),
        ("info_flags", W.DWORD),
        ("guid", Guid),
        ("balloon", W.HICON),
    ]


class Tray:
    def __init__(self, host):
        self.host = host
        self.window = None
        self.data = None
        self.thread = None
        self.ready = threading.Event()
        self.registered = False
        self.state = host.state

    def start(self):
        self.thread = threading.Thread(target=self._loop, name="soma-tray", daemon=True)
        self.thread.start()
        self.ready.wait(2)

    def update(self, state):
        self.state = state
        if self.window:
            api("user32", "PostMessageW", W.BOOL, [W.HWND, W.UINT, W.WPARAM, W.LPARAM])(
                self.window, 0x8002, 0, 0
            )

    def _tip(self):
        return "SOMA - " + {"READY": "Ready", "QUIESCING": "Stopping", "EXITING": "Stopping", "FAILED": "Failed"}.get(
            self.state, "Starting"
        )

    def _notify(self, operation):
        return api("shell32", "Shell_NotifyIconW", W.BOOL, [W.DWORD, C.POINTER(NotifyData)])(
            operation, C.byref(self.data)
        )

    def _loop(self):
        atom = icon = instance = None
        try:
            instance = api("kernel32", "GetModuleHandleW", W.HINSTANCE, [W.LPCWSTR])(None)
            self.proc = WNDPROC(self._message)
            self.class_name = "SOMA-Tray-" + self.host.run_id
            definition = WndClass(
                0, self.proc, 0, 0, instance, None, None, None, None, self.class_name
            )
            atom = api("user32", "RegisterClassW", W.WORD, [C.POINTER(WndClass)])(
                C.byref(definition)
            )
            if not atom:
                raise ValueError()
            self.window = api(
                "user32",
                "CreateWindowExW",
                W.HWND,
                [
                    W.DWORD,
                    W.LPCWSTR,
                    W.LPCWSTR,
                    W.DWORD,
                    C.c_int,
                    C.c_int,
                    C.c_int,
                    C.c_int,
                    W.HWND,
                    W.HMENU,
                    W.HINSTANCE,
                    C.c_void_p,
                ],
            )(0, self.class_name, "SOMA", 0, 0, 0, 0, 0, None, None, instance, None)
            if not self.window:
                raise ValueError()
            icon = api(
                "user32",
                "LoadImageW",
                W.HANDLE,
                [W.HINSTANCE, W.LPCWSTR, W.UINT, C.c_int, C.c_int, W.UINT],
            )(
                None,
                str(self.host.config.checkout_root / "src/main/assets/brand/soma-tray.ico"),
                1,
                32,
                32,
                0x10,
            )
            if not icon:
                raise ValueError()
            self.data = NotifyData()
            self.data.size, self.data.window, self.data.id = C.sizeof(NotifyData), self.window, 1
            self.data.flags, self.data.callback, self.data.icon, self.data.tip = (
                7,
                0x8001,
                icon,
                self._tip(),
            )
            if not self._notify(0):
                raise ValueError()
            self.registered = True
            self.host.log.emit("TRAY_READY", kind="event")
            self.ready.set()
            msg = W.MSG()
            while (
                api("user32", "GetMessageW", C.c_int, [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT])(
                    C.byref(msg), None, 0, 0
                )
                > 0
            ):
                api("user32", "TranslateMessage", W.BOOL, [C.POINTER(W.MSG)])(C.byref(msg))
                api("user32", "DispatchMessageW", C.c_ssize_t, [C.POINTER(W.MSG)])(C.byref(msg))
        except BaseException:
            self.host.log.emit("TRAY_UNAVAILABLE")
            self.ready.set()
        finally:
            if self.registered:
                self._notify(2)
            self.registered = False
            if icon:
                api("user32", "DestroyIcon", W.BOOL, [W.HICON])(icon)
            if atom:
                api("user32", "UnregisterClassW", W.BOOL, [W.LPCWSTR, W.HINSTANCE])(
                    self.class_name, instance
                )
            self.window = None

    def _message(self, window, message, wparam, lparam):
        try:
            if message == 0x8001 and lparam in (0x205, 0x7B):
                self._menu(window)
                return 0
            if message == 0x8001 and lparam == 0x203:
                self._action(2)
                return 0
            if message == 0x8002 and self.data:
                self.data.tip = self._tip()
                self._notify(1)
                return 0
            if message == 0x10:
                api("user32", "DestroyWindow", W.BOOL, [W.HWND])(window)
                return 0
            if message == 2:
                api("user32", "PostQuitMessage", None, [C.c_int])(0)
                return 0
        except Exception:
            self.host.log.emit("TRAY_ACTION_FAILED")
            return 0
        return api("user32", "DefWindowProcW", C.c_ssize_t, [W.HWND, W.UINT, W.WPARAM, W.LPARAM])(
            window, message, wparam, lparam
        )

    def _menu(self, window):
        menu = api("user32", "CreatePopupMenu", W.HMENU, [])()
        try:
            append = api("user32", "AppendMenuW", W.BOOL, [W.HMENU, W.UINT, C.c_size_t, W.LPCWSTR])
            append(menu, 3, 1, self._tip())
            for identity, text in (
                (2, "Open SOMA"),
                (3, "Open Current Log"),
                (4, "Open Logs Folder"),
            ):
                append(menu, 0, identity, text)
            append(menu, 0x800, 0, None)
            append(menu, 0, 5, "Stop SOMA")
            point = W.POINT()
            api("user32", "GetCursorPos", W.BOOL, [C.POINTER(W.POINT)])(C.byref(point))
            api("user32", "SetForegroundWindow", W.BOOL, [W.HWND])(window)
            command = api(
                "user32",
                "TrackPopupMenu",
                W.UINT,
                [W.HMENU, W.UINT, C.c_int, C.c_int, C.c_int, W.HWND, C.c_void_p],
            )(menu, 0x100 | 2, point.x, point.y, 0, window, None)
            if command:
                self._action(command)
        finally:
            api("user32", "DestroyMenu", W.BOOL, [W.HMENU])(menu)

    def _action(self, command):
        def run():
            try:
                verified = verify_current(self.host.config)
                if verified is None or verified[0]["run_id"] != self.host.run_id:
                    raise ValueError()
                if command == 2:
                    webbrowser.open(verified[0]["origin"])
                elif command == 3:
                    os.startfile(self.host.log.path)
                elif command == 4:
                    os.startfile(self.host.config.path("diagnostics"))
                elif command == 5:
                    if not stop_current(self.host.config):
                        raise ValueError()
            except Exception:
                self.host.log.emit("TRAY_ACTION_FAILED")

        threading.Thread(target=run, name="soma-tray-action", daemon=True).start()

    def close(self):
        if self.window:
            api("user32", "PostMessageW", W.BOOL, [W.HWND, W.UINT, W.WPARAM, W.LPARAM])(
                self.window, 0x10, 0, 0
            )
        if self.thread:
            self.thread.join(1)
