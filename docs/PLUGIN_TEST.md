# Tekken 6 PPSSPP Ultrawide Fix — v0.4 beta test guide

Last updated: 2026-09-03

## What this build tests

v0.3 established a visually working PRX baseline for the known-good 3D ultrawide patch by reproducing PPSSPP CWCheat's invalidate-before-write behavior.

v0.4 keeps that validated 3D path and adds the project's known gameplay-camera adjustment directly to the PRX.

HUD/UI/menu correction is still intentionally disabled.

## Install

Replace the entire previous plugin folder with the v0.4 package so these files exist:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

Supported game:

```text
ULUS10466
```

## Supplied configuration

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1

EnableCamera = 1
CameraPreset = 2

PatchIntervalMs = 77
DebugLogging = 0
```

Camera presets:

```text
0 = Original        0x3F80
1 = Slightly Wider  0x3F81
2 = Wider           0x3F82   (v0.4 default)
3 = Widest          0x3F83
```

## PPSSPP test conditions

1. Disable the existing Tekken 6 ultrawide/widescreen CWCheat.
2. Keep PPSSPP Display Layout = `Stretch` for comparison with the established development baseline.
3. Ensure plugins are enabled for Tekken 6.
4. Fully close PPSSPP.
5. Cold boot the game and enter a fight.
6. Confirm character proportions and horizontal field of view still match the successful v0.3 result.
7. Confirm the gameplay camera is visibly wider than the original camera.

## Camera A/B test

To verify that the camera patch is independently controlled by the plugin, keep all settings unchanged and test these values one at a time with a cold boot between tests:

```ini
CameraPreset = 0
CameraPreset = 1
CameraPreset = 2
CameraPreset = 3
```

Expected order from narrowest to widest:

```text
Original < Slightly Wider < Wider < Widest
```

The v0.4 default is `CameraPreset = 2`.

## Disable camera without disabling ultrawide

Use:

```ini
EnableCamera = 0
```

The 3D 20:9 aspect correction should remain active while the gameplay camera returns to its original behavior.

## Diagnostic logging

Verbose logging is off by default for the public beta.

If troubleshooting, change:

```ini
DebugLogging = 0
```

to:

```ini
DebugLogging = 1
```

Then fully restart PPSSPP and reproduce the issue.

Expected header:

```text
=== Tekken6.PPSSPP.UltrawideFix v0.4 ===
Plugin module_start reached successfully
```

A successful initial cycle should include messages equivalent to:

```text
3D: first CWCheat-order cycle patched all four sites
Camera: first CWCheat-order cycle patched the camera site
```

The camera site is:

```text
0x0895350C
```

and the default v0.4 target word is:

```text
0x3C013F82
```

## Important PPSSPP JIT note

PPSSPP may place internal `0x68xxxxxx` emuhack markers into guest code when JIT blocks are compiled. These are not Tekken restoring the original instruction.

The plugin deliberately invalidates each relevant code range before inspecting/writing it, preserving the behavior that made v0.3 successful.

## What to report

For a useful v0.4 test report, include:

```text
PPSSPP version:
Platform/device:
Display aspect ratio:
ForceAspectRatio:
CameraPreset:
3D aspect: correct / incorrect
Camera: original / slightly wider / wider / widest / no visible change
HUD/UI: note any unexpected regression
```

If `DebugLogging = 1`, also include:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log
```

Screenshots from the same fight/camera position are especially useful when comparing camera presets.

## HUD status

No HUD/UI/menu correction is active in v0.4. If HUD elements remain stretched or incorrectly positioned on ultrawide displays, that is a known limitation rather than a failed v0.4 camera/3D installation.
