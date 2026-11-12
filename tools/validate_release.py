"""Validate release metadata and the explicit public-source allowlist."""
from pathlib import Path
import ast
import json
import re
import sys
from submission_checks import inspect_plugin, image_info

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"README.md", "README.zh-CN.md", "LICENSE", "CHANGELOG.md", ".gitignore", ".gitattributes"}
SOURCE_DIRS = {"plugins", "docs", "tests", "tools"}
EXCLUDE_PARTS = {".git", "__pycache__", "runtime", "dist", ".test-artifacts", ".venv"}


def public_files():
    result = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDE_PARTS for part in relative.parts):
            continue
        allowed = (str(relative).replace("\\", "/") == ".agents/plugins/marketplace.json"
                   or relative.parts[0] in SOURCE_DIRS or (len(relative.parts) == 1 and relative.name in ROOT_FILES))
        if allowed:
            if path.suffix in (".pyc", ".sqlite", ".sqlite3", ".log", ".zip") or path.name in ("config.json", "cards.json", ".env", "auth.json"):
                raise ValueError(f"Private/state file inside release sources: {relative}")
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError(f"External path not allowed: {relative}")
            result.append(path)
    return sorted(result, key=lambda p: p.relative_to(ROOT).as_posix())


def validate():
    plugin = ROOT / "plugins" / "experiment-learning"
    manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
    compat = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    for key in ("name", "version", "description"):
        if manifest[key] != compat[key]:
            raise ValueError(f"Portable/compatibility manifests differ: {key}")
    if manifest["license"] != "MIT" or not manifest["version"]:
        raise ValueError("Missing release version/license")
    marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    entry = marketplace["plugins"][0]
    selected = (ROOT / entry["source"]["path"]).resolve()
    if not entry["source"]["path"].startswith("./") or selected != plugin.resolve():
        raise ValueError("Marketplace path does not resolve to this plugin")
    for key in ("installation", "authentication"):
        if not entry["policy"].get(key):
            raise ValueError(f"Missing marketplace policy {key}")
    onboarding = manifest["extensions"]["com.openai"]["onboardingSkill"]
    if not onboarding.startswith("./") or not (plugin / onboarding).is_file():
        raise ValueError("Onboarding skill path does not exist")
    config = json.loads((plugin / "assets" / "config.example.json").read_text(encoding="utf-8"))
    if config["thread_id"] is not None or config["connection_verified"] or config["auto_start_on_codex_open"]:
        raise ValueError("Public defaults must be unbound, unverified and inactive")
    forbidden = [
        ("absolute user home", re.compile(r"[A-Z]:[\\/]+Users[\\/]+[^\\/\s'\"]+", re.I)),
        ("literal session UUID", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)),
        ("credential-like token", re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,})")),
    ]
    files = public_files()
    for path in files:
        if path.suffix == ".png":
            image_info(path)
            continue
        text = path.read_bytes().decode("utf-8")
        for reason, pattern in forbidden:
            if pattern.search(text):
                raise ValueError(f"{reason} found in {path.relative_to(ROOT)}")
        if path.suffix == ".py":
            ast.parse(text, filename=str(path))
        if path.suffix == ".json":
            json.loads(text)
        if path.name == "SKILL.md":
            match = re.match(r"---\s*\nname: ([a-z0-9-]+)\ndescription: (.+)\n---", text)
            if not match or len(match[1]) > 64 or path.parent.name != match[1]:
                raise ValueError(f"Invalid skill frontmatter/name: {path.relative_to(ROOT)}")
    return {"passed": True, "version": manifest["version"], "file_count": len(files),
            "marketplace": marketplace["name"], "plugin": manifest["name"], "private_state_included": False,
            "portal_review_performed": False, **inspect_plugin(plugin)}


if __name__ == "__main__":
    try:
        print(json.dumps(validate(), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, SyntaxError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
