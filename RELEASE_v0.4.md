# Tekken 6 PPSSPP Ultrawide Fix v0.4

v0.4 promotes the proven v0.3 ultrawide runtime foundation into a more practical public beta and adds the project's known camera adjustment directly to the PRX.

## What's new

- Added the gameplay camera patch at runtime address `0x0895350C`.
- **Wider camera is now the default**: `0x3F82` (`lui $at, 0x3F82`).
- Added configurable camera presets in `Tekken6.PPSSPP.UltrawideFix.ini`:
  - `0` — Original (`0x3F80`)
  - `1` — Slightly Wider (`0x3F81`)
  - `2` — Wider (`0x3F82`) — default
  - `3` — Widest (`0x3F83`)
- Added `EnableCamera` so the camera patch can be disabled independently.
- Retained the validated v0.3 3D aspect patch and PPSSPP JIT-safe invalidate-before-write behavior.
- Kept the default target at `20:9`.
- Disabled verbose diagnostic logging by default; set `DebugLogging = 1` when troubleshooting.
- Expanded automated HUD/camera static analysis and documented the current HUD research direction.
- Added a full project README with installation, configuration, compatibility, research status, and development notes.

## Important HUD/UI status

**HUD/UI/menu ultrawide correction is not included yet.**

Previous testing ruled out the obvious global 480×272 orthographic patches because they either produced no useful correction or risked affecting unrelated 2D elements such as health bars and overlays.

Current research is focused on identifying a dedicated HUD-scale/render-state path similar in architecture to Warriors Fusion Fix. Static analysis has highlighted the `0x08A391xx`–`0x08A39Axx` descriptor family and the property helper at `0x08A39808`, but no broad patch from that family is enabled in this release because the relevant fields are shared widely across the executable.

## Default configuration

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1

EnableCamera = 1
CameraPreset = 2

PatchIntervalMs = 77
DebugLogging = 0
```

## Compatibility

- Game: **Tekken 6 USA**
- Game ID: **ULUS10466**
- Emulator: **PPSSPP with plugin support**
- Primary development target: modern ultrawide Android devices; 20:9 was the main test ratio.

Other game regions are not supported by this release because their executable addresses have not yet been mapped and validated.

## Install / upgrade

Replace the complete previous plugin folder with the v0.4 package so the active PPSSPP memory-stick path contains:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

Disable older Tekken 6 ultrawide CWCheats that modify the same aspect or camera code before testing the plugin, then fully restart PPSSPP.

## Validation note

The **3D runtime foundation is already visually validated from v0.3**. The v0.4 camera integration uses the camera address and values established by the project's earlier working INI/CWCheat research. Because the combined PRX build is new, v0.4 is intentionally labeled **beta** and should receive fresh device testing before the camera portion is considered fully validated across platforms.

## Known limitations

- HUD/UI/menu elements are not yet ultrawide-corrected.
- Only `ULUS10466` is supported.
- The current runtime approach intentionally reapplies code patches at a configurable interval to mirror the known-good PPSSPP CWCheat behavior. A cleaner dedicated runtime hook remains a future optimization once the rendering paths are fully understood.

## Research milestone

The repository now includes reproducible CI-based disassembly/data-flow tracing for the known camera site and the strongest HUD candidates. This keeps future HUD work evidence-driven and preserves failed experiments so they are not repeated.
