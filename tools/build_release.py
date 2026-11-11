"""Create a portable source ZIP from the same allowlist used for publishing."""
from pathlib import Path
import hashlib
import json
import zipfile
from validate_release import ROOT, public_files, validate

report = validate()
target = ROOT / "dist"
target.mkdir(exist_ok=True)
name = f"experiment-learning-v{report['version']}"
archive = target / (name + ".zip")
manifest = {}
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for path in public_files():
        relative = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        manifest[relative] = hashlib.sha256(data).hexdigest()
        z.writestr(name + "/" + relative, data)
with zipfile.ZipFile(archive) as z:
    if z.testzip() is not None or len(z.namelist()) != len(manifest):
        raise ValueError("Archive integrity check failed")
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(target / (archive.name + ".sha256")).write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
(target / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"archive": str(archive), "sha256": digest, "files": len(manifest), "validated": True}, ensure_ascii=False, indent=2))
