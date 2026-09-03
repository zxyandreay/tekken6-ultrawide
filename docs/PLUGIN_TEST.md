# Tekken 6 PPSSPP Ultrawide Fix — v0.2 runtime diagnostic

Last updated: 2026-09-03

## Why this build exists

The first PRX build did **not** reproduce the user's known-good CWCheat result: both 3D and HUD/UI still appeared stretched with `HUDMode` off and on.

Therefore v0.2 removes the HUD experiment from the test path and answers one question first:

> Is PPSSPP actually starting the PRX, and are the exact four known-good Tekken 6 aspect instructions being found, written, read back, and kept active in the live game module?

Do not use v0.2 to evaluate HUD correction. HUD work resumes only after this test proves the PRX 3D path.

## Install

Extract the package into the active PPSSPP memstick root so these files exist:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

The manifest supports:

```text
ULUS10466
```

only.

## Configuration

Use the supplied INI unchanged:

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1
DebugLogging = 1
```

## PPSSPP test conditions

1. Disable the old Tekken 6 widescreen CWCheat.
2. Keep PPSSPP Display Layout = `Stretch`.
3. Make sure PPSSPP plugins are enabled for the game.
4. Fully close Tekken 6 / PPSSPP before the test.
5. For this diagnostic, do **not** manually load a savestate.
6. If PPSSPP is configured to auto-load a savestate, disable that for this test.
7. Launch Tekken 6 normally.

PPSSPP should normally display a short `Loaded plugin: ...` message when a PRX plugin starts successfully.

## What v0.2 does differently

### Fresh startup marker

At the start of `module_start`, it deletes the prior log and immediately creates a new log containing:

```text
=== Tekken6.PPSSPP.UltrawideFix v0.2 runtime diagnostic ===
Plugin module_start reached successfully
```

If a fresh log with this header does not appear, stop. The plugin is not starting and no Tekken rendering conclusion should be drawn.

### Live module discovery

The PRX enumerates PSP modules and logs their names, text addresses, and text sizes.

It searches live module text for the exact verified layout of the four Tekken aspect case-0 instruction pairs.

The verified relative spacing is:

```text
site 1 +0x0000
site 2 +0x0884
site 3 +0x0CB8
site 4 +0x1E80
```

Original pair:

```text
0x3C013FE3
0x34218E39
```

20:9 pair:

```text
0x3C01400E
0x342138E4
```

### Exact write/readback

For every accepted site, v0.2 writes the 20:9 pair, flushes the corresponding data-cache range, invalidates the exact PPSSPP/JIT instruction range, and immediately reads both instructions back.

A fully successful runtime patch should include four lines resembling:

```text
3D patched/readback: 0x........ = 0x3C01400E 0x342138E4
```

followed by:

```text
3D: all four sites patched and immediate readback verified
```

### Early-boot monitor

The plugin checks the sites for roughly three seconds after startup.

If something restores or changes the code, the log will contain:

```text
3D monitor: patch was reverted/changed; reapplying
```

If the target instructions remain stable, the end should contain:

```text
3D monitor: target instructions remained present through early boot
```

## What to send back

After the test, send this file:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
Tekken6.PPSSPP.UltrawideFix.log
```

Also say whether the 3D scene now visually matches the known-good CWCheat.

## How the result will be interpreted

### A. No fresh log exists

The PRX never started. Investigate active memstick path, PPSSPP plugin setting, DISC_ID matching, or load failure.

### B. Log starts, but no four-site signature is found

The live runtime executable/module layout differs from what the static EBOOT analysis predicted, or the main module is not visible when expected. The logged module list and known-address pre-scan values will tell us which.

### C. Four writes succeed, then are reverted

Startup ordering, state loading, or another runtime action is undoing the patch. The monitor will prove it rather than leaving us to guess.

### D. Four writes/readbacks succeed and remain stable, but 3D still looks stretched

This is a deeper PPSSPP/runtime issue. The next step is to compare the PRX code-write/JIT path against PPSSPP's CWCheat implementation and verify which projection path is actually executing.

### E. 3D finally matches the CWCheat

The PRX runtime foundation is proven. Then resume the real goal: identify and implement Tekken's separate HUD-scale path analogous to The Warriors Fusion Fix.

## HUD note

There is intentionally no `HUDMode` in the v0.2 package INI.

The previous Group A/B paths remain research hypotheses, not a working HUD fix. Testing them before the PRX 3D path is verified would mix two different problems and produce ambiguous results.
