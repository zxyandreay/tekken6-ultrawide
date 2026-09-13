# Tekken 6 PPSSPP Ultrawide

Automatic 3D aspect-ratio correction for **Tekken 6 USA (`ULUS10466`)** on **PPSSPP**, with optional gameplay camera presets available from PPSSPP's normal Cheat menu.

![Tekken 6 PPSSPP ultrawide 20:9 aspect ratio with Widest camera preview](assets/tekken6-aspect-camera-preview.png)

> **Screenshot settings:** 20:9 display + `Camera - Widest`

## v1.1.0

v1.1.0 replaces the old manual aspect-ratio CWCheats with a PRX plugin that reads PPSSPP's current landscape display aspect automatically.

You no longer need to choose a 21:9, 20:9, 19.5:9, 16:10, or other matching aspect entry yourself. Keep PPSSPP on **Stretch**, enable the plugin, and the 3D projection is corrected for the display aspect PPSSPP reports.

Camera selection remains separate as lightweight CWCheats, so users can change camera framing directly from the Cheat menu without editing a plugin configuration file.

## Installation

1. Open the [latest release](https://github.com/zxyandreay/tekken6-ultrawide/releases/latest) and download the v1.1.0 ZIP.
2. If you already have `PSP/Cheats/ULUS10466.ini` with unrelated custom cheats, back it up first.
3. Extract the ZIP into your PPSSPP memory-stick root so the included `PSP` folder merges with your existing `PSP` folder.
4. Enable **Tekken 6 Ultrawide** in PPSSPP's plugin manager if it is not enabled automatically.
5. Go to **Settings → Graphics → Display layout & effects** and enable **Stretch**.
6. Cold-boot **Tekken 6 USA (`ULUS10466`)**.
7. Do not enable the legacy v1.0.0 manual aspect-ratio CWCheats at the same time as the plugin.

## Camera options

The included `PSP/Cheats/ULUS10466.ini` contains camera presets only. Enable at most one:

| Cheat entry | Effect |
| --- | --- |
| `Camera - Original (Default)` | Stock gameplay camera |
| `Camera - Slightly Wider` | Small increase in visible play area |
| `Camera - Wider` | Wider gameplay framing |
| `Camera - Widest` | Maximum included camera preset |

Camera cheats are optional. The automatic aspect plugin works independently of them.

## How automatic aspect correction works

Tekken 6 constructs its stock `16:9` projection constant in four validated code paths. The plugin asks PPSSPP for the current landscape display aspect, converts that float into the same MIPS `lui` / `ori` constant pair used by the game, patches those four projection paths, and invalidates the relevant instruction-cache ranges.

The plugin accepts landscape aspect values from `1.0` through `4.0`, so it is not limited to a hardcoded list of phone or monitor ratios.

## Compatibility

- **Game:** Tekken 6 USA
- **Game ID:** `ULUS10466`
- **Emulator:** PPSSPP with PRX plugin support
- **Orientation:** landscape

Other regional versions are not currently supported.

## Limitations

- v1.1.0 corrects the game's **3D projection**.
- Tekken 6's original 2D HUD and menu layout is not independently repositioned or corrected yet.
- The package's `ULUS10466.ini` contains camera presets only; if you maintain other custom cheats for the game, merge them manually after backing up your file.

## Previous release

v1.0.0 used manual CWCheat aspect-ratio presets plus camera presets. That release remains available in GitHub Releases for users who prefer the original cheat-only approach.

## Development

The source for the PRX plugin lives under `plugin/`. Automatic aspect math has a small host-side test in `tools/test_aspect_math.c`. The device-side ABI investigation that led to the working automatic build is preserved in `research/v1.1.0-auto-aspect-abi.md`.
