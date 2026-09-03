# Status

Last updated: 2026-09-03

## Current Phase

Phase 7: v0.4 public beta — preserve the validated v0.3 3D runtime foundation, integrate the known wider camera patch, and continue targeted HUD/UI reverse engineering.

## What is verified

- Tekken 6 USA `ULUS10466`.
- `ULUS10466_EBOOT.BIN` is a decrypted 32-bit little-endian MIPS ELF suitable for static analysis.
- The known-good 20:9 CWCheat visually fixes the 3D view on the user's POCO F5 when PPSSPP Display Layout is set to Stretch.
- The four exact CWCheat/runtime aspect sites are:
  - `0x08945F10`
  - `0x08946794`
  - `0x08946BC8`
  - `0x08947D90`
- Original instruction pair at each site:
  - `0x3C013FE3`
  - `0x34218E39`
- Exact 20:9 pair:
  - `0x3C01400E`
  - `0x342138E4`
- v0.3's invalidate-before-write PRX approach was visually tested successfully and is now the validated 3D plugin baseline.
- The documented gameplay-camera instruction is at `0x0895350C`:
  - Original: `0x3C013F80`
  - Slightly Wider: `0x3C013F81`
  - Wider: `0x3C013F82`
  - Widest: `0x3C013F83`
- Generic orthographic Paths A/B/C were user-tested visible no-ops for HUD/UI/menu screens.
- The Warriors Fusion Fix uses separate 3D aspect and HUD-scale hooks; Tekken still needs its actual HUD-scale equivalent identified.

## v0.1 result

FAILED/UNVERIFIED. Both 3D and HUD appeared stretched. It used fixed addresses and mixed HUD experiments into the first PRX test.

## v0.2 result

The v0.2 log proved the PRX loaded and wrote the correct four 3D aspect sites. It also exposed PPSSPP's `0x68xxxxxx` JIT/emuhack block markers. Those markers were initially mistaken for game-side code reversion.

See `docs/PLUGIN_V02_LOG_ANALYSIS.md`.

## v0.3 result

SUCCESSFUL 3D BASELINE.

v0.3 changed the ordering to mirror PPSSPP CWCheat more closely:

1. `sceKernelIcacheInvalidateRange()` first,
2. inspect the restored guest instruction,
3. write the requested aspect pair,
4. `sceKernelDcacheWritebackRange()`,
5. repeat continuously at a configurable cadence (default 77 ms).

The user tested the resulting plugin and confirmed that it worked. This closes the PRX/JIT foundation question and allows development to move forward from a known-good plugin baseline.

## v0.4 implementation

v0.4 keeps the validated v0.3 3D path and adds the known camera adjustment using the same invalidate-before-write discipline.

Default package:

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1

EnableCamera = 1
CameraPreset = 2

PatchIntervalMs = 77
DebugLogging = 0
```

`CameraPreset = 2` is the project's previously documented **Wider** value (`0x3F82`). The camera can be disabled independently or changed between Original / Slightly Wider / Wider / Widest without rebuilding the PRX.

v0.4 is labeled beta because the combined PRX camera integration is new even though the underlying camera address/value research and the v0.3 3D foundation are established.

## HUD/UI research status

HUD correction remains disabled in v0.4.

The project's current evidence says not to patch generic 480×272 projection constants globally. Focused CI tracing instead highlighted:

- descriptor/render family around `0x08A391xx`–`0x08A39Axx`,
- coordinate/set helper `0x08A39158`,
- initializer `0x08A392F0`,
- follow-up float/property helper `0x08A39808`.

The suspected `+0x4C` structure field is not safe to patch globally: static analysis found it used broadly across the executable. Future work must identify a callsite-specific or subsystem-specific HUD scale/coordinate path before enabling any UI patch in a release.

## Immediate next steps

1. Device-test v0.4 with `CameraPreset = 2` and confirm the combined PRX produces the same wider camera behavior as the known cheat/INI value.
2. Test `CameraPreset = 0`, `1`, and `3` to confirm the plugin switch behaves independently of the 3D aspect fix.
3. Continue tracing the `0x08A39808` caller families and descriptor ownership to isolate battle HUD/menu callsites.
4. Keep overlays, health bars, menus, and general 2D projection experiments separated until a dedicated hook is proven.
5. Only after a safe HUD hook is validated should it become enabled by default in a future release.
