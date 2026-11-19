# ASURT CARLA on WSL2 — Mesa Dozen team driver kit

## Purpose and placement

This package contains custom Mesa 26.2.5 Dozen Vulkan-to-Direct3D12 Linux x86-64 binaries, their ICD manifests, source diffs, checksums, license texts and isolated installation tools. Install it **inside WSL2 Ubuntu 22.04**, not Windows. The Windows host must retain a suitable GPU vendor's Windows graphics driver with WSL support, while WSL supplies /dev/dxg, libd3d12.so and libdxcore.so.

The default descriptor-reset-candidate binary has SHA256 cce0e8ac41b33b179c58e1a315c94d153fe1a7f031e57d09585a7d20616ccf78. The preserved ASURT WSLg launcher selects it. The October 24 report recorded moving coloured Silverstone views, ASURT controls/ROS and 28.26 FPS in two fixed-pose WSLg 180-second trials. This result is machine-specific, not a guaranteed frame rate or complete endurance certification.

The optional working binary has SHA256 33d4b222f9ea05bb18fcd10ac3cc757a3792b26919450eef3609427469674d14. The historical 25.674 FPS ASURT measurement used another intermediate binary (SHA256 e79358a40bf4c8eb8f57825ee9aff70b14c0038cf4e2f06ae4a65d61b8289614) and must not be attributed directly to this working artifact. The original /opt/carla-vulkan-26.2.5 baseline successfully enumerated Vulkan but failed UE4 rendering; it is deliberately not packaged.

## Windows and WSL team setup

1. Install/update WSL2 and your Windows GPU manufacturer's supported WSL-capable driver. Use Windows PowerShell: wsl --update.
2. Start WSL: wsl -d Ubuntu-22.04. Confirm /dev/dxg and /usr/lib/wsl/lib/libd3d12.so exist. Do not install NVIDIA Linux kernel/display drivers inside WSL.
3. Inside Ubuntu: sudo apt update; sudo apt install -y vulkan-tools libdrm2 libxcb1 libx11-xcb1 libxcb-dri3-0 libxcb-present0 libxcb-xfixes0 libxcb-sync1 libxcb-randr0 libxcb-shm0 libxshmfence1 libexpat1 zlib1g libzstd1
4. Clone this repository into the Linux home filesystem (or extract the GitHub release archive), and run: bash scripts/verify.sh --files-only
5. Run: bash scripts/install.sh
6. The installer creates only $HOME/.local/opt/asurt-dozen-20261024, and refuses to overwrite an existing destination. Confirm detection: $HOME/.local/opt/asurt-dozen-20261024/scripts/verify.sh
7. Launch an individual Vulkan application with: $HOME/.local/opt/asurt-dozen-20261024/scripts/run-dozen.sh <program> [args...]. To use the older working build, insert --variant working before the program.

## Integrating with the original ASURT simulator

The original launcher under ~/asurt/scripts/carla-gpu-profile-20261024/launch_gpu.py accepts CARLA_DRIVER_PREFIX with a lib/x86_64-linux-gnu and share/vulkan/icd.d directory. The kit preserves that layout.

For the ASURT WSLg launcher, set these environment variables in your Ubuntu ASURT shell:

    export CARLA_DRIVER_PREFIX="$HOME/.local/opt/asurt-dozen-20261024/variants/descriptor-reset-candidate"
    export CARLA_SHADER_CACHE_DIR="$HOME/.cache/asurt-dozen-descriptor-reset"
    export CARLA_UNIFORM_SNAPSHOTS=1
    export CARLA_STAGE_DESCRIPTORS=1
    export CARLA_CACHED_UNIFORMS=1
    export CARLA_POOL_UPLOADS=1
    export CARLA_POOL_CPU_DESCRIPTOR_HEAPS=1
    export CARLA_UPLOAD_POOL_MAX_MB=512
    export CARLA_CACHE_IMAGE_DESCRIPTORS=1
    python3 "$HOME/asurt/scripts/carla-gpu-profile-20261024/launch_asurt_sim.py" wslg --threading parallel --rhi-width 4

For VNC, use the original VNC supervisor and CARLA_CACHE_IMAGE_DESCRIPTORS=0. The simulator, ASURT custom matching client, map/vehicle assets, ROS2 Humble bridge and display services are NOT bundled here. Only one CARLA server should own port 2000. The existing supervisor controls cleanup, temporary Unreal configuration, map changes, and avoiding unsafe TCP connect/close readiness probes.

The standalone run-dozen.sh wrapper exports the equivalent DZN_* switches; it does not set Unreal RHI or ROS settings.

## How we got normal rendering

1. Initially UE4 showed a black image and lost the GPU around compute dispatch 41. A standalone reproduction isolated unstable uniform values; private GPU-readable copies restored intended shader inputs. Broader copies for graphics and compute returned road, markings and foliage to the intermediate HDR scene.
2. Final camera RGB was still black because a 32x32x32 colour lookup texture was zero. The neighboring-shader BLAKE3 cache-key array used incorrect dimensions [BLAKE3_KEY_LEN][2] instead of [2][BLAKE3_KEY_LEN]. Correcting the overlapping hash layout and using an isolated clean shader cache restored the lookup and real final colour.
3. Persistently mapped upload resources, staged CPU descriptors, targeted host-cached UBO memory, parallel-RHI shared snapshot readers, region reuse, bounded upload-resource pooling and shared CPU descriptor backing removed expensive allocation and descriptor overhead. Pool on/off gave 24.307 versus 12.522 stock world updates/sec in a same-binary run.
4. The later descriptor-reset candidate skipped freed/unused sets and redundant metadata clearing. The live ASURT driving application then rendered actual Silverstone RGB frames, drove the car, changed cameras and delivered live ROS topics. Unused spectator parking improved the distinct measured ASURT camera rate from 16.683 to 25.674 FPS in the earlier working session.

## Limitations, rollback and provenance

Uniform snapshots capture recording-time bytes. They intentionally differ from legal Vulkan updates between recording and submission; never enable this as a universal Vulkan compatibility replacement. Reported fixed-pose performance and long-term stability are specific to the recorded hardware/software and do not imply broad support. Some freshly rebuilt variants crashed during ASURT integration despite passing generic tests. The included patches are exact differences between preserved source trees, NOT a reviewed upstream patch series nor a guarantee that new binaries will pass full CARLA testing.

To rollback, remove the CARLA_DRIVER_PREFIX override or select the working variant. To uninstall only the kit, run $HOME/.local/opt/asurt-dozen-20261024/scripts/uninstall.sh; no system Mesa, Windows graphics drivers, /usr/lib/wsl/lib, WSL settings or global ICD paths are modified.

Original Mesa 26.2.5 source base commit recorded: ddaf85e353442d9d7f192fdcf1823e652e3f2ee3. Retained source files under src/microsoft/vulkan are the six changed Dozen files. This archive includes Mesa license notices under licenses/; upstream source license headers remain authoritative. Windows-side proprietary driver files, private CARLA/Unreal/ASURT assets and shader caches are not redistributed.

For evidence, see the engineering report CARLA GPU rendering on WSL2 with Mesa Dozen (23–24 October 2026), particularly sections 4–17, 19 and 22–27. This is a historical engineering record; runtime claims should be independently rechecked on new hardware. For maintainers rebuilding this kit from the original preserved source trees, set the ASURT_WSL_SOURCE_ROOT environment variable to the original WSL asurt folder and run python tools/assemble_from_wsl.py. Ordinary users do not need that original source-tree folder to install the release.
