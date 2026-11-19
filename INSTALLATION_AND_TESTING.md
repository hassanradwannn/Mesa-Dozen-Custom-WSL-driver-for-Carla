# Mesa Dozen Custom WSL Driver for CARLA — Installation & Test Walkthrough

**Audience:** a human teammate performing the setup, or a coding agent executing and recording it on an authorized machine.

**Target:** Windows with WSL2, **Ubuntu 22.04 x86-64 inside WSL**, a WSL-capable Windows GPU driver, and the custom Mesa Dozen (dzn) 26.2.5 binaries in this repository. Dozen translates Linux Vulkan commands to Direct3D 12; the Windows GPU driver ultimately executes them.

**Scope:** This kit installs the **Linux Vulkan userspace driver only**. It does **not** install CARLA, Unreal Engine, the ASURT Silverstone map, the ASURT car, ROS, Python client wheels, WSL itself, or a Windows graphics driver. Installing it is **not equivalent to proving CARLA renders correctly**. The historical ASURT acceptance in October 2026 was on a specific machine with a matching custom CARLA build.

**Do not** install the Mesa .so files into Windows, replace Ubuntu system Mesa, replace files in /usr/lib/wsl/lib, install a Linux NVIDIA kernel driver into WSL, turn off Windows TDR protection, or globally set a Vulkan ICD. All driver selection below is scoped to individual processes.

## 0. Quick navigation and decision points

| Phase | Where | Required? | What passing means |
| --- | --- | --- | --- |
| A. Windows / WSL GPU prerequisites | Windows PowerShell, then Ubuntu | Yes | WSL2 sees /dev/dxg and the Windows-provided D3D12 library |
| B. Download, checksums, and install | Ubuntu 22.04 | Yes | Files are intact, ELF dependencies resolve, isolated prefix exists |
| C. Actual Vulkan driver detection | Ubuntu 22.04 | Yes | vulkaninfo selects **Dozen** on **Microsoft Direct3D12 (your GPU)** |
| D. Real CARLA rendered sensor and vehicle test | Ubuntu with a compatible CARLA runtime | Only if CARLA is available | A **real, changing, nonblack RGB sensor stream** and normal simulation |
| E. ASURT / Silverstone / ROS test | Ubuntu with the separate ASURT package | Only if ASURT is available | Matched Silverstone map, hero vehicle, controls, RGB, and bridge |
| F. Cleanup and handoff | Ubuntu / report | Yes | No unexpected processes/settings changed, evidence recorded |

**Stop at the last successful phase.** If Phase C passes but CARLA is absent or fails, report *driver detection PASS / CARLA rendering NOT TESTED or FAIL* — never upgrade that to full CARLA success.

## A. Windows prerequisites (run in Windows PowerShell, not Bash)

1. Ensure the hardware has a GPU and Windows is using the GPU manufacturer's driver with WSL graphics support. Windows owns this driver; the Linux kit is separate.
2. Inspect WSL and your installed distributions:

   ```powershell
   wsl --version
   wsl --list --verbose
   ```

3. Ubuntu-22.04 must appear as WSL **version 2**. If WSL needs an update, run ```wsl --update``` in PowerShell (admin permissions or restart may be requested). If Ubuntu 22.04 is not installed, it must be provisioned separately; do not overwrite an existing distribution.
4. Start the target distribution:

   ```powershell
   wsl -d Ubuntu-22.04
   ```

**Pass:** You enter a Linux shell in the intended Ubuntu-22.04 distribution. **Fail:** WSL missing, WSL 1, missing distro, no compatible Windows GPU driver, or unresolved WSL GPU passthrough. Resolve this before touching the kit.

## B. Ubuntu preflight, packages, and installation

All commands in this section run **inside the Ubuntu WSL terminal**. Do not paste them into Windows PowerShell.

### B1. Check Linux version, architecture, and GPU interface

```bash
cat /etc/os-release | grep -E '^(NAME|VERSION_ID)='
uname -m
ls -l /dev/dxg
ls -l /usr/lib/wsl/lib/libd3d12.so
ls -l /usr/lib/wsl/lib/libdxcore.so
```

**Pass:** Ubuntu 22.04, x86_64, a /dev/dxg character device, and readable libd3d12.so and libdxcore.so. If these are missing, return to the Windows GPU/WSL configuration; copying these libraries from another PC is not the fix.

### B2. Install Linux user-space dependencies

The following matches the prerequisites documented in the package README; it installs **Ubuntu user-space libraries**, not a Linux graphics kernel driver:

```bash
sudo apt update
sudo apt install -y vulkan-tools libdrm2 libxcb1 libx11-xcb1 \
  libxcb-dri3-0 libxcb-present0 libxcb-xfixes0 libxcb-sync1 \
  libxcb-randr0 libxcb-shm0 libxshmfence1 libexpat1 zlib1g libzstd1
```

