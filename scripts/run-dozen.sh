#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
variant=${ASURT_DOZEN_VARIANT:-descriptor-reset-candidate}
if [[ ${1:-} == --variant ]]; then
  [[ $# -ge 3 ]] || { echo 'Usage: run-dozen.sh [--variant working|descriptor-reset-candidate] COMMAND [ARGS...]' >&2; exit 2; }
  variant=$2
  shift 2
fi
case "$variant" in working|descriptor-reset-candidate) ;; *) echo "Unknown variant: $variant" >&2; exit 2 ;; esac
[[ $# -gt 0 ]] || { echo 'Usage: run-dozen.sh [--variant working|descriptor-reset-candidate] COMMAND [ARGS...]' >&2; exit 2; }
source /etc/os-release
[[ ${ID:-} == ubuntu && ${VERSION_ID:-} == 22.04 ]] || { echo 'Only tested on Ubuntu 22.04 x86_64 WSL2.' >&2; exit 3; }
[[ $(uname -m) == x86_64 && -c /dev/dxg && -r /usr/lib/wsl/lib/libd3d12.so ]] || { echo 'Missing WSL2 D3D12 GPU interface.' >&2; exit 3; }
prefix="$root/variants/$variant"
driverdir="$prefix/lib/x86_64-linux-gnu"
icd="$prefix/share/vulkan/icd.d/dzn_icd.x86_64.json"
[[ -r "$icd" && -r "$driverdir/libvulkan_dzn.so" ]] || { echo "Incomplete driver variant: $variant" >&2; exit 4; }
unset LIBGL_ALWAYS_SOFTWARE MESA_VK_DEVICE_SELECT MESA_VK_DEVICE_SELECT_FORCE_DEFAULT_DEVICE
export VK_DRIVER_FILES="$icd" VK_ICD_FILENAMES="$icd"
export LD_LIBRARY_PATH="$driverdir:/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# CARLA compatibility mode; intentionally opt-in, not a Vulkan conformance fix.
export CARLA_UNIFORM_SNAPSHOTS="${CARLA_UNIFORM_SNAPSHOTS:-1}"
export CARLA_STAGE_DESCRIPTORS="${CARLA_STAGE_DESCRIPTORS:-1}"
export CARLA_CACHED_UNIFORMS="${CARLA_CACHED_UNIFORMS:-1}"
export CARLA_POOL_UPLOADS="${CARLA_POOL_UPLOADS:-1}"
export CARLA_POOL_CPU_DESCRIPTOR_HEAPS="${CARLA_POOL_CPU_DESCRIPTOR_HEAPS:-1}"
export CARLA_UPLOAD_POOL_MAX_MB="${CARLA_UPLOAD_POOL_MAX_MB:-512}"
export DZN_SNAPSHOT_UNIFORMS="$CARLA_UNIFORM_SNAPSHOTS"
export DZN_STAGE_SNAPSHOT_DESCRIPTORS="$CARLA_STAGE_DESCRIPTORS"
export DZN_CACHED_UNIFORM_MEMORY="$CARLA_CACHED_UNIFORMS"
export DZN_POOL_UPLOADS="$CARLA_POOL_UPLOADS"
export DZN_POOL_CPU_DESCRIPTOR_HEAPS="$CARLA_POOL_CPU_DESCRIPTOR_HEAPS"
export DZN_UPLOAD_POOL_MAX_MB="$CARLA_UPLOAD_POOL_MAX_MB"
exec "$@"
