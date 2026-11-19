#!/usr/bin/env bash
set -euo pipefail
dest=${ASURT_DOZEN_PREFIX:-"$HOME/.local/opt/asurt-dozen-20261024"}
[[ "$dest" == "$HOME"/.local/opt/asurt-dozen-20261024 || "$dest" == "$HOME"/.local/opt/asurt-dozen-20261024-* ]] || { echo 'Refusing unexpected destination' >&2; exit 2; }
[[ -d "$dest" && ! -L "$dest" && -f "$dest/.asurt-dozen-kit" ]] || { echo 'Not an ASURT Dozen installation' >&2; exit 3; }
[[ $(cat "$dest/.asurt-dozen-kit") == asurt-dozen-wsl-team-kit/20261024 ]] || { echo 'Unexpected installation marker' >&2; exit 4; }
rm -rf -- "$dest"
echo "Uninstalled only: $dest"
