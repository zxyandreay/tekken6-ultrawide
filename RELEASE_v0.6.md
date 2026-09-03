# Tekken 6 PPSSPP Ultrawide Fix v0.6 beta

v0.6 replaces the failed v0.5 HUD-width experiment with the clarified target architecture: **3D stays ultrawide, while the complete flat/2D presentation is kept at native PSP proportions in a centered safe area.** It also removes the plugin manifest's forced 93 MB RAM override, which was an unnecessary compatibility risk for replacement-texture hashing and game allocations.

## Major changes

### Native PSP 2D safe area

v0.6 does **not** reposition individual health bars, menus, prompts, or HUD elements. Tekken's authored UI coordinates remain unchanged.

Static tracing identified the live viewport call at runtime `0x08864B88` as part of a flat/surface render path that is separate from the nearby perspective and generic orthographic setup paths. The plugin redirects only that viewport call through a small MIPS wrapper.

The wrapper keeps Y/height/depth unchanged and applies one centered horizontal viewport transform:

```text
nativePSPAspect = 480 / 272
safeScale       = nativePSPAspect / targetAspect
safeWidth       = originalWidth * safeScale
safeX           = originalX + (originalWidth - safeWidth) / 2
```

For the supplied 20:9 configuration:

```text
safeScale = 27/34 = 0.794117647...
```

This is designed to cancel PPSSPP Stretch's horizontal distortion for flat graphics while leaving the validated 3D perspective patch ultrawide.

New option:

```ini
EnableNative2DSafeArea = 1
```

Set it to `0` to return to the v0.4/v0.5-style stretched 2D presentation while keeping 3D and camera fixes active.

### Replacement-texture compatibility / memory correction

Previous plugin packages contained:

```ini
memory = 93
```

PPSSPP interprets that manifest field as a request to raise the game's emulated RAM size, not simply as a small private allocation for this PRX. The ultrawide plugin does not require extended RAM.

v0.6 removes the `memory` override entirely so Tekken runs with PPSSPP's normal game-memory configuration. This removes a major allocation-layout variable that could alter dynamically generated UI texture contents/padding/hashes and cause selective HD replacement textures to miss.

The plugin itself does not edit texture packs or replacement keys.

### Retired v0.5 HUD experiment

The v0.5 `0x08A392F0` / descriptor `+0x28` logical-width hook is removed. Device testing showed that it did not correct the battle HUD, so it is no longer part of the runtime code or INI.

### Preserved behavior

The following validated addresses/values remain unchanged:

- 3D aspect sites: `0x08945F10`, `0x08946794`, `0x08946BC8`, `0x08947D90`
- gameplay camera site: `0x0895350C`
- default camera: `CameraPreset = 2` / Wider (`0x3F82`)
- low-churn PPSSPP JIT maintenance introduced in v0.5

## Supplied configuration

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

## What needs device validation

CI verifies the static signatures, analysis tools, PSPSDK build, and release package. It cannot verify the final visual result on the POCO F5.

Please specifically compare:

- battle health bars, names, timer, round/rage indicators,
- pause menu and bottom button prompts,
- character/stage select,
- main/options/results menus,
- full flat backgrounds/overlays,
- the exact HD replacement textures that fell back with v0.4/v0.5,
- 3D field of view and CameraPreset 2 against the known v0.4 baseline.

A cold PPSSPP restart is strongly recommended because v0.6 changes the plugin memory manifest as well as runtime code.

## Compatibility

- Game: Tekken 6 USA `ULUS10466`
- Primary development target: PPSSPP, 20:9, Display Layout = Stretch
- Other regions are not supported yet.
- Disable older CWCheats that patch the same 3D aspect/camera addresses.
