# Tekken 6 Ultrawide v1.1.0

This release replaces the old manual aspect-ratio CWCheats with an automatic PPSSPP PRX plugin for **Tekken 6 USA (`ULUS10466`)**.

## What v1.1.0 does

- Automatically reads PPSSPP's current landscape display aspect ratio.
- Corrects Tekken 6's 3D projection without requiring a matching aspect-ratio cheat.
- Keeps camera preference separate as normal CWCheat presets.
- Requires no plugin configuration file editing.

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
5. Cold-boot Tekken 6 USA (`ULUS10466`). Do not enable any legacy v1.0.0 aspect-ratio CWCheats.

The 3D scene should now use PPSSPP's current landscape display aspect automatically.

## Camera presets

Camera settings remain optional and are selected from PPSSPP's normal Cheat menu. Enable at most one:

- `Camera - Original (Default)`
- `Camera - Slightly Wider`
- `Camera - Wider`
- `Camera - Widest`

No plugin INI editing is required for camera selection.

## Compatibility

- Game: Tekken 6 USA
- Game ID: `ULUS10466`
- Emulator: PPSSPP with PRX plugin support
- Orientation: landscape

Other regional releases are not currently supported.

## Known limitation

v1.1.0 corrects the **3D projection**. Tekken 6's original 2D HUD and menu layout is still rendered for the stock presentation and is not independently repositioned in this release.

## Development note

The automatic-aspect path was validated on-device after isolating a temporary non-PSPDEV test-build ABI issue around six-argument `sceIoDevctl` calls. The investigation is preserved in `research/v1.1.0-auto-aspect-abi.md`.
