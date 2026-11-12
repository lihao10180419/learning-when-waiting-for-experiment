"""Local Plugin Creator preflight; this does not perform Portal review."""
from pathlib import Path
import json
import re
import struct
from urllib.parse import urlsplit

URL_FIELDS = ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL")


def contained(plugin, reference):
    if not isinstance(reference, str) or not reference.startswith("./"):
        raise ValueError(f"Expected a contained relative path: {reference}")
    selected = (plugin / reference).resolve()
    if not selected.is_relative_to(plugin.resolve()) or not selected.is_file():
        raise ValueError(f"Missing or external plugin asset: {reference}")
    return selected


def image_info(path):
    data = path.read_bytes()
    if len(data) > 5 * 1024 * 1024 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"Invalid/oversized PNG: {path.name}")
    width, height = struct.unpack(">II", data[16:24])
    if width != height or not 48 <= width <= 4096:
        raise ValueError(f"Invalid icon dimensions: {path.name}")
    return {"width": width, "height": height, "bytes": len(data)}


def inspect_plugin(plugin):
    manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
    compat = json.loads((plugin / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError("Missing portable schema declaration")
    if not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", manifest["name"]) or len(manifest["name"]) > 64:
        raise ValueError("Invalid plugin identity")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", manifest["version"]):
        raise ValueError("Invalid semantic version")
    for key in ("name", "version", "description", "author"):
        if manifest[key] != compat[key]:
            raise ValueError(f"Portable/compatibility manifests differ: {key}")
    if manifest["license"] != "MIT" or not (plugin / "LICENSE").is_file():
        raise ValueError("Missing MIT license")
    if any(key in manifest for key in ("skills", "mcpServers", "interface")):
        raise ValueError("Legacy fields at portable manifest root")
    for item in (manifest, compat):
        extension = item.get("extensions", {}).get("com.openai", {})
        if item.get("apps") is not None or extension.get("apps") is not None:
            raise ValueError("Public upload cannot contain app bindings")
    if any(p.name in {".app.json", "hooks.json", ".mcp.json", "hooks"} for p in plugin.rglob("*")):
        raise ValueError("Unexpected app binding, hook or legacy MCP payload")
    ext = manifest["extensions"]["com.openai"]
    interface = ext["interface"]
    if interface != compat["interface"] or ext["publication"] != compat["extensions"]["com.openai"]["publication"]:
        raise ValueError("Compatibility presentation/publication metadata differs")
    if ext.get("review") != compat["extensions"]["com.openai"].get("review"):
        raise ValueError("Compatibility review metadata differs")
    if ext.get("requires_local_executor") is not True or compat.get("requires_local_executor") is not True:
        raise ValueError("Local execution declaration missing")
    for key, maximum in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000), ("developerName", 80)):
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise ValueError(f"Invalid listing text: {key}")
    # Current category is an exact title in Plugin Creator's supported list.
    if interface.get("category") != "Productivity":
        raise ValueError("Recheck a changed category against the official supported list")
    prompts = interface.get("defaultPrompt")
    prompts = [prompts] if isinstance(prompts, str) else prompts
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or any(not isinstance(p, str) or not p.strip() or len(p) > 128 for p in prompts):
        raise ValueError("Invalid default prompts")
    if not isinstance(interface.get("capabilities"), list) or any(not isinstance(v, str) or not v.strip() for v in interface["capabilities"]):
        raise ValueError("Invalid capabilities")
    icons = {key: image_info(contained(plugin, interface[key])) for key in ("logo", "composerIcon")}
    if icons["logo"]["width"] < 256:
        raise ValueError("Listing logo must be at least 256px")
    for key in URL_FIELDS:
        if key in interface:
            parsed = urlsplit(interface[key])
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or len(interface[key]) > 1024:
                raise ValueError(f"Invalid public URL: {key}")
    contained(plugin, ext["onboardingSkill"])
    skills = sorted((plugin / "skills").glob("*/SKILL.md"))
    if len(skills) != 2:
        raise ValueError("Expected both portable skills")
    for path in skills:
        text = path.read_text(encoding="utf-8")
        match = re.match(r"---\s*\nname: ([a-z0-9-]+)\ndescription: (.+)\n---", text)
        if not match or path.parent.name != match[1] or len(text.encode()) > 1024 * 1024:
            raise ValueError(f"Invalid skill frontmatter/name: {path.name}")
    review_prompts = ext.get("review", {}).get("prompts", [])
    if not isinstance(review_prompts, list) or len(review_prompts) > 20 or any(not isinstance(p, str) or not p.strip() or len(p) > 4000 for p in review_prompts):
        raise ValueError("Invalid reviewer prompts")
    gaps = [f"Verified public {key}" for key in URL_FIELDS if key not in interface]
    if "countries" not in ext.get("publication", {}):
        gaps.append("Owner's supported-country declaration")
    if "commerce" not in ext.get("review", {}):
        gaps.append("Owner's commerce declaration")
    return {"icons": icons, "skills": [p.parent.name for p in skills], "listing_gaps": gaps,
            "listing_lengths": {k: len(interface[k]) for k in ("displayName", "shortDescription", "longDescription", "developerName")}}
