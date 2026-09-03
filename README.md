# Tekken 6 PPSSPP Ultrawide Fix

A fan-made PPSSPP plugin and reverse-engineering project for **Tekken 6 (USA, ULUS10466)** focused on proper ultrawide 3D rendering, camera tuning, and targeted HUD/UI correction.

> **Current release:** v0.5 beta  
> **Supported game:** Tekken 6 USA — `ULUS10466`  
> **Primary target:** PPSSPP on modern widescreen / ultrawide Android devices

This project is not affiliated with or endorsed by Bandai Namco Entertainment, Sony, or the PPSSPP project. You must provide your own legally obtained copy of Tekken 6.

## What v0.5 does

- Keeps the visually validated v0.3/v0.4 3D ultrawide runtime foundation.
- Defaults to **20:9**.
- Keeps the configurable gameplay-camera fix, with **Wider** as the default preset.
- Retains PPSSPP JIT-safe invalidate-before-write installation.
- Reduces repeated JIT/cache churn by no longer invalidating and rewriting already healthy patched blocks every maintenance poll.
- Adds a **targeted experimental HUD/UI logical-canvas hook** at only three traced external initializer callsites.
- Leaves the earlier disproven global 480x272 projection experiments disabled.

## Current status

| Area | Status |
| --- | --- |
| 3D ultrawide aspect | ✅ Working / validated baseline |
| 20:9 target | ✅ Implemented |
| Wider gameplay camera | ✅ Implemented |
| Camera presets | ✅ Configurable |
| PPSSPP JIT-safe runtime patching | ✅ Implemented |
| Low-churn JIT maintenance | ✅ New in v0.5 |
| HUD/UI logical-canvas hook | 🧪 Experimental in v0.5 |
| General HUD/menu correction | 🧪 Not yet considered complete |
| Other Tekken 6 regions | ❌ Not supported yet |

## Installation

1. Download the latest release ZIP.
2. Extract it into the active PPSSPP memory-stick directory so this folder exists:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

3. Make sure PPSSPP plugins are enabled for Tekken 6.
4. Disable older Tekken 6 widescreen/ultrawide CWCheats that change the same aspect or camera addresses.
5. Fully restart PPSSPP and launch Tekken 6 normally.

The development baseline uses PPSSPP Display Layout = **Stretch**, with the plugin correcting the game-side 3D projection.

## Default v0.5 configuration

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1

EnableCamera = 1
CameraPreset = 2

EnableHUDExperimental = 1

