#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows tray utility: toggle Always on Top for any foreground window.

Run with:
    python always_on_top.py

Hotkey:
    Ctrl+Space toggles the current foreground window.
    Ctrl+Alt+Q exits this utility.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path


user32 = ctypes.WinDLL("user32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# Some Python builds do not expose these pointer-sized Win32 aliases in
# ctypes.wintypes, so define the few we need here.
LRESULT = ctypes.c_ssize_t
UINT_PTR = ctypes.c_size_t
HCURSOR = wintypes.HANDLE


APP_NAME = "窗口置顶工具"
CLASS_NAME = "AlwaysOnTopTrayWindow"
MUTEX_NAME = "Local\\ZhidAlwaysOnTopWindowUtility"
HOTKEY_TOGGLE_ID = 1
HOTKEY_EXIT_ID = 2
TRAY_ID = 1
TIMER_ID = 1
TIMER_MS = 250
WM_TRAYICON = 0x8000 + 1

IDM_TOGGLE = 1001
IDM_STARTUP = 1002
IDM_EXIT = 1003

MOD_CONTROL = 0x0002
MOD_ALT = 0x0001
VK_SPACE = 0x20
VK_Q = 0x51

WM_DESTROY = 0x0002
WM_COMMAND = 0x0111
WM_TIMER = 0x0113
WM_HOTKEY = 0x0312
WM_CONTEXTMENU = 0x007B
WM_USER = 0x0400
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
NIN_SELECT = WM_USER
NIN_KEYSELECT = WM_USER + 1

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIM_SETVERSION = 0x00000004

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010

NOTIFYICON_VERSION_4 = 4
NIIF_INFO = 0x00000001
NIIF_WARNING = 0x00000002

IDI_APPLICATION = 32512
ERROR_ALREADY_EXISTS = 183
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040

MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800
MF_CHECKED = 0x00000008
MF_UNCHECKED = 0x00000000

TPM_LEFTALIGN = 0x0000
TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010

GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008


HWND_TOPMOST = wintypes.HWND(-1)
HWND_NOTOPMOST = wintypes.HWND(-2)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HICON),
    ]


WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND
user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.DefWindowProcW.restype = LRESULT
user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.RegisterHotKey.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
    wintypes.UINT,
    wintypes.UINT,
]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.SetTimer.argtypes = [wintypes.HWND, UINT_PTR, wintypes.UINT, wintypes.LPVOID]
user32.KillTimer.argtypes = [wintypes.HWND, UINT_PTR]
user32.GetForegroundWindow.restype = wintypes.HWND
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsWindow.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL
user32.LoadIconW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR]
user32.LoadIconW.restype = wintypes.HICON
user32.LoadImageW.argtypes = [
    wintypes.HINSTANCE,
    wintypes.LPCWSTR,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.LoadImageW.restype = wintypes.HANDLE
user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
user32.CreatePopupMenu.restype = wintypes.HMENU
user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, UINT_PTR, wintypes.LPCWSTR]
user32.TrackPopupMenu.argtypes = [
    wintypes.HMENU,
    wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.LPVOID,
]
user32.TrackPopupMenu.restype = wintypes.BOOL
user32.DestroyMenu.argtypes = [wintypes.HMENU]
user32.DestroyIcon.argtypes = [wintypes.HICON]
user32.DestroyIcon.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]

if ctypes.sizeof(ctypes.c_void_p) == 8:
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_longlong
    get_window_long_ptr = user32.GetWindowLongPtrW
else:
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long
    get_window_long_ptr = user32.GetWindowLongW

shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL
shell32.ExtractIconExW.argtypes = [
    wintypes.LPCWSTR,
    ctypes.c_int,
    ctypes.POINTER(wintypes.HICON),
    ctypes.POINTER(wintypes.HICON),
    wintypes.UINT,
]
shell32.ExtractIconExW.restype = wintypes.UINT

kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def check(result, message: str) -> None:
    if not result:
        error = ctypes.get_last_error()
        raise ctypes.WinError(error, message)


def truncate(text: str, limit: int) -> str:
    return text if len(text) < limit else text[: limit - 1]


