"""Zero-model local watcher: start the monitor once per Codex desktop process session."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import time

# Startup shortcuts pass the selected profile explicitly; login does not inherit
# a setup shell's process-local environment.
profile_parser = argparse.ArgumentParser(add_help=False)
profile_parser.add_argument("--home")
profile_args, _ = profile_parser.parse_known_args()
if profile_args.home:
    os.environ["EXPERIMENT_LEARNING_HOME"] = str(Path(profile_args.home).expanduser().resolve())
import assistant as a
from settings import CONFIG_PATH, load_config

ROOT = Path(__file__).resolve().parent
STATE = a.RUNTIME / "autostart-state.json"
POLL_SECONDS = 5


def desktop_path(path):
    # Match the actual packaged Codex app, including after a package version update.
    # The separate ChatGPT app and codex.exe CLI do not match this path.
    return bool(re.search(r"\\windowsapps\\openai\.codex_[^\\]+\\app\\chatgpt\.exe$", path, re.I))


def desktop_session():
    """Enumerate process metadata with local Win32 APIs, never through a model."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)

    class Entry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]

    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    matching = {}
    try:
        entry = Entry()
        entry.dwSize = ctypes.sizeof(entry)
        found = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while found:
            if entry.szExeFile.casefold() == "chatgpt.exe":
                handle = kernel.OpenProcess(0x1000, False, entry.th32ProcessID)
                if handle:
                    try:
                        size = wintypes.DWORD(32768)
                        path = ctypes.create_unicode_buffer(size.value)
                        if kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)) and desktop_path(path.value):
                            matching[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
                    finally:
                        kernel.CloseHandle(handle)
            found = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    roots = []
    for pid, parent in matching.items():
        if parent not in matching:
            birth = a.process_birth(pid)
            if birth:
                roots.append(f"{pid}:{birth}")
    return sorted(roots)


def read_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_state(state):
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(STATE)


def status():
    state = read_state()
    pid, birth = state.get("watcher_pid"), state.get("watcher_birth")
    state["watcher_running"] = bool(pid and birth and a.process_birth(pid) == birth and time.time() - state.get("heartbeat", 0) < 20)
    config = load_config()
    state["enabled"] = config.get("auto_start_on_codex_open", False)
    return state


def disable():
    startup_buffer = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.shell32.SHGetFolderPathW(None, 7, None, 0, startup_buffer)
    if result:
        raise OSError("Cannot resolve current-user Startup folder")
    target = Path(startup_buffer.value) / "Codex Experiment Learning Plugin.lnk"
    receipt_path = a.RUNTIME / "autostart-install.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig")) if receipt_path.exists() else {}
    if target.exists():
        if Path(receipt.get("shortcut", "")).resolve() != target.resolve():
            raise ValueError("Startup shortcut identity does not match our installation receipt")
        expected = receipt.get("shortcut_sha256", "").casefold()
        if not expected or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError("Startup shortcut changed; will not remove an unverified entry")
    config_path = CONFIG_PATH
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config.update(auto_start_on_codex_open=False, autostart_watcher_on_windows_logon=False)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if target.exists():
        target.unlink()
    print("已关闭自动启动；监听器约 5 秒内退出，实验与监测器不被终止。")
    return 0


class SessionGate:
    """Remember a handled app instance, so manual Stop stays stopped in that instance."""
    def __init__(self, handled=None):
        self.handled = handled or []

    def should_start(self, session):
        if not session:
            self.handled = []
            return False
        if session == self.handled:
            return False
        self.handled = list(session)
        return True


def start_monitor():
    console_python = Path(sys.executable).with_name("python.exe")
    result = subprocess.run([str(console_python), "-X", "utf8", str(ROOT / "assistant.py"), "start"],
                            cwd=ROOT.parent, capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=12, creationflags=subprocess.CREATE_NO_WINDOW)
    with a.connect() as db:
        alive = a.monitor_running(db)
        pid = a.setting(db, "monitor_pid")
    return {"exit_code": result.returncode, "monitor_running": alive, "monitor_pid": pid,
            "output": (result.stdout + result.stderr).strip()[:1500]}


def serve():
    import msvcrt
    a.RUNTIME.mkdir(parents=True, exist_ok=True)
    with open(a.RUNTIME / "autostart.lock", "a+b") as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return 0
        state = read_state()
        gate = SessionGate(state.get("handled_session"))
        state.update(watcher_pid=os.getpid(), watcher_birth=a.process_birth(os.getpid()), started_at=time.time())
        try:
            while True:
                config = load_config()
                if not config.get("auto_start_on_codex_open", False):
                    break
                try:
                    session = desktop_session()
                    state.update(codex_present=bool(session), codex_session=session, heartbeat=time.time(), error=None)
                    if gate.should_start(session):
                        # Persist the gate before attempting startup: no repeated resurrection
                        # after Stop, even if this watcher itself later restarts.
                        state.update(handled_session=gate.handled, last_action="starting_monitor", last_action_at=time.time())
                        write_state(state)
                        result = start_monitor()
                        state.update(last_start=result, last_action="monitor_ready" if result["monitor_running"] else "monitor_start_failed", last_action_at=time.time())
                    state["handled_session"] = gate.handled
                except Exception as error:
                    state.update(error=f"{type(error).__name__}: {error}", heartbeat=time.time())
                write_state(state)
                time.sleep(POLL_SECONDS)
        finally:
            state.update(stopped_at=time.time(), heartbeat=0)
            write_state(state)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--home")
    p.add_argument("--status", action="store_true")
    p.add_argument("--probe", action="store_true")
    p.add_argument("--disable", action="store_true")
    args = p.parse_args()
    if args.status:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0
    if args.probe:
        print(json.dumps({"codex_session": desktop_session()}, ensure_ascii=False))
        return 0
    if args.disable:
        return disable()
    return serve()


if __name__ == "__main__":
    sys.exit(main())
