# Tekken 6 PPSSPP Ultrawide Fix — first plugin test

Last updated: 2026-09-03

## What is verified vs experimental

### Verified component: 3D aspect patch

The plugin patches the same four ULUS10466 aspect-dispatch locations already proven by the known-good 20:9 CWCheat:

- `0x08945F10`
- `0x08946794`
- `0x08946BC8`
- `0x08947D90`

At each location it verifies the expected MIPS instruction pair (`lui at,...` + `ori at,at,...`) before writing the requested aspect float. The initial POCO F5 configuration uses exact `20:9`.

This part is expected to reproduce the existing correct 3D ultrawide behavior without requiring CWCheat.

### Experimental component: HUD correction

The current repository still does **not** prove the live HUD ownership path. The first plugin therefore exposes two isolated Warriors-style candidate groups instead of pretending the HUD is solved.

`HUDMode = 1` patches three `480.0` LUI loads in the higher-ranked general 2D/render-descriptor candidate around `0x08A3916C–0x08A396D8`:

- `0x08A39288`
- `0x08A392F4`
- `0x08A39360`

For a 20:9 display, the plugin changes those 480.0 logical-width loads to exactly 600.0. This is the mathematically correct virtual width for preserving a 16:9 HUD inside a 20:9 stretched output, but it remains an ownership hypothesis until visually validated.

`HUDMode = 2` isolates the second candidate around `0x08AA62D8–0x08AA655C`:

- `0x08AA6314`
- `0x08AA63B8`
- `0x08AA64C0`

This second family appears mask-like and is intentionally kept separate because it may correspond to fades, masks, clipping, or overlays rather than ordinary HUD.

`HUDMode = 3` applies both groups and should only be used after the isolated tests.

## Installation

Download the build artifact from the GitHub Actions `Build PPSSPP plugin` workflow and extract it into the PPSSPP memstick root. The resulting files should be:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

The manifest is restricted to USA Tekken 6 `ULUS10466`.

## PPSSPP setup for the POCO F5 test

1. Disable the existing Tekken 6 20:9 CWCheat. The plugin should be the only aspect patch during the test.
2. Keep PPSSPP Display Layout set to `Stretch`, matching the previous verified test setup.
3. The supplied package starts safely with HUD correction disabled:

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1
HUDMode = 0
HUDVirtualWidth = 600
DebugLogging = 1
```

4. Fully close and relaunch Tekken 6 after every configuration change. The PRX patches game memory at boot.

## Test sequence

### Test 1 — plugin 3D only

Leave:

```ini
HUDMode = 0
```

Expected result: the 3D scene should look the same as the known-good 20:9 CWCheat while the HUD remains stretched. If the 3D scene is not correct, stop HUD testing and send the plugin log.

### Test 2 — candidate group A

Set:

```ini
HUDMode = 1
```

Check at minimum:

- health bars and health fill,
- timer / round indicators,
- player names and icons,
- character-select UI,
- pause menu,
- normal menu panels,
- dark pause overlay / fades.

Useful outcomes are not limited to a perfect fix. Classification is valuable:

- If ordinary HUD becomes narrower/correct while full-screen overlays remain full-screen, group A is a strong Warriors-style HUD path.
- If only some HUD categories change, the path is useful but needs caller/category separation.
- If dark overlays shrink or stop covering the whole display, the path mixes HUD and full-screen masks and must be split in the final plugin.
- If nothing visible changes, group A is not the live visible HUD path and should be rejected.
- If corruption occurs, immediately return to `HUDMode = 0`; no persistent game data is modified.

### Test 3 — candidate group B

Only after recording Test 2, set:

```ini
HUDMode = 2
```

This specifically helps determine whether the second family controls masks/overlays rather than ordinary HUD.

### Test 4 — both groups

Use `HUDMode = 3` only if Tests 2 and 3 show complementary behavior. Do not use this as the first test because it would hide which path owns each visual category.

## Log file

With `DebugLogging = 1`, inspect:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log
```

The plugin records whether each verified 3D site and each experimental HUD candidate site matched its expected instruction shape and was patched.

If a signature does not match, the plugin skips that write instead of blindly patching memory.

## Reliability statement

The current repository findings are sufficient to make the **3D plugin path reliable for this exact ULUS10466 executable**, because it directly reproduces a user-verified CWCheat and validates each instruction before writing.

The repository findings are **not yet sufficient to call the HUD fix reliable**. The HUD portion of this build is deliberately a controlled runtime experiment that tests the two best current Warriors-style candidates with isolated modes and logging. A final `FixHUD = 1` implementation should only replace these diagnostic modes after one candidate is visually and structurally confirmed.