PatchIntervalMs = 77
DebugLogging = 0
```

The packaged beta enables the experimental HUD path so it can be tested immediately. The PRX's built-in fallback keeps that option disabled if the INI is missing.

If a menu or HUD screen regresses, set:

```ini
EnableHUDExperimental = 0
```

and fully restart PPSSPP. The 3D and camera fixes remain active.

## Camera presets

| `CameraPreset` | Result | Patched value |
| ---: | --- | --- |
| `0` | Original | `0x3F80` |
| `1` | Slightly Wider | `0x3F81` |
| `2` | **Wider — default** | `0x3F82` |
| `3` | Widest | `0x3F83` |

The camera instruction is at runtime address `0x0895350C`. The original instruction is `lui $at, 0x3F80`; preset 2 changes it to `lui $at, 0x3F82`.

## 3D runtime foundation

The four established 3D aspect sites are:

```text
0x08945F10
0x08946794
0x08946BC8
0x08947D90
```

PPSSPP can replace the first guest instruction of a compiled block with an internal `0x68xxxxxx` emuhack marker. The successful v0.3 plugin fixed the earlier PRX failure by following the same important order used by PPSSPP's CWCheat path:

1. invalidate the relevant instruction/JIT range,
2. inspect the restored guest instruction,
3. apply the target instruction,
4. write back the data cache.

v0.5 keeps that behavior when a patch actually needs installation. Once the requested code is healthy, maintenance polls leave the target/emuhack state alone instead of repeatedly forcing the block back through invalidation.

## Experimental HUD/UI path

Earlier runtime tests ruled out three generic 480x272 orthographic/projection candidates because they were too broad and could affect unrelated 2D elements.

Focused static tracing later identified a 2D descriptor family around `0x08A391xx–0x08A39Axx`. Initializer `0x08A392F0` builds a descriptor with:

```text
+0x28 = 480.0   logical width
+0x2C = 272.0   logical height
```

v0.5 redirects only these three external calls to that initializer:

```text
0x089A92D8
0x089AB3A4
0x089AD87C
```

The hook calls the original initializer first, preserves its return value, then changes only `+0x28` to an aspect-derived logical width:

```text
480 * targetAspect / (16/9)
```

At 20:9, the experimental width is **600**, producing a `600x272` logical canvas for those three paths.

This is intentionally described as an **experiment**, not a finished universal HUD fix. It needs screen-by-screen device validation.

## Why `+0x4C` is not patched

Earlier research considered descriptor field `+0x4C`. A later whole-executable scan found 117 generic COP1 references at that offset, and the initializer sets a run of fields (`+0x40`, `+0x44`, `+0x48`, `+0x4C`) to `1.0`. That makes color/alpha-style state more plausible than a dedicated HUD horizontal-scale control.

v0.5 therefore does **not** patch `+0x4C`, and it does not invent a global `+0x30/+0x34` scale hook either.

## Replacement texture packs

The plugin does not edit texture image data or PPSSPP texture-replacement definitions. v0.5's compatibility change is on the code/JIT side: it avoids needless repeated invalidation of already healthy guest-code blocks.

For a useful replacement-texture test, compare the same screen with:

```ini
EnableHUDExperimental = 1
```

and:

```ini
EnableHUDExperimental = 0
```

If a replacement disappears only when the experimental HUD path is enabled, report that exact screen/texture. That gives the project a concrete renderer path to isolate without broad global patches.

## Research and documentation

Useful files:

- [`docs/STATUS.md`](docs/STATUS.md) — current verified state and next tests
- [`docs/BASELINE.md`](docs/BASELINE.md) — known-good ultrawide baseline
- [`docs/ADDRESS_MAP.md`](docs/ADDRESS_MAP.md) — important runtime addresses
- [`docs/HUD_RESEARCH.md`](docs/HUD_RESEARCH.md) — HUD/UI reverse-engineering work
- [`docs/WARRIORS_ARCHITECTURE.md`](docs/WARRIORS_ARCHITECTURE.md) — reference architecture study
- [`docs/PLUGIN_TEST.md`](docs/PLUGIN_TEST.md) — v0.5 test procedure
- [`docs/HANDOFF.md`](docs/HANDOFF.md) — research handoff notes
- [`tools/trace_hud_candidates.py`](tools/trace_hud_candidates.py) — reproducible HUD trace
- [`tools/trace_v05_candidates.py`](tools/trace_v05_candidates.py) — focused v0.5 callsite/field trace

## Building from source

The plugin uses PSPDEV / PSPSDK:

```bash
make -C plugin clean all
```

GitHub Actions builds the PRX, packages the PPSSPP plugin directory, and runs the static-analysis traces against the checked-in research EBOOT.

## Compatibility and limitations

- Only `ULUS10466` is currently supported.
- v0.5 is a **beta** because the targeted UI canvas path requires device validation.
- General HUD/UI/menu correction is not yet complete.
- Cold-boot testing is preferred while reverse engineering.
- Do not run an old ultrawide CWCheat and the PRX against the same code addresses simultaneously.

## Release history

### v0.5

- Keeps the validated 3D and camera addresses/values unchanged.
- Adds low-churn JIT maintenance after initial patch installation.
- Adds `EnableHUDExperimental`.
- Adds a caller-specific hook for three traced `0x08A392F0` UI initializer calls.
- Uses an aspect-derived logical width (`600x272` at 20:9) only on those hooked descriptors.
- Rejects `+0x4C` and broad 480x272 patches as unsafe targets based on the current trace.

### v0.4

- Promoted the validated v0.3 3D runtime foundation into a public beta.
- Added the Wider camera preset (`0x3F82`) as the default.
- Added configurable camera presets.
- Expanded reproducible HUD/camera analysis tooling.

### v0.3

- First visually successful PRX baseline for the known-good ultrawide 3D patch.
- Corrected PPSSPP JIT handling by invalidating code before inspecting/writing it.
