"""Check Codex catalog discovery; optional temporary registration is cleaned up."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--temporary-register", action="store_true")
parser.add_argument("--details", action="store_true")
args = parser.parse_args()
binary = shutil.which("codex")
if not binary:
    raise SystemExit("Codex CLI is not on PATH")
marketplace = "experiment-learning-community"
def call(*arguments):
    return subprocess.run([binary, "-C", str(ROOT), *arguments], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=40)

added = False
removed = False
try:
    if args.temporary_register:
        existing = call("plugin", "marketplace", "list")
        if existing.returncode:
            raise RuntimeError(existing.stderr)
        if marketplace not in existing.stdout:
            registration = call("plugin", "marketplace", "add", str(ROOT), "--json")
            if registration.returncode:
                raise RuntimeError(registration.stderr)
            added = True
    result = call("plugin", "list", "--available", "--json", "--marketplace", marketplace)
    if result.returncode:
        raise RuntimeError(result.stderr)
    value = json.loads(result.stdout)
    expected_version = json.loads((ROOT / "plugins" / "experiment-learning" / "plugin.json").read_text(encoding="utf-8"))["version"]
    records = value.get("available", []) + value.get("installed", [])
    matched = any(item.get("pluginId") == f"experiment-learning@{marketplace}" and item.get("version") == expected_version for item in records)
finally:
    if added:
        cleanup = call("plugin", "marketplace", "remove", marketplace)
        removed = cleanup.returncode == 0
        if not removed:
            raise RuntimeError("Temporary marketplace cleanup failed: " + cleanup.stderr)
print(json.dumps({"cli_catalog_visible": matched, "marketplace": marketplace,
                  "plugin": "experiment-learning", "temporary_registration_used": added,
                  "temporary_registration_removed": removed, "plugin_installed": False}, ensure_ascii=False))
if args.details:
    print(json.dumps(value, ensure_ascii=False, indent=2))
sys.exit(0 if matched else 1)
