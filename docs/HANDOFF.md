# Handoff

Last updated: 2026-09-03

## Current Objective

Validate the first real PPSSPP PRX for Tekken 6 USA (`ULUS10466`) on the target POCO F5, then use the results to convert the experimental HUD candidate modes into a proper Warriors-style HUD fix.

The 3D side is already tied to the known-good 20:9 CWCheat. The unresolved question is still HUD ownership: which live 2D/render-state path controls ordinary HUD, and which path controls masks/overlays.

## Verified So Far

### Input and executable

- `ULUS10466_EBOOT.BIN` is a decrypted 32-bit little-endian MIPS ELF executable.
- Load segment:
  - file offset `0x00001018`
  - virtual address `0x08804018`
  - file size `0x003F62A8`
  - memory size `0x0045F02C`
- Known-good CWCheat 3D ultrawide behavior has already been validated by the user on a POCO F5.

### 3D aspect system

Verified runtime aspect-dispatch patch sites:

- `0x08945F10`
- `0x08946794`
- `0x08946BC8`
- `0x08947D90`

Each site is a `lui at,...` + `ori at,at,...` pair that constructs the aspect float used by the working 3D patch.

Perspective projection builder: `0x08ACA6C4`.

### Rejected generic HUD hypothesis

Generic orthographic builder: `0x08ACA990`.

Three direct 480x272 setup paths A/B/C were changed independently from 480 to 600 and produced no visible HUD/UI/menu change in user testing. Do not return to those as the primary HUD solution.

### Warriors reference

The Warriors PPSSPP Fusion Fix uses two distinct runtime corrections:

1. one game/perspective aspect injection,
2. one separate HUD-scale injection.

This is the architecture to emulate, not a single global 2D projection change.

See `docs/WARRIORS_ARCHITECTURE.md`.

## Current Plugin

Source:

```text
plugin/main.c
plugin/Makefile
plugin/exports.exp
plugin/package/plugin.ini
plugin/package/Tekken6.PPSSPP.UltrawideFix.ini
```

Build workflow:

```text
.github/workflows/build-plugin.yml
```

The workflow uses `pspdev/pspdev:latest` and packages a PPSSPP-ready plugin tree.

### Successful build

- Workflow: `Build PPSSPP plugin`
- Successful run: `2`
- Build commit: `10ea8db60763bb293f65694cf0c5a5bf3337d215`
- Artifact: `Tekken6-PPSSPP-UltrawideFix`

The PRX compiles successfully with current PSPSDK.

## Plugin Logic

### 3D

`Enable3D = 1` writes the selected aspect to the four verified 3D sites after checking the expected instruction shape.

Default test ratio:

```ini
ForceAspectRatio = 20:9
```

`auto` support is implemented through PPSSPP's `kemulator:` aspect query, but fixed 20:9 is used for the first POCO F5 validation to remove another variable.

### HUD experimental groups

`HUDMode = 1` tests Group A around `0x08A3916C–0x08A396D8` by changing these 480.0 LUI loads to exact 600.0:

- `0x08A39288`
- `0x08A392F4`
- `0x08A39360`

This is the recommended first HUD test because it ranked as the stronger general 2D/render-descriptor candidate.

`HUDMode = 2` isolates Group B around `0x08AA62D8–0x08AA655C`:

- `0x08AA6314`
- `0x08AA63B8`
- `0x08AA64C0`

Group B currently looks more mask-like and may affect fades/overlays rather than ordinary HUD.

`HUDMode = 3` applies both and should not be used until the isolated tests are recorded.

## Required User Test Sequence

1. Disable the existing Tekken 6 ultrawide CWCheat.
2. Keep PPSSPP Display Layout = Stretch.
3. Set `HUDMode = 0` and verify that the plugin alone reproduces the known-good 20:9 3D view.
4. Set `HUDMode = 1` and check health bars, timer, names/icons, character select, pause menu, menu panels, fades and the dark pause overlay.
5. Set `HUDMode = 2` separately and record what changes.
6. Only use `HUDMode = 3` if Groups A and B show complementary ownership.
7. Send `Tekken6.PPSSPP.UltrawideFix.log` after any unexpected result or signature mismatch.

Detailed instructions: `docs/PLUGIN_TEST.md`.

## Interpretation Rules

- If Group A corrects ordinary HUD proportions while overlays remain full-screen, promote Group A into the final `FixHUD` path.
- If Group A corrects HUD but shrinks full-screen fades/overlays, keep the path but add caller/context filtering in the final PRX.
- If Group B only changes masks/overlays, use it as a classification/exclusion signal rather than a normal HUD correction.
- If either group causes corruption, return to `HUDMode = 0`; no persistent game data is modified.
- If neither group changes the visible HUD, reject them and continue tracing higher-level descriptor/caller code. Do not go back to the already rejected generic orthographic paths.

## Current Reliability

- **3D:** high confidence for this exact ULUS10466 executable.
- **HUD:** controlled experiment only; not yet equivalent in reliability to The Warriors Fusion Fix.

The next useful development input is the user's visual classification of `HUDMode 0`, `1`, and `2`, plus the plugin log.
