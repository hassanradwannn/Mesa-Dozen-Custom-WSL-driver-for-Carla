"""Create a release tarball with Linux-safe file permissions.

Run with Windows or Linux Python 3; files come from the current package tree.
The Git repository and any local build logs are excluded.
"""
from pathlib import Path
import argparse
import hashlib
import tarfile

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=root.parent / "asurt-mesa-dozen-wsl-team-kit-20261024.tar.gz")
args = parser.parse_args()
target = args.output.resolve()
if root == target or root in target.parents:
    raise SystemExit("Choose a release archive path outside the Git repository.")
items = [
    "README.md", ".gitattributes", ".gitignore", "SHA256SUMS", "manifest.json",
    "variants", "patches", "licenses", "scripts", "tools",
]


def normalize(info):
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    info.mtime = 0
    info.mode = 0o755 if info.isdir() or info.name.startswith("scripts/") else 0o644
    return info


with tarfile.open(target, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
    for item in items:
        source = root / item
        if not source.exists():
            raise SystemExit("Missing release item: " + item)
        archive.add(source, arcname=item, filter=normalize)
hasher = hashlib.sha256()
with target.open("rb") as stream:
    for data in iter(lambda: stream.read(1024 * 1024), b""):
        hasher.update(data)
print("Archive:", target)
print("SHA256:", hasher.hexdigest())
print("Bytes:", target.stat().st_size)
