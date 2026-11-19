"""Read-only capture of the preserved WSL Dozen artifacts into this team repository.

Run on Windows with Python 3. The source WSL filesystem is never modified.
"""
from pathlib import Path
import os
import hashlib
import difflib
import json
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
source_root = os.environ.get("ASURT_WSL_SOURCE_ROOT")
if not source_root:
    raise SystemExit("Set ASURT_WSL_SOURCE_ROOT to the original Ubuntu asurt directory before rebuilding the kit.")
wsl = Path(source_root).expanduser()
source = wsl / "source"
clean = source / "mesa-26.2.5"
working = source / "mesa-dzn-carla-fix-26.2.5"
candidate = source / "descriptor-reset-candidate-20261024"
names = ["dzn_cmd_buffer.c", "dzn_descriptor_set.c", "dzn_device.c",
         "dzn_image.c", "dzn_pipeline.c", "dzn_private.h"]
relative = Path("src/microsoft/vulkan")
variants = {
    "working": ("dzn-carla-fix", "33d4b222f9ea05bb18fcd10ac3cc757a3792b26919450eef3609427469674d14"),
    "descriptor-reset-candidate": ("descriptor-reset-candidate-20261024", "cce0e8ac41b33b179c58e1a315c94d153fe1a7f031e57d09585a7d20616ccf78"),
}


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(data)
    return hasher.hexdigest()


def diff(left, right):
    out = []
    for name in names:
        item = (relative / name).as_posix()
        a = (left / item).read_text(encoding="utf-8").splitlines(keepends=True)
        b = (right / item).read_text(encoding="utf-8").splitlines(keepends=True)
        out.extend(difflib.unified_diff(a, b, fromfile="a/" + item, tofile="b/" + item))
    return "".join(out)


def assemble():
    for d in (clean, working, candidate):
        assert d.is_dir(), "Missing preserved WSL source: " + str(d)
    (root / "patches").mkdir(exist_ok=True)
    p1 = root / "patches/0001-working-compatibility.patch"
    p2 = root / "patches/0002-descriptor-reset-candidate.patch"
    p1.write_text(diff(clean, working), encoding="utf-8", newline="\n")
    p2.write_text(diff(working, candidate), encoding="utf-8", newline="\n")
    assert p1.stat().st_size and p2.stat().st_size
    # An actual source patch must recreate both preserved trees byte-for-byte.
    with tempfile.TemporaryDirectory(prefix="asurt-dozen-source-check-") as scratch:
        temp = Path(scratch)
        for name in names:
            item = relative / name
            (temp / item).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(clean / item, temp / item)
        for patch, expected in ((p1, working), (p2, candidate)):
            subprocess.run(["git", "apply", "--check", str(patch)], cwd=temp, check=True)
            subprocess.run(["git", "apply", str(patch)], cwd=temp, check=True)
            for name in names:
                item = relative / name
                got = (temp / item).read_bytes()
                want = (expected / item).read_bytes()
                # Git for Windows can materialize CRLF even outside a repository.
                # Compare exact source content after canonical LF normalization.
                got = got.replace(b"\r\n", b"\n")
                want = want.replace(b"\r\n", b"\n")
                if got != want:
                    index = next((i for i, (a, b) in enumerate(zip(got, want)) if a != b), min(len(got), len(want)))
                    raise RuntimeError(f"{item}: offset={index} actual={len(got)} expected={len(want)} got={got[index:index+24]!r} want={want[index:index+24]!r}")
            print("Patch reproduced source:", expected.name)
    recorded = {}
    for variant, (prefix, expected_hash) in variants.items():
        source_lib = wsl / "mesa-prefixes" / prefix / "lib/x86_64-linux-gnu"
        target = root / "variants" / variant
        libdir = target / "lib/x86_64-linux-gnu"
        icddir = target / "share/vulkan/icd.d"
        libdir.mkdir(parents=True, exist_ok=True)
        icddir.mkdir(parents=True, exist_ok=True)
        for name in ("libvulkan_dzn.so", "libspirv_to_dxil.so"):
            shutil.copy2(source_lib / name, libdir / name)
        actual = digest(libdir / "libvulkan_dzn.so")
        assert actual == expected_hash, f"Invalid {variant} binary: {actual}"
        (icddir / "dzn_icd.x86_64.json").write_text(json.dumps({
            "file_format_version": "1.0.1",
            "ICD": {"library_path": "../../../lib/x86_64-linux-gnu/libvulkan_dzn.so",
                    "library_arch": "64", "api_version": "1.1.354"},
        }, indent=2) + "\n", encoding="utf-8", newline="\n")
        recorded[variant] = {"sha256": actual, "source_prefix": prefix,
                             "spirv_to_dxil_sha256": digest(libdir / "libspirv_to_dxil.so")}
        print(variant, actual)
    shutil.copytree(clean / "licenses", root / "licenses", dirs_exist_ok=True)
    (root / "manifest.json").write_text(json.dumps({
        "mesa_base_commit_reported": "ddaf85e353442d9d7f192fdcf1823e652e3f2ee3",
        "mesa_version": "26.2.5",
        "target": "Ubuntu 22.04 x86_64 WSL2",
        "warning": "Reconstructed source differences; binary rebuild not CARLA-accepted by this packaging step.",
        "variants": recorded,
    }, indent=2) + "\n", encoding="utf-8")
    files = [f for d in ("variants", "patches", "licenses", "scripts", "tools")
             for f in (root / d).rglob("*") if f.is_file() and f.suffix != ".pyc"]
    files += [root / "README.md", root / "manifest.json"]
    lines = [digest(f) + "  " + f.relative_to(root).as_posix()
             for f in sorted(files, key=str)]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("Checksummed:", len(lines), "files")


if __name__ == "__main__":
    assemble()
