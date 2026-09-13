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

Device testing established the following sequence:

- `v1.1.0-dev1/dev2`: automatic aspect candidates failed to correct the 3D scene.
- `v1.1.0-dev3`: removed the PPSSPP aspect-query path and hardcoded the proven 20:9 projection value. This worked on-device.
- `v1.1.0-dev4`: kept the exact dev3 PRX and moved camera selection into a camera-only CWCheat file. This also worked on-device.
- `v1.1.0-dev5`: restores automatic PPSSPP display-aspect detection with the failed test-build ABI issue corrected.

The dev1/dev2 failure is now understood. PPSSPP's HLE wrapper for `sceIoDevctl` reads six integer/pointer arguments from PSP registers `$a0`, `$a1`, `$a2`, `$a3`, `$t0`, and `$t1`. The temporary non-PSPDEV build path used generic MIPS o32, which placed arguments 5 and 6 on the stack instead. As a result, PPSSPP did not receive the `GET_ASPECT_RATIO` output pointer/length correctly.

The dev5 diagnostic build adds a tiny ABI bridge that copies generic-o32 stack arguments 5/6 into `$t0/$t1` before calling the imported `sceIoDevctl` stub. Production builds should not need this bridge: the canonical repository source remains normal PSPSDK C and is intended to be built with PSPDEV.

The successful dev3/dev4 tests already confirm:

- the four ULUS10466 projection addresses are correct;
- direct PRX memory patching works;
- the 20:9 projection words `0x3C01400E / 0x342138E4` behave identically to the proven CWCheat;
- camera CWCheats can remain fully separate from the PRX.

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

1. If `PSP/Cheats/ULUS10466.ini` already contains unrelated custom cheats you want to keep, back it up before installing. PPSSPP uses one game-specific cheat INI for ULUS10466.
2. Copy the package contents into the PPSSPP memory-stick root.
3. Enable `Tekken 6 Ultrawide Auto Aspect` in PPSSPP's plugin manager if needed.
4. Keep PPSSPP display scaling set to **Stretch**.
5. Open PPSSPP's Cheats menu for Tekken 6 and enable exactly one camera preset if you want a non-default camera.
6. Do not combine the v1.1 plugin with the old v1.0.0 manual aspect-ratio CWCheats.

Target game: Tekken 6 USA (`ULUS10466`).
