# Tekken 6 PPSSPP Ultrawide Fix

A fan-made PPSSPP plugin and reverse-engineering project for **Tekken 6 (USA, ULUS10466)** focused on proper ultrawide 3D rendering, camera tuning, and ultimately HUD/UI/menu correction.

> **Current release:** v0.4 (beta)  
> **Supported game:** Tekken 6 USA — `ULUS10466`  
> **Primary target:** PPSSPP on modern widescreen / ultrawide Android devices

This project is not affiliated with or endorsed by Bandai Namco Entertainment, Sony, or the PPSSPP project. You must provide your own legally obtained copy of Tekken 6.

## What v0.4 does

- Applies the validated 3D ultrawide aspect patch from the working v0.3 PRX baseline.
- Defaults to **20:9**, matching the target device used during development.
- Adds the known working **Wider** camera adjustment directly to the plugin.
- Keeps the camera setting configurable through the plugin INI.
- Mirrors PPSSPP CWCheat's important **invalidate-before-write** behavior so patched code survives PPSSPP JIT/emuhack handling reliably.
- Includes reproducible static-analysis tooling and CI traces for ongoing HUD/UI research.

## Current status

| Area | Status |
| --- | --- |
| 3D ultrawide aspect | ✅ Working / validated baseline |
| 20:9 target | ✅ Implemented |
| Wider gameplay camera | ✅ Implemented in v0.4 |
| Camera presets | ✅ Configurable |
| PPSSPP JIT-safe runtime patching | ✅ Implemented |
| HUD/UI/menu correction | 🧪 Research in progress |
| Pause overlays / health bars / 2D special cases | 🧪 Not yet corrected |
| Other Tekken 6 regions | ❌ Not supported yet |

The HUD/UI/menu portion is deliberately **not** advertised as finished. Earlier experiments showed that changing generic 480×272 orthographic paths is too broad and can affect unrelated 2D elements. Current research is instead looking for the Tekken equivalent of the dedicated HUD-scale path used by projects such as Warriors Fusion Fix.

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
4. Disable any older Tekken 6 widescreen / ultrawide CWCheat that changes the same aspect or camera addresses.
5. Fully restart PPSSPP and launch Tekken 6 normally.

For the development target, PPSSPP Display Layout was tested with **Stretch** so the plugin is responsible for correcting the game-side 3D projection while PPSSPP fills the physical screen.

## Default configuration

The supplied v0.4 INI uses:

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1

EnableCamera = 1
CameraPreset = 2

PatchIntervalMs = 77
DebugLogging = 0
```

### Camera presets

| `CameraPreset` | Result | Patched value |
| ---: | --- | --- |
| `0` | Original | `0x3F80` |
| `1` | Slightly Wider | `0x3F81` |
| `2` | **Wider — v0.4 default** | `0x3F82` |
| `3` | Widest | `0x3F83` |

The camera instruction is located at runtime address `0x0895350C`. The original instruction is `lui $at, 0x3F80`; v0.4's default changes it to `lui $at, 0x3F82`.

## Why a plugin instead of only CWCheat?

The original ultrawide work proved that the correct 3D result could be achieved using CWCheat. Turning those findings into a PPSSPP plugin provides a cleaner install path and creates a foundation for more advanced fixes that are difficult to maintain as isolated cheat writes.

A key obstacle was PPSSPP's JIT. PPSSPP can replace the first instruction of compiled guest blocks with internal `0x68xxxxxx` emuhack markers. v0.2 initially interpreted those markers as a failed or reverted patch. v0.3 corrected this by reproducing the ordering used by PPSSPP's own CWCheat engine:

1. invalidate the relevant instruction/JIT range,
2. inspect the restored guest instruction,
3. apply the target instruction,
4. write back the data cache,
5. repeat at a configurable interval.

That v0.3 approach was visually validated and is retained as the v0.4 runtime foundation.

## HUD/UI research

The next major goal is proper ultrawide placement/scaling for:

- health bars and fight HUD,
- menus,
- pause UI,
- overlays,
- other 2D elements.

Three generic 480×272 orthographic candidates were already ruled out by runtime testing. Current static analysis has identified a more promising 2D descriptor family around `0x08A391xx`–`0x08A39Axx`, including a repeatedly used float/property helper at `0x08A39808`.

That path is **not enabled in v0.4** because the associated structure field is used broadly throughout the executable. The project will only promote a HUD patch after a callsite- or subsystem-specific hook is identified and tested, avoiding the regressions seen with earlier global 2D experiments.

## Research and documentation

The repository intentionally preserves both successful and failed experiments so later work does not repeat already-disproven approaches.

Useful documents:

- [`docs/STATUS.md`](docs/STATUS.md) — current project state and verified findings
- [`docs/BASELINE.md`](docs/BASELINE.md) — known-good ultrawide baseline
- [`docs/ADDRESS_MAP.md`](docs/ADDRESS_MAP.md) — important runtime addresses and candidates
- [`docs/HUD_RESEARCH.md`](docs/HUD_RESEARCH.md) — HUD/UI reverse-engineering work
- [`docs/WARRIORS_ARCHITECTURE.md`](docs/WARRIORS_ARCHITECTURE.md) — architecture study used as a reference
- [`docs/PLUGIN_V01_FAILURE_ANALYSIS.md`](docs/PLUGIN_V01_FAILURE_ANALYSIS.md) — first PRX failure analysis
- [`docs/PLUGIN_V02_LOG_ANALYSIS.md`](docs/PLUGIN_V02_LOG_ANALYSIS.md) — PPSSPP JIT/emuhack discovery
- [`docs/PLUGIN_TEST.md`](docs/PLUGIN_TEST.md) — current plugin test procedure
- [`docs/HANDOFF.md`](docs/HANDOFF.md) — research handoff / continuation notes

## Building from source

The plugin uses the PSP SDK / `pspdev` toolchain.

```bash
make -C plugin clean all
```

GitHub Actions also builds the PRX, packages the PPSSPP plugin directory, and runs the repository's focused static-analysis trace against the checked-in research EBOOT.

## Compatibility and known limitations

- Only `ULUS10466` is currently supported.
- v0.4 is a **beta** release because the combined PRX camera integration is newer than the already validated v0.3 3D-only baseline.
- HUD/UI/menu correction is still under development.
- Savestates created under heavily modified cheat configurations may complicate testing; cold-boot testing is preferred while reverse engineering.
- Do not run the old ultrawide CWCheat and the PRX patch against the same code addresses at the same time.

## Contributing / continuing the research

Useful contributions include:

- confirming v0.4 behavior on additional PPSSPP platforms,
- testing camera presets,
- identifying HUD-specific render-state callsites,
- tracing menu and battle-HUD draw paths,
- documenting region differences for non-ULUS builds.

When reporting a rendering issue, include the PPSSPP version, game region/ID, device or desktop aspect ratio, plugin INI, and screenshots showing the affected screen.

## Release history

### v0.4

- Promotes the validated v0.3 3D runtime foundation into a public beta.
- Adds the **Wider** camera preset (`0x3F82`) as the default.
- Adds configurable camera presets.
- Disables verbose debug logging by default.
- Expands reproducible HUD/camera static-analysis tooling and documentation.
- Keeps experimental HUD correction disabled until a safe dedicated hook is proven.

### v0.3

- First visually successful PRX baseline for the known-good ultrawide 3D patch.
- Corrected PPSSPP JIT handling by invalidating code before inspecting/writing it, matching CWCheat behavior more closely.
