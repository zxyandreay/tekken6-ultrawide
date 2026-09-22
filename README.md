# Tekken 6 PPSSPP Ultrawide

Automatic **3D + gameplay HUD aspect-ratio correction** for **Tekken 6 USA (`ULUS10466`)** on **PPSSPP**, with optional gameplay camera presets.

![Tekken 6 PPSSPP ultrawide 20:9 aspect ratio with Widest camera preview](assets/tekken6-aspect-camera-preview.png)

> **Screenshot:** 20:9 display + `Camera - Widest`

## About

Tekken 6 was designed around a 16:9 presentation. On wider displays, simply stretching the image can distort the 3D view and gameplay HUD.

This plugin reads PPSSPP's current landscape display aspect ratio at runtime and applies automatic correction to the game's 3D projection and supported gameplay HUD paths.

The HUD correction is **aspect-derived**, not hard-coded to a specific display ratio.

## Features

- Automatic 3D aspect-ratio correction
- Automatic gameplay HUD correction
- Corrected HP bars and fills
- Player-side HUD and rank badge anchoring
- Character-name anchoring
- Round timer and round markers
- Animated winner/earned-round effects
- Practice mode HUD text
- Gold Rush battle labels
- Support for tested custom replacement textures/fonts
- Optional gameplay camera presets through PPSSPP's Cheat menu
- No manual aspect-ratio cheat selection required

## Installation

1. Open the [latest release](https://github.com/zxyandreay/tekken6-ultrawide/releases/latest).
2. Download the release ZIP.
3. Back up `PSP/Cheats/ULUS10466.ini` first if it contains unrelated custom cheats.
4. Extract the ZIP into the PPSSPP memory-stick root so the included `PSP` folder merges with your existing `PSP` folder.
5. Enable **Tekken 6 Ultrawide** in PPSSPP's plugin manager if needed.
6. Go to **Settings → Graphics → Display layout & effects** and enable **Stretch**.
7. Cold-boot **Tekken 6 USA (`ULUS10466`)**.

The plugin is installed at:

```text
PSP/PLUGINS/Tekken6Ultrawide/Tekken6Ultrawide.prx
```

Do not use legacy manual aspect-ratio CWCheats at the same time as the automatic plugin.

## Camera presets

The included `PSP/Cheats/ULUS10466.ini` contains optional camera presets:

| Preset | Effect |
| --- | --- |
| `Camera - Original (Default)` | Stock gameplay camera |
| `Camera - Slightly Wider` | Slightly wider gameplay framing |
| `Camera - Wider` | Wider gameplay framing |
| `Camera - Widest` | Widest included gameplay framing |

Enable at most one camera preset.

Camera selection is separate from automatic 3D/HUD aspect correction.

## How it works

The plugin queries PPSSPP for the current landscape display aspect ratio and derives the required correction at runtime.

The 3D projection is adjusted to the reported display aspect. Supported HUD elements use aspect-derived horizontal scaling and semantic left/center/right anchoring while preserving their intended vertical geometry and game behavior.

## Compatibility

- **Game:** Tekken 6 USA
- **Game ID:** `ULUS10466`
- **Emulator:** PPSSPP with PRX plugin support
- **Orientation:** Landscape

Other regional versions are not currently supported.

## Scope and limitations

The project focuses primarily on the gameplay presentation and battle HUD.

Some menu, character-select, pause, or transient pre/post-battle UI may retain the game's original layout behavior.

The implementation is designed to adapt to the current display aspect ratio. Development and device validation have primarily been performed on an approximately 20:9 display, so other ratios may need additional real-device validation.

If you maintain custom cheats, merge the included camera entries into your existing `ULUS10466.ini` instead of overwriting unrelated entries.

