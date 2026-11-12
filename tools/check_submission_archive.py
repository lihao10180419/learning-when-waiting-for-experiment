"""Reopen and inspect the actual ZIP, including hidden files and file hashes."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import tempfile
import zipfile
from validate_release import ROOT, EXCLUDE_PARTS, public_files
from submission_checks import inspect_plugin

PLUGIN = ROOT / "plugins" / "experiment-learning"


def inspect_archive(archive):
    with zipfile.ZipFile(archive) as source, tempfile.TemporaryDirectory(prefix="experiment-plugin-") as temp:
        if source.testzip() is not None:
            raise ValueError("Archive CRC check failed")
        names = source.namelist()
        if len(names) != len(set(names)) or "plugin.json" not in names:
            raise ValueError("Submission ZIP must have one plugin at its root")
        for info in source.infolist():
            p = PurePosixPath(info.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in info.filename or any(part in EXCLUDE_PARTS for part in p.parts):
                raise ValueError("Unsafe or unwanted archive member")
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError("Symlink in archive")
        expected = {p.relative_to(PLUGIN).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in public_files() if p.is_relative_to(PLUGIN)}
        actual = {name: hashlib.sha256(source.read(name)).hexdigest() for name in names}
        if actual != expected:
            raise ValueError("Submission archive inventory/content differs from validated plugin")
        source.extractall(temp)
        details = inspect_plugin(Path(temp))
    return {"archive_valid": True, "files": len(names),
            "sha256": hashlib.sha256(Path(archive).read_bytes()).hexdigest(), **details}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    print(json.dumps(inspect_archive(p.parse_args().archive), ensure_ascii=False, indent=2))
