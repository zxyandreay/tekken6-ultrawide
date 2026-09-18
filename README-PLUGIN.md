# Tekken 6 Ultrawide v1.2.0

v1.2.0 adds automatic battle-HUD correction on top of the automatic 3D aspect-ratio correction introduced in v1.1.0 for **Tekken 6 USA (`ULUS10466`)** on PPSSPP.

## What v1.2.0 does

- Automatically reads PPSSPP's current landscape display aspect ratio.
- Corrects Tekken 6's 3D projection without requiring a manual aspect-ratio cheat.
- Dynamically corrects the persistent fight HUD so it keeps its intended proportions and anchoring on widescreen displays.
- Preserves both HP fills, player-side HUD, timer, round indicators, winner effects, character labels, Practice HUD text, and Gold Rush battle labels.
- Keeps optional camera framing as normal CWCheat presets in PPSSPP's Cheats menu.
- Requires no plugin configuration editing.

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

The automatic aspect/HUD plugin works independently of the camera preset.

## Compatibility

- Game: Tekken 6 USA
- Game ID: `ULUS10466`
- Emulator: PPSSPP with PRX plugin support
- Orientation: landscape

Other regional releases are not currently supported.

## Validation and limitations

The v1.2.0 PRX was validated on-device across Arcade, Story, Ghost Battle, Practice, and Gold Rush, including HP fill, mode-specific battle text, and replacement-texture/font behavior. The HUD coefficients are derived from PPSSPP's reported aspect at runtime rather than selected from a fixed list. The validated target device used an approximately 20:9 presentation; other aspect ratios were not independently device-tested during this release cycle.

v1.2.0 focuses on the persistent fight HUD. Some menu, character-select, pause, or transient pre/post-battle UI may still retain the game's original layout behavior.
