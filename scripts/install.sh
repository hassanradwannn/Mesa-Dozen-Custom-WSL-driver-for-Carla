#!/usr/bin/env bash
# Installs only to a new isolated location; no global ICD or Windows driver changes.
set -euo pipefail
src=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
dest=${ASURT_DOZEN_PREFIX:-"$HOME/.local/opt/asurt-dozen-20261024"}
[[ "$dest" == "$HOME"/.local/opt/* && "$dest" != "$HOME"/.local/opt/ ]] || { echo "Unsafe install destination: $dest" >&2; exit 2; }
[[ ! -e "$dest" && ! -L "$dest" ]] || { echo "Destination already exists; refusing overwrite: $dest" >&2; exit 3; }
"$src/scripts/verify.sh" --files-only
parent=$(dirname "$dest")
mkdir -p "$parent"
tmp=$(mktemp -d "$parent/.asurt-dozen-stage.XXXXXXXX")
cleanup() { [[ -d "$tmp" ]] && rm -rf -- "$tmp"; }
trap cleanup EXIT
cp -a "$src/variants" "$src/patches" "$src/licenses" "$src/scripts" "$src/tools" "$src/README.md" "$src/manifest.json" "$src/SHA256SUMS" "$tmp/"
printf 'asurt-dozen-wsl-team-kit/20261024\n' > "$tmp/.asurt-dozen-kit"
chmod +x "$tmp/scripts/"*.sh
mv -- "$tmp" "$dest"
trap - EXIT
echo "Installed Dozen package: $dest"
echo "Verify: $dest/scripts/verify.sh"
