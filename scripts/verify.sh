#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$root"
sha256sum --check --status SHA256SUMS || { echo 'FAILED SHA256 verification' >&2; exit 6; }
echo 'File SHA-256 hashes: PASS'
for v in working descriptor-reset-candidate; do
  lib="$root/variants/$v/lib/x86_64-linux-gnu/libvulkan_dzn.so"
  [[ -s "$lib" ]] || exit 7
  if ldd "$lib" | grep -q 'not found'; then
    echo "Missing Linux dependencies for $v" >&2
    ldd "$lib" >&2
    exit 8
  fi
done
echo 'Linux dynamic dependencies: PASS'
if [[ ${1:-} == --files-only ]]; then exit 0; fi
if ! command -v vulkaninfo >/dev/null; then
  echo 'Optional Vulkan test requires: sudo apt install vulkan-tools'
  exit 0
fi
"$root/scripts/run-dozen.sh" vulkaninfo --summary
echo 'Look for driverName=Dozen and expected D3D12 GPU; this is not a CARLA RGB test.'
