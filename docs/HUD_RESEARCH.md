# HUD Research

Last updated: 2026-09-03

## Goal

Find the highest practical level where Tekken 6 converts logical HUD, UI, or screen-space coordinates into output coordinates, so HUD/UI proportions can be preserved independently from 20:9 3D rendering.

## Current Findings

### VERIFIED: generic orthographic projection builder

A generic orthographic projection builder has been identified at runtime address `0x08ACA990`.

Static analysis shows that it builds a conventional orthographic matrix from six floating-point bounds:

- X bounds: `$f12`, `$f13`
- Y bounds: `$f14`, `$f15`
- Z bounds: `$f16`, `$f17`

Its math uses coordinate sums/differences, scale terms equivalent to `2 / (max - min)`, and translation terms equivalent to `-(max + min) / (max - min)`.

This is separate from the perspective projection builder at `0x08ACA6C4` used by the known 3D aspect paths.

### VERIFIED: three direct 480x272 orthographic setup paths

Exactly three direct `jal` calls to `0x08ACA990` were identified in the file-backed game executable:

| Path | Right-X `480.0` load | Ortho call | Matrix-combine call | Evidence |
| --- | --- | --- | --- | --- |
| A | `0x08863230` | `0x08863258` | `0x0886327C` -> `0x08ACAB14` | Builds X `0..480`, Y `272..0` |
| B | `0x088634A0` | `0x088634E4` | `0x088634F4` -> `0x08ACAB14` | Builds X `0..480`, Y `272..0` |
| C | `0x08864494` | `0x088644B8` | `0x088644D4` -> `0x08ACAB14` | Builds X `0..480`, Y `272..0` |

All three therefore establish a PSP-native 480x272 logical 2D projection.

`tools/analyze_projection_paths.py` reproduces the direct perspective/ortho call scan and verifies the three original `480.0` instructions.

### VERIFIED USER TEST: isolated A/B/C tests produced no visible HUD/UI/menu change

On the target POCO F5 with PPSSPP Stretch and the known-good 20:9 3D patch enabled, the user tested `Diag - Ortho Path A 600-wide`, `Path B`, and `Path C` independently.

Observed result:

- Path A: no visible change in HUD/UI/menus.
- Path B: no visible change in HUD/UI/menus.
- Path C: no visible change in HUD/UI/menus.

This is an important negative result. A `480 -> 600` horizontal orthographic change should be visually obvious if the tested visible UI is actively rendered through that projection path. Therefore the three direct `0x08ACA990` call sites should **not** be treated as the primary live HUD/UI path for the tested screens.

Possible explanations still to distinguish:

1. the three paths are used by other rendering categories not visited during the test,
2. they are initialization/utility/dead paths for normal fight/menu rendering,
3. Tekken's visible HUD uses pre-transformed/sprite geometry or a different matrix path,
4. a later transform overrides/neutralizes these matrices.

The next research phase should therefore pivot away from A/B/C and search more broadly for the live screen-space/sprite coordinate path.

### STRONG EVIDENCE: why the previous global HUD experiment broke overlays

A centered 16:9 safe area inside a 20:9 output has a virtual width of 600 logical units:

- `480 * (20 / 16) = 600`
- centered around original X center `240` gives bounds `[-60, 540]`

Earlier experiments changed broad 2D rendering behavior using this kind of safe-area math. The math itself can preserve ordinary 16:9 HUD proportions after a 20:9 final stretch.

However, a full-screen quad still authored from X `0..480` then occupies only the central 480 units of a 600-unit projection. This remains a useful explanation for the historical symptom where a dark pause overlay/fade stopped covering the full screen: ordinary HUD and full-screen overlays cannot necessarily receive the same treatment.

The new no-op A/B/C result means those three specific orthographic paths are not sufficient to explain the historical overlay behavior; another 2D/sprite path must still be identified.

### REJECTED as a first-line HUD target: `0x08864B74` path

A previous broad safe-area experiment also modified code around `0x08864B74`. Static disassembly shows that this path does **not** call the orthographic builder `0x08ACA990`; it calls a different routine at `0x08AC5BA8`.

It should not be included in a new HUD fix without separate evidence, but the distinct `0x08AC5BA8` path is now worth analyzing as a possible screen-space/sprite transform family because A/B/C did not affect visible UI.

## Superseded Diagnostic Strategy

`diagnostics/ULUS10466_ORTHO_PATH_TEST.ini` remains in the repository as a reproducible negative test artifact. It changes only the right X bound from `480.0` to `600.0` for one path at a time:

- Path A: CWCheat `0x20063230`, original word `0x3C0143F0`, diagnostic word `0x3C014416`
- Path B: CWCheat `0x200634A0`, original word `0x3C0143F0`, diagnostic word `0x3C014416`
- Path C: CWCheat `0x20064494`, original word `0x3C0143F0`, diagnostic word `0x3C014416`

The test has now served its purpose: none of the three paths visibly changed the tested HUD/UI/menu groups.

Do not spend further user time repeating A/B/C unless a newly identified screen specifically points back to one of them.

## New Static-Analysis Direction

Use `tools/find_screen_space_candidates.py` to scan the decrypted EBOOT for likely PSP logical screen constants and nearby code/call structure.

It searches for code/data related to:

- `480.0`, `272.0`
- `240.0`, `136.0`
- `512.0`, `320.0`
- `256.0`, `160.0`
- corresponding small integer immediates

The report is intentionally broad. Every hit remains a candidate until caller/use analysis shows that it belongs to live HUD/UI rendering.

Special attention should now go to:

- sprite batching / pre-transformed vertices,
- screen-coordinate conversion functions,
- matrix path around `0x08AC5BA8`,
- functions that are shared by health bars, text, and menu panels but not necessarily by full-screen overlays.

## Important Prior Negative Result

User-provided historical result:

- Previous sprite-level or individual 2D element experiments caused regressions including dark pause overlay issues, incorrect or empty health-bar fills, blocky graphical corruption, and inconsistent UI behavior.

Status: STRONG EVIDENCE that broad per-sprite manipulation is the wrong first strategy.

## Candidate Categories To Separate

- Gameplay HUD: health bars, names, timer, round indicators, rage indicators.
- Menus: title, character select, stage select, options, pause menu, results.
- Full-screen overlays: pause darkening, fades, screen effects.
- Pre-rendered/video elements.

## Research Rules

- Do not globally shrink all 2D rendering.
- Do not patch every occurrence of a coordinate or aspect constant.
- Trace usage before patching.
- Keep full-screen overlays distinct from ordinary HUD where evidence supports separate paths.
- Preserve the known-good 3D-only configuration as the safe baseline.
