# Tekken 6 PPSSPP Ultrawide Fix — v0.6 beta test guide

Last updated: 2026-09-03

## What v0.6 tests

v0.6 keeps the validated ultrawide 3D and camera baseline, removes the plugin's forced 93 MB emulated-memory request, and replaces the failed v0.5 HUD experiment with one native-PSP flat-layer viewport transform.

The intended result is:

```text
3D world: full ultrawide
2D/HUD/menu: centered, native PSP 480:272 proportions, no horizontal stretch
```

No individual HUD positions are edited.

## Install

Replace the previous plugin folder completely:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

Then fully close PPSSPP before launching Tekken 6 again. Do not rely on a savestate for the first test because the plugin manifest memory setting changed.

Supported game: `ULUS10466`.

## Supplied INI

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

Use PPSSPP Display Layout = `Stretch` for comparison with the known development baseline.

## Test 1 — texture compatibility

Use the same custom HD texture pack that showed selective fallback in v0.4/v0.5.

Check the exact affected areas first:

- pause menu,
- bottom button prompts/indications,
- any menu/UI texture previously reverting to the original PSP asset.

Record whether each replacement is:

```text
restored / still missing / intermittent
```

Do not modify the texture pack's `textures.ini` for this first v0.6 comparison.

## Test 2 — 3D/camera regression

Enter the same kind of fight used to validate v0.4.

Expected:

- character proportions remain correct,
- field of view remains ultrawide,
- `CameraPreset = 2` still looks like the known Wider camera,
- stage/3D geometry should not be compressed into the 2D safe area.

If the world itself becomes narrower/boxed, report it immediately; that would mean the selected flat viewport is not sufficiently isolated.

## Test 3 — native PSP flat layer

Check:

- battle health bars,
- names,
- timer/round/rage UI,
- prompts,
- pause menu,
- main/options menus,
- character select,
- stage select,
- results screens,
- ordinary 2D backgrounds/overlays.

Expected behavior: the complete flat presentation should look like the original PSP composition placed in a centered safe area, without individually moving elements and without horizontal stretch.

At 20:9 the plugin uses exact native PSP proportions:

```text
safeScale = (480/272) / (20/9)
          = 27/34
          ≈ 0.794117647
```

## A/B fallback

If a screen looks wrong, change only:

```ini
EnableNative2DSafeArea = 0
```

cold restart PPSSPP and revisit the same screen.

This leaves the 3D aspect and camera fixes enabled and gives a clean comparison of the new flat-layer path.

## Diagnostic logging

Set:

```ini
DebugLogging = 1
```

Expected log header:

```text
=== Tekken6.PPSSPP.UltrawideFix v0.6 ===
Plugin module_start reached successfully
```

A successful first patch cycle should include messages equivalent to:

```text
3D: installed all four validated aspect sites
Camera: installed validated camera site
2D: installed native-PSP safe-area viewport hook
```

Log path:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log
```

## Report template

```text
PPSSPP version:
Device/platform:
Display resolution/aspect:
Display Layout:
HD texture pack:
ForceAspectRatio:
CameraPreset:
EnableNative2DSafeArea:

3D world: correct / wrong
Camera: correct / wrong
Battle HUD proportions: native / stretched / other
Menus: native / stretched / other
Pause UI: native / stretched / other
Replacement textures: restored / mixed / still missing
Specific problem screens:
```

Screenshots of the same screen with `EnableNative2DSafeArea = 1` and `0` are especially useful.
