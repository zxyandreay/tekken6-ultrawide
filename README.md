# Tekken 6 PPSSPP Ultrawide

Automatic **3D + gameplay HUD aspect-ratio correction** for **Tekken 6 USA (`ULUS10466`)** on **PPSSPP**, with optional gameplay camera presets in PPSSPP's normal Cheat menu.

![Tekken 6 PPSSPP ultrawide 20:9 aspect ratio with Widest camera preview](assets/tekken6-aspect-camera-preview.png)

> **Screenshot settings:** 20:9 display + `Camera - Widest`

## v1.2.1

v1.2.1 is a maintenance release for the AutoHUD implementation introduced in v1.2.0.

It fixes the animated winner/earned-round glow so the spinning effect follows the newly earned orb for **both P1 and P2 on first and later wins**, while preserving the existing automatic 3D/HUD correction, fast-forward, and replacement-texture/font compatibility.

### AutoHUD coverage

v1.2.1 corrects:

- HP shells and both colored HP fill layers
- player-side strips and rank badges
- character-name anchoring
- round timer
- persistent and newly earned round markers
- animated winner/earned-round glow across first and later wins
- Practice infinite timer and combo/damage text
- Gold Rush `REWARD` and `ATTACK VARIATION` labels
- mode-specific fight HUD used by Arcade, Story, Ghost Battle, Practice, and Gold Rush
- custom replacement textures/fonts

Camera framing remains optional and separate through CWCheat presets.

## Installation

1. Open the [latest release](https://github.com/zxyandreay/tekken6-ultrawide/releases/latest) and download **`Tekken6-Ultrawide-v1.2.1.zip`**.
2. Back up `PSP/Cheats/ULUS10466.ini` first if it contains unrelated custom cheats you want to keep.
3. Extract the ZIP into the PPSSPP memory-stick root so the included `PSP` folder merges with your existing `PSP` folder.
4. Enable **Tekken 6 Ultrawide** in PPSSPP's plugin manager if it is not enabled automatically.
5. Go to **Settings → Graphics → Display layout & effects** and enable **Stretch**.
6. Cold-boot **Tekken 6 USA (`ULUS10466`)**.
7. Do not enable legacy v1.0.0 manual aspect-ratio CWCheats at the same time as the plugin.

The plugin is installed at:

```text
PSP/PLUGINS/Tekken6Ultrawide/Tekken6Ultrawide.prx
```

## Camera options

The included `PSP/Cheats/ULUS10466.ini` contains camera presets only. Enable at most one:

| Cheat entry | Effect |
| --- | --- |
| `Camera - Original (Default)` | Stock gameplay camera |
| `Camera - Slightly Wider` | Small increase in visible play area |
| `Camera - Wider` | Wider gameplay framing |
| `Camera - Widest` | Maximum included camera preset |

Camera cheats are optional. Automatic aspect/HUD correction works independently of them.

## How automatic correction works

Tekken 6's stock presentation is based on a 16:9 logical frame. The plugin asks PPSSPP for the current landscape display aspect and derives the correction at runtime rather than selecting from a fixed list of phone or monitor ratios.

The 3D projection is patched to PPSSPP's reported display aspect. For HUD paths that need correction, AutoHUD applies aspect-derived horizontal scaling and left/center/right anchoring while preserving vertical geometry and mode-specific behavior.

## Validation

v1.2.1 was tested on-device across the existing v1.2.0 gameplay coverage:

- Arcade
- Story
- Ghost Battle
- Practice
- Gold Rush

The maintenance validation additionally confirmed:

- P1 first and later winner-glow slots
- P2 first and later winner-glow slots
- visible spinner animation on the newly lit orb
- HP shell/fill and persistent round markers
- character names, ranks, side strips, and timer
- Practice and Gold Rush font/HUD corrections
- custom replacement textures/fonts
- fast-forward

The implementation is aspect-derived rather than fixed to 20:9. Testing was performed on an approximately 20:9 display; other display ratios have not yet been independently tested.

## Compatibility

- **Game:** Tekken 6 USA
- **Game ID:** `ULUS10466`
- **Emulator:** PPSSPP with PRX plugin support
- **Orientation:** landscape

Other regional versions are not currently supported.

## Limitations

- The plugin focuses on gameplay HUD correction. Some menu, character-select, pause, or transient pre/post-battle UI may retain the game's original layout behavior.
- The package's `ULUS10466.ini` contains camera presets only. Merge it manually if you maintain other custom cheats.
- Other display ratios have not yet been independently tested.

## Previous releases

- **v1.2.0:** introduced AutoHUD correction for the persistent fight HUD.
- **v1.1.0:** automatic 3D aspect correction; original 2D HUD remained uncorrected.
- **v1.0.0:** manual aspect-ratio CWCheats plus camera presets.

## Technical notes

The AutoHUD reverse-engineering process is documented in [`research/v1.2.0-autohud.md`](research/v1.2.0-autohud.md).

The v1.2.1 maintenance/optimization work, including the winner-glow root-cause analysis and accepted renderer checkpoints, is documented in [`research/renderer-optimization/`](research/renderer-optimization/).
