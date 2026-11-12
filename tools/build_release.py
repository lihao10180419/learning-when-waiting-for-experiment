"""Create a portable source ZIP from the same allowlist used for publishing."""
from pathlib import Path
import hashlib
import json
import zipfile
from validate_release import ROOT, public_files, validate
from check_submission_archive import inspect_archive

report = validate()
target = ROOT / "dist"
target.mkdir(exist_ok=True)
name = f"experiment-learning-v{report['version']}"
archive = target / (name + "-source.zip")
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

# This is the upload copy: one self-contained plugin at the archive root,
# without the source repository, marketplace, tests or developer tools.
plugin = ROOT / "plugins" / "experiment-learning"
submission = target / (name + "-submission.zip")
with zipfile.ZipFile(submission, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for path in public_files():
        if path.is_relative_to(plugin):
            entry = zipfile.ZipInfo(path.relative_to(plugin).as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            z.writestr(entry, path.read_bytes())
archive_report = inspect_archive(submission)
digest = archive_report["sha256"]
(target / (submission.name + ".sha256")).write_text(f"{digest}  {submission.name}\n", encoding="utf-8")
release_report = {"source": str(archive), "submission": str(submission), "checks": archive_report,
                  "readiness": "Structural checks do not verify public URLs, publisher identity or Portal approval. See docs/SUBMISSION.md."}
(target / "release-report.json").write_text(json.dumps(release_report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(release_report, ensure_ascii=False, indent=2))
