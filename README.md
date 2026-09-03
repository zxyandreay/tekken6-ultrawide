# Tekken 6 PPSSPP Ultrawide Fix

A fan-made PPSSPP plugin and reverse-engineering project for **Tekken 6 USA (`ULUS10466`)**.

> **Current release:** v0.6 beta  
> **Primary target:** 20:9 Android devices such as the POCO F5  
> **Development display mode:** PPSSPP Display Layout = `Stretch`

The project is not affiliated with Bandai Namco Entertainment, Sony, or PPSSPP. Use your own legally obtained copy of Tekken 6.

## v0.6 design

v0.6 deliberately separates the game into two presentation goals:

```text
3D world        -> true ultrawide aspect + wider camera
flat 2D layer   -> native PSP 480:272 proportions, centered, not stretched
```

The 2D fix is **not** an element-by-element HUD repositioning system. Tekken keeps its original HUD/menu coordinates and layout. The plugin only changes how the complete flat viewport is mapped before PPSSPP performs its final Stretch.

## Current status

| Area | Status |
| --- | --- |
| 3D ultrawide aspect | ✅ Validated baseline |
| 20:9 | ✅ Implemented |
| Wider gameplay camera | ✅ Validated baseline |
| Camera presets | ✅ Configurable |
| Low-churn PPSSPP JIT maintenance | ✅ Implemented |
| Forced 93 MB plugin memory override | ✅ Removed in v0.6 |
| Native PSP 2D safe-area viewport | 🧪 New in v0.6; device validation required |
| Other Tekken 6 regions | ❌ Not supported yet |

## Installation

Extract the release ZIP into the active PPSSPP memory-stick location so you have:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

Then:

1. Enable PPSSPP plugins for Tekken 6.
2. Disable older Tekken 6 CWCheats that change the same aspect/camera addresses.
3. Use PPSSPP Display Layout = `Stretch` for the established 20:9 development setup.
4. Fully close PPSSPP and cold boot Tekken 6.

A full restart matters for v0.6 because the plugin manifest no longer forces extended emulated RAM.

## Default configuration

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1

EnableCamera = 1
CameraPreset = 2

EnableNative2DSafeArea = 1

PatchIntervalMs = 77
DebugLogging = 0
```

### Camera presets

| Value | Result | Word |
| ---: | --- | --- |
| `0` | Original | `0x3F80` |
| `1` | Slightly Wider | `0x3F81` |
| `2` | **Wider — default** | `0x3F82` |
| `3` | Widest | `0x3F83` |

## 3D foundation

The known-good Tekken 6 aspect fix uses four runtime sites:

```text
0x08945F10
0x08946794
0x08946BC8
0x08947D90
```

The gameplay camera site is:

```text
0x0895350C
```

These addresses and their validated v0.4 behavior are intentionally unchanged by v0.6.

PPSSPP JIT can replace guest-code block starts with internal `0x68xxxxxx` emuhack markers. The plugin installs code changes with invalidate-before-write behavior and then uses low-churn maintenance rather than repeatedly invalidating healthy blocks.

## Native PSP 2D safe area

### Requirement

The objective is to keep all ordinary flat graphics in their **native PSP presentation** while the 3D scene fills the ultrawide display:

- health bars,
- names and timer,
- button prompts,
- menus,
- character/stage select,
- pause/results/options UI,
- ordinary flat backgrounds and overlays.

Tekken's original authored positions are not individually modified.

### Why the earlier v0.5 approach was removed

v0.5 experimented with changing a logical-width field in three calls to initializer `0x08A392F0`. Device testing showed the battle HUD remained stretched, proving that descriptor was not the required common HUD presentation path.

That hook is removed in v0.6.

### v0.6 viewport path

Static tracing identified runtime call `0x08864B88` as a live flat/surface viewport path. Unlike Tekken's validated perspective setup and the three previously tested generic orthographic paths, the surrounding function has no direct perspective or orthographic builder call.

The original game arrives at the viewport routine with:

```text
f12 = X
f13 = Y
f14 = width
f15 = height
f16 = near
f17 = far
```

v0.6 redirects only that call through `safe_area.S`, which applies:

```text
nativePSPAspect = 480 / 272
safeScale       = nativePSPAspect / targetAspect
safeWidth       = width * safeScale
safeX           = x + (width - safeWidth) / 2
```

Y, height, depth, and all Tekken-authored UI coordinates are untouched.

For 20:9:

```text
safeScale = (480/272) / (20/9)
          = 27/34
          ≈ 0.794117647
```

This is intended to inverse-compensate the horizontal part of PPSSPP Stretch for the flat layer only.

Disable the new path without disabling 3D/camera using:

```ini
EnableNative2DSafeArea = 0
```

## Replacement textures and memory

v0.4/v0.5 packages declared:

```ini
memory = 93
```

in `plugin.ini`. PPSSPP uses that field to raise the game's emulated RAM size. The ultrawide PRX does not require that memory override.

v0.6 removes the field entirely. This keeps Tekken in PPSSPP's normal memory configuration and removes a major source of allocation-layout changes that can alter dynamically prepared UI texture hashes/padding and make some replacement textures fall back to originals.

The plugin does not modify `textures.ini`, HD texture files, or PPSSPP replacement keys.

## Building

Requires PSPDEV / PSPSDK:

```bash
make -C plugin clean all
```

The plugin now builds from:

```text
plugin/main.c
plugin/safe_area.S
```

GitHub Actions also runs the EBOOT static-analysis traces before packaging/release.

## Research files

- [`docs/STATUS.md`](docs/STATUS.md)
- [`docs/HUD_RESEARCH.md`](docs/HUD_RESEARCH.md)
- [`docs/ADDRESS_MAP.md`](docs/ADDRESS_MAP.md)
- [`docs/PLUGIN_TEST.md`](docs/PLUGIN_TEST.md)
- [`docs/WARRIORS_ARCHITECTURE.md`](docs/WARRIORS_ARCHITECTURE.md)
- [`tools/trace_native_2d_path.py`](tools/trace_native_2d_path.py)
- [`tools/trace_hud_candidates.py`](tools/trace_hud_candidates.py)

## Release history

### v0.6

- Removes the forced 93 MB emulated-memory request.
- Removes the ineffective v0.5 descriptor-width HUD hook.
- Adds one centered native-PSP 2D viewport hook at `0x08864B88`.
- Uses exact PSP `480:272` proportions rather than treating PSP output as exact 16:9.
- Preserves the validated v0.4 3D and camera behavior.

### v0.5

- Added low-churn JIT maintenance.
- Tested a three-callsite logical-width HUD experiment; battle HUD remained stretched, so that experiment is retired in v0.6.

### v0.4

- Validated public baseline combining the successful 3D fix and configurable wider camera.
