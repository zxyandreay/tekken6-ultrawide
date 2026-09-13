# Tekken 6 Ultrawide — v1.1.0 development

The next release separates responsibilities to keep installation and day-to-day use simple:

- `Tekken6Ultrawide.prx` handles the 3D aspect-ratio correction.
- `PSP/Cheats/ULUS10466.ini` contains camera presets only.
- Camera selection stays in PPSSPP's normal Cheat menu; no plugin INI editing is required.
- The v1.1 package intentionally does not include manual aspect-ratio CWCheats, avoiding conflicts with the plugin.

## Camera presets

Enable only one camera preset at a time in PPSSPP:

- Camera - Original (Default)
- Camera - Slightly Wider
- Camera - Wider
- Camera - Widest

These retain the proven camera writes from the public v1.0.0 release at `0x1015350C`.

## Aspect-ratio development status

The first automatic-aspect candidates did not correct the 3D scene. Device testing of `v1.1.0-dev3` then isolated the issue by removing the PPSSPP emulator API/syscall path and hardcoding the already-proven 20:9 projection value.

`v1.1.0-dev3` worked on-device. That confirms:

- the four ULUS10466 projection addresses are correct;
- direct PRX memory patching works;
- the 20:9 projection words `0x3C01400E / 0x342138E4` behave identically to the proven CWCheat;
- the remaining work for the aspect plugin is reliable automatic display-aspect detection/build integration, not new Tekken projection addresses.

## Intended v1.1.0 package layout

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

## Usage

1. Copy the package contents into the PPSSPP memory-stick root.
2. Enable `Tekken 6 Ultrawide Auto Aspect` in PPSSPP's plugin manager if needed.
3. Keep PPSSPP display scaling set to **Stretch**.
4. Open PPSSPP's Cheats menu for Tekken 6 and enable exactly one camera preset if you want a non-default camera.
5. Do not combine the v1.1 plugin with the old v1.0.0 manual aspect-ratio CWCheats.

Target game: Tekken 6 USA (`ULUS10466`).
