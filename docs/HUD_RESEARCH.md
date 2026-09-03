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

All three therefore establish a PSP-native 480x272 logical 2D projection. Which screen categories use each path is not yet visually classified.

`tools/analyze_projection_paths.py` reproduces the direct perspective/ortho call scan and verifies the three original `480.0` instructions.

### STRONG EVIDENCE: why the previous global HUD experiment broke overlays

A centered 16:9 safe area inside a 20:9 output has a virtual width of 600 logical units:

- `480 * (20 / 16) = 600`
- centered around original X center `240` gives bounds `[-60, 540]`

Earlier experiments changed all three orthographic paths from X `0..480` to X `-60..540`. The math itself is consistent with preserving ordinary 16:9 HUD proportions after a 20:9 final stretch.

However, a full-screen quad still authored from X `0..480` then occupies only the central 480 units of a 600-unit projection. This provides a direct architectural explanation for the historical symptom where a dark pause overlay/fade stopped covering the full screen: ordinary HUD and full-screen overlays cannot necessarily receive the same safe-area treatment.

Status: STRONG EVIDENCE. The exact caller/screen ownership of paths A/B/C still needs PPSSPP runtime/visual validation.

### REJECTED as a first-line HUD target: `0x08864B74` path

A previous broad safe-area experiment also modified code around `0x08864B74`. Static disassembly shows that this path does **not** call the orthographic builder `0x08ACA990`; it calls a different routine at `0x08AC5BA8`.

It should not be included in the first isolated orthographic-path experiments without separate evidence.

## New Diagnostic Strategy

Instead of changing whole projection sequences, `diagnostics/ULUS10466_ORTHO_PATH_TEST.ini` changes only the right X bound from `480.0` to `600.0` for one path at a time:

- Path A: CWCheat `0x20063230`, original word `0x3C0143F0`, diagnostic word `0x3C014416`
- Path B: CWCheat `0x200634A0`, original word `0x3C0143F0`, diagnostic word `0x3C014416`
- Path C: CWCheat `0x20064494`, original word `0x3C0143F0`, diagnostic word `0x3C014416`

`600.0f` is `0x44160000`, so replacing only the `lui $at, 0x43F0` instruction with `lui $at, 0x4416` is intentionally minimal.

This is **not a final HUD fix**. It deliberately produces a left-aligned/narrower-looking 2D group under Stretch so the user can identify which screens/elements each orthographic path owns without moving instruction sequences or touching sprite data.

Enable only one diagnostic path at a time and restore the three paths between tests.

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
