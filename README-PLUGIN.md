# Tekken 6 Ultrawide v1.2.1

v1.2.1 is a maintenance release for **Tekken 6 USA (`ULUS10466`)** on PPSSPP. It preserves the automatic 3D + AutoHUD correction introduced in v1.2.0 while fixing the animated winner/earned-round glow across first and later wins.

## What v1.2.1 does

- Automatically reads PPSSPP's current landscape display aspect ratio.
- Corrects Tekken 6's 3D projection without requiring a manual aspect-ratio cheat.
- Dynamically corrects the persistent fight HUD with aspect-derived horizontal scaling and semantic anchoring.
- Corrects HP shells/fills, player-side HUD, rank badges, timer, round markers, character names, Practice HUD text, and Gold Rush labels.
- Fixes the **spinning winner/earned-round glow** so it follows the newly earned orb for both P1 and P2 on first and later wins.
- Preserves custom replacement textures/fonts tested during development.
- Preserves PPSSPP fast-forward behavior.
- Keeps optional camera framing as normal CWCheat presets.

The package intentionally contains **no manual aspect-ratio CWCheats**, avoiding conflicts with the automatic plugin.

## Package layout

```text
PSP/
├── Cheats/
│   └── ULUS10466.ini
└── PLUGINS/
    └── Tekken6Ultrawide/
        ├── Tekken6Ultrawide.prx
        └── plugin.ini
README-PLUGIN.md
```

## Installation

1. Back up your existing `PSP/Cheats/ULUS10466.ini` first if it contains unrelated custom cheats you want to keep.
2. Extract the package into the PPSSPP memory-stick root so the included `PSP` folder merges with your existing `PSP` folder.
3. Enable **Tekken 6 Ultrawide** in PPSSPP's plugin manager if it is not enabled automatically.
4. Go to **Settings → Graphics → Display layout & effects** and enable **Stretch**.
5. Cold-boot Tekken 6 USA (`ULUS10466`).
6. Do not enable legacy v1.0.0 manual aspect-ratio CWCheats at the same time as this plugin.

## Camera presets

The included `PSP/Cheats/ULUS10466.ini` contains optional camera presets. Enable at most one:

- `Camera - Original (Default)`
- `Camera - Slightly Wider`
- `Camera - Wider`
- `Camera - Widest`

Automatic 3D/HUD correction works independently of the camera preset.

## Compatibility

- Game: Tekken 6 USA
- Game ID: `ULUS10466`
- Emulator: PPSSPP with PRX plugin support
- Orientation: landscape

Other regional releases are not currently supported.

## Validation and limitations

The v1.2.1 PRX was validated on-device across the existing v1.2.0 gameplay/HUD coverage. Validation also explicitly covered P1/P2 first and later winner-glow slots, visible spinner animation, custom replacement textures/fonts, and fast-forward.

The HUD coefficients are derived from PPSSPP's reported aspect at runtime rather than selected from a fixed list. The validated target device used an approximately 20:9 presentation; other aspect ratios were not independently device-tested during this release cycle.

The plugin focuses on gameplay HUD correction. Some menu, character-select, pause, or transient pre/post-battle UI may retain the game's original layout behavior.