If apt reports a package or dependency error, record the exact message and fix it using the Ubuntu 22.04 repositories. Do not downgrade the entire system or add unrelated graphics-driver PPAs.

### B3. Obtain the package — choose **one** method

**Method 1 — Git clone (recommended for the newest README and this guide):**

```bash
cd ~
git clone https://github.com/hassanradwannn/Mesa-Dozen-Custom-WSL-driver-for-Carla.git
cd ~/Mesa-Dozen-Custom-WSL-driver-for-Carla
git log -1 --format='%h %s'
```

If the repository directory already exists, **do not blindly clone over it or run git reset --hard**. Inspect it and decide whether it is safe to update.

**Method 2 — pinned GitHub release v0.1.0 (for a separately downloaded archive):**

```bash
mkdir -p ~/asurt-dozen-kit
cd ~/asurt-dozen-kit
# Copy the downloaded v0.1.0 .tar.gz into this folder first.
echo 'f729e89f8e069b4e717a3b38d5ce89311789a38b81e450d4b6014e08b3204200  asurt-mesa-dozen-wsl-team-kit-20261024.tar.gz' \
  | sha256sum --check \
  && tar -xzf asurt-mesa-dozen-wsl-team-kit-20261024.tar.gz
```

**Expected SHA-256 for that exact v0.1.0 release asset:**

```text
f729e89f8e069b4e717a3b38d5ce89311789a38b81e450d4b6014e08b3204200
```

Extraction above is conditional on a matching SHA-256; if verification fails, it will not run. **Stop on any mismatch**, and never execute contents from an unverified archive. The release archive may predate this guide; use the documentation on the current main branch. Use only an archive obtained from the official repository release.

### B4. Verify the checked-out package, then install

From the kit directory (the clone or the extracted archive):

```bash
bash scripts/verify.sh --files-only
bash scripts/install.sh
```

**Expected positive messages:**

```text
File SHA-256 hashes: PASS
Linux dynamic dependencies: PASS
Installed Dozen package: /home/<your-linux-user>/.local/opt/asurt-dozen-20261024
```

The default install prefix is **$HOME/.local/opt/asurt-dozen-20261024**. The installer refuses to overwrite an existing target. Never delete an existing installation automatically: inspect it and use the kit's uninstall procedure only when authorized.

**Important:** ```scripts/verify.sh --files-only``` verifies the *package's own SHA256SUMS and ELF dependencies*. It does **not** start Vulkan, CARLA, Unreal, ROS or a sensor.

## C. Vulkan GPU detection — mandatory acceptance gate

In the same Ubuntu terminal, run:

```bash
KIT="$HOME/.local/opt/asurt-dozen-20261024"
"$KIT/scripts/run-dozen.sh" vulkaninfo --summary
```

Check the actual output; a zero exit code alone is not sufficient. Expected example from the original NVIDIA machine:

```text
deviceName = Microsoft Direct3D12 (NVIDIA GeForce RTX 3060)
driverName = Dozen
driverInfo = Mesa 26.2.5
```

A teammate's GPU model may differ. A warning that Dozen is **not a conformant Vulkan implementation** is known for this driver; do not confuse it with proof of CARLA failure or conformance. A headless Vulkan enumeration warning is distinct from rendering a scene.

To check the optional earlier variant:

```bash
"$KIT/scripts/run-dozen.sh" --variant working vulkaninfo --summary
```

**Pass C:** Vulkan selects the intended **Dozen** ICD and the expected Windows Direct3D12 GPU, with no missing shared libraries. **Fail C:** device absent, llvmpipe/lavapipe or another driver selected, Vulkan loader error, undefined symbol, missing library, or process crash.

### Which binary is being tested?

| Variant | Selection | SHA-256 of libvulkan_dzn.so |
| --- | --- | --- |
| descriptor-reset-candidate (default) | no --variant argument | cce0e8ac41b33b179c58e1a315c94d153fe1a7f031e57d09585a7d20616ccf78 |
| working (earlier compatible build) | --variant working | 33d4b222f9ea05bb18fcd10ac3cc757a3792b26919450eef3609427469674d14 |

Check the manifest and file hash when diagnosing version discrepancies:

```bash
cat "$KIT/manifest.json"
sha256sum "$KIT/variants/descriptor-reset-candidate/lib/x86_64-linux-gnu/libvulkan_dzn.so"
```

Do not accidentally select the older unrelated /opt/carla-vulkan-26.2.5 baseline; it passed GPU detection but previously failed full UE4 rendering.

## D. Rendered CARLA test (only when CARLA is installed separately)

This kit **does not include a runnable CARLA server**. A valid rendering test needs a separately installed, compatible Linux CARLA binary, its matching Python client, and a loaded map. Do not claim a test was run merely because the above Vulkan enumeration succeeded.

