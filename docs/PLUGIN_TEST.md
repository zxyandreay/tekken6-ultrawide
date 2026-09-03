# Tekken 6 PPSSPP Ultrawide Fix — v0.5 beta test guide

Last updated: 2026-09-03

## What this build tests

v0.5 preserves the validated 3D and camera behavior, reduces repeated PPSSPP JIT/cache churn, and enables one narrowly scoped HUD/UI experiment in the supplied INI.

The HUD experiment is not considered finished. It redirects only three traced UI initializer callsites and changes their logical canvas width after the game's original initializer runs.

## Install

Replace the entire previous plugin folder with the v0.5 package:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

Supported game: `ULUS10466`.

Disable any older Tekken 6 widescreen/ultrawide CWCheat that changes the same 3D aspect or camera addresses, fully close PPSSPP, then cold boot the game.

## Supplied configuration

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

At 20:9, the experimental UI descriptors use a logical width of 600 instead of 480 while retaining the original logical height of 272.

## First test: baseline regression check

With `EnableHUDExperimental = 1`:

1. Use the same PPSSPP Display Layout (`Stretch`) as the established development baseline.
2. Enter a fight and confirm character proportions and horizontal field of view still match v0.4.
3. Confirm `CameraPreset = 2` still gives the expected Wider camera.
4. Check the fight HUD and at least one menu/pause screen.

If 3D or camera changed, report that separately from HUD behavior because v0.5 does not intentionally change their addresses or values.

## HUD A/B test

Test the same screens twice with a full PPSSPP restart between runs.

Run A:

```ini
EnableHUDExperimental = 1
```

Run B:

```ini
EnableHUDExperimental = 0
```

Compare:

- health bars and fight HUD,
- character select,
- pause UI,
- result screens,
- prompts and overlays,
- full-screen 2D backgrounds/panels.

If the experimental hook improves one family but breaks another, record the exact screens. Do not compensate with additional global cheats during this comparison.

## Replacement-texture A/B test

If you use a PPSSPP replacement texture pack, keep the pack itself unchanged and repeat the HUD A/B test.

Report whether a replacement texture:

- works with both settings,
- disappears only when `EnableHUDExperimental = 1`,
- disappears with both settings,
- changes only on a specific screen.

v0.5 does not intentionally change texture data or replacement keys. The runtime maintenance change merely avoids invalidating/re-writing already healthy JIT blocks every polling cycle.

## Emergency fallback

If a menu/HUD path becomes unusable, use:

```ini
EnableHUDExperimental = 0
```

The 3D ultrawide and camera fixes remain enabled.

## Camera controls

```text
CameraPreset = 0   Original
CameraPreset = 1   Slightly Wider
CameraPreset = 2   Wider (default)
CameraPreset = 3   Widest
```

## Diagnostic logging

Change:

```ini
DebugLogging = 1
```

and fully restart PPSSPP. The log is:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log
```

Expected header:

```text
=== Tekken6.PPSSPP.UltrawideFix v0.5 ===
Plugin module_start reached successfully
```

A successful first pass can log messages equivalent to:

```text
3D: initial low-churn cycle installed all four sites
Camera: initial low-churn cycle installed the camera site
HUD: installed all three targeted experimental UI hooks
```

## Useful report format

```text
PPSSPP version:
Platform/device:
Display aspect ratio:
ForceAspectRatio:
CameraPreset:
EnableHUDExperimental:
Replacement texture pack: none / name
3D aspect: correct / incorrect
Camera: correct / incorrect
Fight HUD: improved / same / worse
Menus/pause: improved / same / worse
Replacement textures: working / missing / mixed
Specific affected screens:
```

Screenshots of the same screen with the HUD option on and off are especially useful.