def loword(value: int) -> int:
    return value & 0xFFFF


class AlwaysOnTopApp:
    def __init__(self, mutex: wintypes.HANDLE) -> None:
        self.mutex = mutex
        self.hinstance = kernel32.GetModuleHandleW(None)
        self.hwnd = wintypes.HWND()
        self.hicon, self.owns_icon = self._load_app_icon()
        self.wndproc = WNDPROC(self._wndproc)
        self.last_target = wintypes.HWND()
        self.toggle_hotkey_registered = False
        self.exit_hotkey_registered = False

    def run(self) -> int:
        self._create_window()
        self._add_tray_icon()
        self._register_hotkey()
        user32.SetTimer(self.hwnd, TIMER_ID, TIMER_MS, None)
        self._message_loop()
        return 0

    def _create_window(self) -> None:
        wc = WNDCLASSW()
        wc.lpfnWndProc = self.wndproc
        wc.hInstance = self.hinstance
        wc.lpszClassName = CLASS_NAME

        if not user32.RegisterClassW(ctypes.byref(wc)):
            error = ctypes.get_last_error()
            # ERROR_CLASS_ALREADY_EXISTS is harmless during rapid restarts.
            if error != 1410:
                raise ctypes.WinError(error, "RegisterClassW failed")

        self.hwnd = user32.CreateWindowExW(
            0,
            CLASS_NAME,
            APP_NAME,
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            self.hinstance,
            None,
        )
        check(self.hwnd, "CreateWindowExW failed")

    def _load_app_icon(self) -> tuple[wintypes.HICON, bool]:
        if getattr(sys, "frozen", False):
            large_icon = wintypes.HICON()
            small_icon = wintypes.HICON()
            count = shell32.ExtractIconExW(
                sys.executable, 0, ctypes.byref(large_icon), ctypes.byref(small_icon), 1
            )
            if count and small_icon:
                if large_icon:
                    user32.DestroyIcon(large_icon)
                return small_icon, True
            if large_icon:
                return large_icon, True

        icon_file = Path(__file__).resolve().parent / "assets" / "app-icon.ico"
        if icon_file.exists():
            icon = user32.LoadImageW(
                None,
                str(icon_file),
                IMAGE_ICON,
                16,
                16,
                LR_LOADFROMFILE | LR_DEFAULTSIZE,
            )
            if icon:
                return wintypes.HICON(icon), True

        return user32.LoadIconW(None, wintypes.LPCWSTR(IDI_APPLICATION)), False

    def _notify_data(self, flags: int = 0) -> NOTIFYICONDATAW:
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        data.hWnd = self.hwnd
        data.uID = TRAY_ID
        data.uFlags = flags
        data.uCallbackMessage = WM_TRAYICON
        data.hIcon = self.hicon
        data.szTip = truncate(f"{APP_NAME} - Ctrl+Space 置顶 / Ctrl+Alt+Q 退出", 127)
        return data

    def _add_tray_icon(self) -> None:
        data = self._notify_data(NIF_MESSAGE | NIF_ICON | NIF_TIP)
        check(shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(data)), "添加托盘图标失败")
        data.uTimeoutOrVersion = NOTIFYICON_VERSION_4
        shell32.Shell_NotifyIconW(NIM_SETVERSION, ctypes.byref(data))

    def _remove_tray_icon(self) -> None:
        data = self._notify_data()
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(data))

    def _show_balloon(self, title: str, text: str, warning: bool = False) -> None:
        data = self._notify_data(NIF_INFO)
        data.szInfoTitle = truncate(title, 63)
        data.szInfo = truncate(text, 255)
        data.dwInfoFlags = NIIF_WARNING if warning else NIIF_INFO
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(data))

    def _register_hotkey(self) -> None:
        self.toggle_hotkey_registered = bool(
            user32.RegisterHotKey(self.hwnd, HOTKEY_TOGGLE_ID, MOD_CONTROL, VK_SPACE)
        )
        self.exit_hotkey_registered = bool(
            user32.RegisterHotKey(self.hwnd, HOTKEY_EXIT_ID, MOD_CONTROL | MOD_ALT, VK_Q)
        )

        if self.toggle_hotkey_registered and self.exit_hotkey_registered:
            self._show_balloon(APP_NAME, "已启动：Ctrl+Space 置顶，Ctrl+Alt+Q 退出。")
        else:
            failed = []
            if not self.toggle_hotkey_registered:
                failed.append("Ctrl+Space")
            if not self.exit_hotkey_registered:
                failed.append("Ctrl+Alt+Q")
            self._show_balloon(
                APP_NAME,
                f"{'、'.join(failed)} 已被其他程序占用。请使用托盘菜单操作或关闭占用程序后重启。",
                warning=True,
            )

    def _message_loop(self) -> None:
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _wndproc(
        self,
        hwnd: wintypes.HWND,
        msg: int,
        wparam: wintypes.WPARAM,
        lparam: wintypes.LPARAM,
    ) -> int:
        if msg == WM_HOTKEY:
            hotkey_id = int(wparam)
            if hotkey_id == HOTKEY_TOGGLE_ID:
                self.toggle_foreground_window()
            elif hotkey_id == HOTKEY_EXIT_ID:
                user32.DestroyWindow(self.hwnd)
            return 0
        if msg == WM_TIMER:
            self._remember_foreground_window()
            return 0
        if msg == WM_TRAYICON:
            tray_msg = int(lparam)
            event = loword(tray_msg)
            if tray_msg in (WM_RBUTTONUP, WM_LBUTTONUP, WM_CONTEXTMENU, NIN_SELECT, NIN_KEYSELECT) or event in (
                WM_RBUTTONUP,
                WM_LBUTTONUP,
                WM_CONTEXTMENU,
                NIN_SELECT,
                NIN_KEYSELECT,
            ):
                self._show_menu()
            return 0
        if msg == WM_COMMAND:
            self._handle_command(int(wparam) & 0xFFFF)
            return 0
        if msg == WM_DESTROY:
            self._cleanup()
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _cleanup(self) -> None:
        user32.KillTimer(self.hwnd, TIMER_ID)
        if self.toggle_hotkey_registered:
            user32.UnregisterHotKey(self.hwnd, HOTKEY_TOGGLE_ID)
        if self.exit_hotkey_registered:
            user32.UnregisterHotKey(self.hwnd, HOTKEY_EXIT_ID)
        self._remove_tray_icon()
        if self.owns_icon:
            user32.DestroyIcon(self.hicon)
            self.owns_icon = False
        if self.mutex:
            kernel32.CloseHandle(self.mutex)
            self.mutex = None

    def _show_menu(self) -> None:
        self._remember_foreground_window()
        menu = user32.CreatePopupMenu()
        if not menu:
            return
        startup_state = MF_CHECKED if self._startup_enabled() else MF_UNCHECKED
        user32.AppendMenuW(menu, MF_STRING, IDM_TOGGLE, "置顶/取消当前窗口")
        user32.AppendMenuW(menu, MF_STRING | startup_state, IDM_STARTUP, "开机启动")
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, IDM_EXIT, "退出")

        point = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point))
        user32.SetForegroundWindow(self.hwnd)
        command = user32.TrackPopupMenu(
            menu,
            TPM_LEFTALIGN | TPM_RIGHTBUTTON | TPM_RETURNCMD,
            point.x,
            point.y,
            0,
            self.hwnd,
            None,
        )
        user32.DestroyMenu(menu)
        if command:
            self._handle_command(int(command))

    def _handle_command(self, command_id: int) -> None:
        if command_id == IDM_TOGGLE:
            self.toggle_remembered_window()
        elif command_id == IDM_STARTUP:
            self._toggle_startup()
        elif command_id == IDM_EXIT:
            user32.DestroyWindow(self.hwnd)

    def _remember_foreground_window(self) -> None:
        hwnd = user32.GetForegroundWindow()
        if self._is_valid_target(hwnd):
            self.last_target = hwnd

    def toggle_foreground_window(self) -> None:
        hwnd = user32.GetForegroundWindow()
        if not self._is_valid_target(hwnd):
            hwnd = self.last_target
        self._toggle_window(hwnd)

    def toggle_remembered_window(self) -> None:
        hwnd = self.last_target
        if not self._is_valid_target(hwnd):
            hwnd = user32.GetForegroundWindow()
        self._toggle_window(hwnd)

    def _toggle_window(self, hwnd: wintypes.HWND) -> None:
        if not self._is_valid_target(hwnd):
            self._show_balloon(APP_NAME, "没有可置顶窗口。", warning=True)
            return

        is_topmost = self._is_topmost(hwnd)
        insert_after = HWND_NOTOPMOST if is_topmost else HWND_TOPMOST
        ok = user32.SetWindowPos(
            hwnd,
            insert_after,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )
        title = self._window_title(hwnd) or "当前窗口"
        if ok:
            action = "已取消置顶" if is_topmost else "已置顶"
            self._show_balloon(APP_NAME, f"{action}：{title}")
            self.last_target = hwnd
        else:
            self._show_balloon(APP_NAME, f"操作失败：{title}", warning=True)

    def _is_topmost(self, hwnd: wintypes.HWND) -> bool:
        exstyle = get_window_long_ptr(hwnd, GWL_EXSTYLE)
        return bool(exstyle & WS_EX_TOPMOST)

    def _is_valid_target(self, hwnd: wintypes.HWND) -> bool:
        if not hwnd or hwnd == self.hwnd:
            return False
        if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            return False
        if not self._window_title(hwnd).strip():
            return False
        class_name = self._class_name(hwnd)
        return class_name not in {
            CLASS_NAME,
            "Shell_TrayWnd",
            "Shell_SecondaryTrayWnd",
            "Progman",
            "WorkerW",
        }

    @staticmethod
    def _window_title(hwnd: wintypes.HWND) -> str:
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value

    @staticmethod
    def _class_name(hwnd: wintypes.HWND) -> str:
        buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buffer, len(buffer))
        return buffer.value

    def _startup_link(self) -> Path:
        startup = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup / f"{APP_NAME}.lnk"

    def _startup_enabled(self) -> bool:
        return self._startup_link().exists()

    def _toggle_startup(self) -> None:
        link = self._startup_link()
        try:
            if link.exists():
                link.unlink()
                self._show_balloon(APP_NAME, "已关闭开机启动。")
            else:
                self._create_startup_shortcut(link)
                self._show_balloon(APP_NAME, "已开启开机启动。")
        except OSError as exc:
            self._show_balloon(APP_NAME, f"开机启动设置失败：{exc}", warning=True)

    def _create_startup_shortcut(self, link: Path) -> None:
        if getattr(sys, "frozen", False):
            target = Path(sys.executable).resolve()
            arguments = ""
            work_dir = target.parent
        else:
            script = Path(__file__).resolve()
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            target = pythonw if pythonw.exists() else Path(sys.executable)
            arguments = f'"{script}"'
            work_dir = script.parent
        link.parent.mkdir(parents=True, exist_ok=True)

        ps_command = (
            "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:LINK_PATH);"
            "$s.TargetPath=$env:TARGET_PATH;"
            "$s.Arguments=$env:SCRIPT_PATH;"
            "$s.WorkingDirectory=$env:WORK_DIR;"
            "$s.IconLocation=$env:ICON_PATH;"
            "$s.Save()"
        )
        env = os.environ.copy()
        env.update(
            {
                "LINK_PATH": str(link),
                "TARGET_PATH": str(target),
                "SCRIPT_PATH": arguments,
                "WORK_DIR": str(work_dir),
                "ICON_PATH": f"{target},0",
            }
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
            check=True,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )


def main() -> int:
    if os.name != "nt":
        print("This tool only supports Windows.", file=sys.stderr)
        return 1
    ctypes.set_last_error(0)
    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not mutex:
        raise ctypes.WinError(ctypes.get_last_error(), "CreateMutexW failed")
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(mutex)
        return 0
    app = AlwaysOnTopApp(mutex)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