**Before starting a simulator:**

```bash
pgrep -af 'CarlaUE4|UE4Editor' || true
ss -ltn | grep -E ':(2000|2100) ' || true
echo "DISPLAY=$DISPLAY"
```

These are **passive checks**; do not use a bare TCP connect/close as a readiness probe. Do not terminate another user's server, spawn a second server on an occupied port, or change existing launch scripts as part of driver installation.

Use an existing, documented **owner-managed CARLA launcher** that explicitly sets this kit's ICD, the correct CARLA server/client version, Vulkan and display settings. This repository cannot provide a universal CARLA launch command because CARLA versions and packaged executables differ.

**Rendered-camera acceptance procedure:** use a safe test town/track and a single RGB camera already provided by the test harness, or deliberately create and clean up a test RGB sensor through the matched CARLA Python API. Confirm the world has rendering enabled, inspect multiple **consecutive** changing camera frames and an actual scene/window, and record:

1. Correct CARLA client/server version and actual map name (not simply the requested map).
2. Real RGB image dimensions, successful callback/frame IDs, and nonzero, nonuniform colour.
3. Distinct frame hashes or visible changes after an authorized spectator/camera move; a single screenshot is inadequate.
4. No VK_ERROR_DEVICE_LOST, GPU device removal, fatal native exception, or black/constant images.
5. Clean process shutdown and released port.

**Pass D** requires a real rendered stream and normal simulation. A window border, open RPC port, or successful vulkaninfo alone does not satisfy it. Do not use historical 25–28 FPS as a mandatory threshold for new hardware.

## E. Full ASURT Silverstone validation (optional; original ASURT runtime required)

Use this path **only if** the team member also has the matching custom ASURT Linux CARLA simulator, its compatible Python client, Silverstone content, hero vehicle, WSLg display, ROS2 Humble bridge and the original supervisor.

### E1. Verify the separately installed ASURT prerequisites

```bash
ASURT="$HOME/asurt"
test -f "$ASURT/scripts/carla-gpu-profile-20261024/launch_asurt_sim.py"
test -f "$ASURT/simulators/asurt-custom-20261023/CarlaUE4.sh"
test -x "$ASURT/.venvs/asurt-custom-client/bin/python"
```

If any test returns nonzero, **stop with "ASURT integration unavailable — prerequisite missing"**. Do not fabricate paths, download unauthorized private assets, or replace the matched client with a stock CARLA wheel.

### E2. Start ASURT using its supervisor, in WSLg

Before launching, confirm there is no competing CARLA server or owner-held ASURT session. Then in **Ubuntu**:

```bash
export CARLA_DRIVER_PREFIX="$HOME/.local/opt/asurt-dozen-20261024/variants/descriptor-reset-candidate"
export CARLA_SHADER_CACHE_DIR="$HOME/.cache/asurt-dozen-descriptor-reset"
export CARLA_UNIFORM_SNAPSHOTS=1
export CARLA_STAGE_DESCRIPTORS=1
export CARLA_CACHED_UNIFORMS=1
export CARLA_POOL_UPLOADS=1
export CARLA_POOL_CPU_DESCRIPTOR_HEAPS=1
export CARLA_UPLOAD_POOL_MAX_MB=512
export CARLA_CACHE_IMAGE_DESCRIPTORS=1
python3 "$HOME/asurt/scripts/carla-gpu-profile-20261024/launch_asurt_sim.py" \
  wslg --threading parallel --rhi-width 4
```

This uses the original supervisor's guarded startup, temporary Unreal configuration and cleanup. It is **not** a universal command for someone who only downloaded the driver kit. For the original VNC supervisor, use the VNC environment and set CARLA_CACHE_IMAGE_DESCRIPTORS=0; do not invent a VNC server or DISPLAY configuration.

### E3. ASURT checks while the supervised session is running

1. The actual world is **Silverstone**, the expected ASURT hero blueprint is available/spawned, and physics/ticks run.
2. Rendering remains enabled after map load: CARLA's no_rendering_mode must be **False**.
3. The actual driving GUI shows coloured road, sky, track structures and a moving/nonuniform RGB camera stream. Compare several frames or movement viewpoints, not one still.
4. If authorized for safe in-simulator manual driving, use **B** for manual control; **W** throttle, **S** brake, **A/D** steer and **Tab** camera. Observe car movement, speed/brake response, and camera changes without compromising the scenario.
5. If the ROS2 bridge is installed, observe its expected node/topics and telemetry; do not send uncontrolled /drive commands during another person's run.
6. Record simulator log, renderer errors (or absence), driver SHA-256, map, resolution, actual measured frames/timestamps, and clean shutdown.

