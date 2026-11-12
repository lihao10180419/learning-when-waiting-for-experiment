"""Use a selected native CLI; diagnostics never send a model request."""
from pathlib import Path
import json
import os
import shutil
import subprocess


def resolve_cli(config):
    selected = config.get("codex_executable")
    if selected:
        path = Path(selected).expanduser()
        if not path.is_absolute() or not path.is_file():
            raise FileNotFoundError("Configured codex_executable must be an existing absolute executable path")
        if os.name == "nt" and path.suffix.casefold() != ".exe":
            raise ValueError("Select the native codex.exe, not a .cmd/.bat/PowerShell wrapper")
        return str(path.resolve())
    binary = shutil.which("codex")
    if binary and os.name == "nt" and Path(binary).suffix.casefold() != ".exe":
        raise ValueError("PATH selects a command wrapper; use set-cli --executable with the packaged native codex.exe")
    return binary or "codex"


def backend_status(binary):
    try:
        result = subprocess.run([binary, "app-server", "daemon", "version"], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=12)
        value = json.loads(result.stdout) if result.returncode == 0 else {}
        if not isinstance(value, dict):
            raise ValueError("Unexpected daemon version response")
        reachable = result.returncode == 0 and value.get("status") == "running"
        return {"reachable": reachable, "exit_code": result.returncode,
                "cli_version": value.get("cliVersion"), "app_server_version": value.get("appServerVersion"),
                "next": None if reachable else "Use a complete packaged CLI and explicitly start its local daemon, then verify a real probe."}
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return {"reachable": False, "error_type": type(error).__name__,
                "next": "Check the selected CLI and local daemon. No model request was sent."}
