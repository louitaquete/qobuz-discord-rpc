"""Funcoes especificas do Windows: janelas, instancia unica e inicio automatico."""

import ctypes
import sys
from ctypes import wintypes
from functools import lru_cache
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "QobuzRPC"
MUTEX_NAME = "QobuzRPC_SingleInstance"  # o instalador (AppMutex) usa o mesmo nome
EXE_NAME = "qobuz.exe"

_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_ERROR_ALREADY_EXISTS = 183


@lru_cache(maxsize=1)
def _libs():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
    user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)

    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.QueryFullProcessImageNameW.argtypes = (
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
    )
    kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    return user32, kernel32


def _exe_name(hwnd):
    user32, kernel32 = _libs()
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buf))
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value.rsplit("\\", 1)[-1].lower()
        return ""
    finally:
        kernel32.CloseHandle(handle)


def qobuz_titles():
    """Titulos das janelas visiveis do Qobuz.exe."""
    user32, _ = _libs()
    titles = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length and _exe_name(hwnd) == EXE_NAME:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                titles.append(buf.value)
        return True

    user32.EnumWindows(callback, 0)
    return titles


def acquire_single_instance():
    """Retorna um handle (guarde-o vivo) ou None se ja existe outra instancia."""
    _, kernel32 = _libs()
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.get_last_error() == _ERROR_ALREADY_EXISTS:
        return None
    return handle


def message_box(text, title="Qobuz Rich Presence"):
    ctypes.windll.user32.MessageBoxW(None, text, title, 0x40)  # MB_ICONINFORMATION


# ---- inicio com o Windows ----------------------------------------------------

def _autostart_command():
    if getattr(sys, "frozen", False):               # versao instalada (.exe)
        return f'"{sys.executable}"'
    pyw = Path(sys.executable).with_name("pythonw.exe")   # rodando do codigo-fonte
    exe = pyw if pyw.exists() else Path(sys.executable)
    run_py = Path(__file__).resolve().parent.parent / "run.py"
    return f'"{exe}" "{run_py}"'


def is_autostart():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, RUN_VALUE)
            return True
    except OSError:
        return False


def set_autostart(enabled):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, _autostart_command())
        else:
            try:
                winreg.DeleteValue(key, RUN_VALUE)
            except FileNotFoundError:
                pass