**Pass E:** the matched ASURT application operates with a real coloured RGB stream, car controls and expected ROS functionality. If only Dozen enumerates, mark **C PASS, E NOT TESTED**. If it previously rendered but now fails, compare the selected driver SHA, cache directory, CARLA build, display, launch flags and map before altering code.

## F. Troubleshooting by symptom

| Symptom | Likely check / safe next action |
| --- | --- |
| /dev/dxg or libd3d12.so missing | Diagnose Windows GPU driver, WSL2 version and distribution first; do not copy GPU libraries from elsewhere |
| install.sh says destination already exists | Do **not** overwrite it; inspect the original install and manifest. For a deliberate replacement, use the verified uninstall script, then reinstall |
| verify.sh reports SHA-256 FAIL | Stop; obtain the untouched official GitHub archive/repo and inspect filesystem corruption |
| verify.sh says "vulkan-tools" missing yet exits zero | Install vulkan-tools; **C is NOT TESTED** until real vulkaninfo output selects Dozen |
| "not found" in ldd or undefined symbol | Resolve Ubuntu 22.04 userspace dependencies; do not install unrelated kernel drivers |
| Vulkan lists lavapipe or another ICD instead of Dozen | Run through scripts/run-dozen.sh; confirm the selected ICD path and corresponding binary |
| Dozen selected, but CARLA returns black RGB | Check matching CARLA build, clean **separate** shader-cache directory, compatibility flags and real RGB callbacks; driver enumeration is not full rendering |
| VK_ERROR_DEVICE_LOST / D3D12 device removed | Preserve complete native log and hardware/driver versions; do not claim generic Vulkan success implies compatibility |
| CARLA port occupied or duplicate launch | Keep the existing session intact and coordinate with its owner; do not force-kill processes or change ports without a plan |
| Visible window absent but RGB sensor works | Distinguish WSLg/X11 presentation from sensor rendering; check display services separately |
| ROS unavailable | Check separately installed ROS2 Humble / ASURT bridge and matched simulator; the Mesa kit does not install ROS |

**Expected limitation:** Recording-time uniform snapshots alter Vulkan's legal post-recording host-update behavior. Dozen warns it is not conformant; it is an opt-in workaround for this tested CARLA workload, not a system-wide Vulkan fix.

## G. Safe rollback / cleanup

First stop only the **simulator instance you started**, through its supervising terminal or the application's normal exit. Do not kill somebody else's processes.

If you exported CARLA settings in your current terminal, close that terminal or explicitly clear only those session-specific variables. They were **not** written to Windows, /etc, .bashrc or the system Vulkan ICD directories.

When removal of the package is desired, run:

```bash
KIT="$HOME/.local/opt/asurt-dozen-20261024"
bash "$KIT/scripts/uninstall.sh"
```

This script checks its installation marker and removes only that isolated default directory. It should not alter the original ASURT setup, Windows GPU driver, or /usr/lib/wsl/lib. If a custom install prefix was used, review the script's supported removal paths before proceeding.

## H. Human / coding-agent handoff template

Fill this in with **observed results**; do not copy the original authors' benchmarks as today's measurements:

```text
Machine / OS:
Windows build and GPU driver:
GPU model:
WSL version / distro / kernel:
Git commit or release tag:
Installed prefix:
Driver variant and libvulkan_dzn.so SHA-256:
Phase A (WSL GPU prerequisites): PASS / FAIL — evidence:
Phase B (hashes, ELF, install): PASS / FAIL — evidence:
Phase C (vulkaninfo Dozen/D3D12): PASS / FAIL / NOT TESTED — evidence:
Phase D (rendered CARLA camera): PASS / FAIL / NOT TESTED — map, client/server, frame IDs, resolution, hashes, logs:
Phase E (ASURT/ROS/controls): PASS / FAIL / NOT TESTED — map, hero, movement, topics, logs:
Crash or device-loss errors:
Cleanup status / port ownership:
Changes made outside this kit (ideally NONE):
Remaining blockers / next investigation:
```

**Agent execution rules:** inspect existing state first; do not install or destroy preexisting simulators; do not assume private CARLA/ASURT assets exist; never modify system-wide graphics settings; run the checks in order and stop on integrity or ownership failures; distinguish historical claims from tests you actually ran; report the exact failing command and log; leave the machine in a reversible state.

## Versioning and links

- Public repository: https://github.com/hassanradwannn/Mesa-Dozen-Custom-WSL-driver-for-Carla
- Published release v0.1.0: https://github.com/hassanradwannn/Mesa-Dozen-Custom-WSL-driver-for-Carla/releases/tag/v0.1.0
- Main project documentation: [README.md](README.md)
- Package manifest: [manifest.json](manifest.json)

**Important:** A v0.1.0 archive is a fixed historical release. New instructions committed to the main branch do not retroactively change that old archive; when using the archived installer, consult this guide online and verify the release digest shown in Phase B.
