# Test Plan

Last updated: 2026-09-03

## Target Setup

- Device: POCO F5
- Resolution: 2400x1080
- Aspect ratio: 20:9
- Emulator: PPSSPP
- PPSSPP Display Layout: Stretch
- Game: Tekken 6 USA (`ULUS10466`)

## Baseline Configurations

Test each build or cheat set with the relevant configuration clearly recorded.

| Configuration | Purpose |
| --- | --- |
| Original 16:9 / no aspect patch | Control case |
| Known-good `Screen - 20:9 Ultrawide` only | 3D-only behavior that must remain safe |
| 20:9 + Ortho Path A diagnostic | Classify path A ownership |
| 20:9 + Ortho Path B diagnostic | Classify path B ownership |
| 20:9 + Ortho Path C diagnostic | Classify path C ownership |
| Future `Fix3D = 1`, `FixHUD = 1` | Final plugin experiment; not implemented yet |

## Orthographic Path Diagnostic Procedure

Use `diagnostics/ULUS10466_ORTHO_PATH_TEST.ini` only for testing. It is not a normal-play cheat file.

1. Keep PPSSPP Display Layout set to `Stretch`.
2. Enable `Screen - 20:9 Ultrawide`.
3. Enable **only one** of `Diag - Ortho Path A/B/C 600-wide`.
4. Visit the screen groups listed below and note what becomes horizontally narrower or left-aligned.
5. Use `Diag - Restore Ortho Paths` before enabling the next path, or fully restart the game/PPSSPP.
6. Do not enable A, B, and C together for classification.

The diagnostic changes only the right X bound from 480 to 600 for a single orthographic projection. It deliberately does **not** center the result. A visible left-aligned/narrower 2D group is therefore a positive identification signal, not a visual defect to fix during this test.

For each path, pay special attention to whether a full-screen dark/fade overlay changes independently from ordinary HUD elements. Separating those categories is the key prerequisite for a safe final HUD fix.

## Path Classification Table

Fill this separately for A, B, and C.

| Area | What changed? | Path A | Path B | Path C |
| --- | --- | --- | --- | --- |
| Boot/title | Logo, title, full-screen backgrounds | NOT TESTED | NOT TESTED | NOT TESTED |
| Main menus | Text, panels, cursor, backgrounds | NOT TESTED | NOT TESTED | NOT TESTED |
| Character select | Portraits, names, cursor, background | NOT TESTED | NOT TESTED | NOT TESTED |
| Stage select | Preview, labels, panels | NOT TESTED | NOT TESTED | NOT TESTED |
| Gameplay HUD | Health bars, names, timer, round/rage indicators | NOT TESTED | NOT TESTED | NOT TESTED |
| Pause menu | Menu geometry/text | NOT TESTED | NOT TESTED | NOT TESTED |
| Pause dark overlay | Whether screen-darkening still covers full width | NOT TESTED | NOT TESTED | NOT TESTED |
| Results | Result panels/text | NOT TESTED | NOT TESTED | NOT TESTED |
| Training | Training overlays/HUD | NOT TESTED | NOT TESTED | NOT TESTED |
| Fades/transitions | Full-screen black/white/color fades | NOT TESTED | NOT TESTED | NOT TESTED |

## Result Labels

Use these labels for each area:

- PASS: behavior is clearly attributable and stable.
- FAIL: corruption/crash or unusable behavior.
- PARTIAL: only some elements in the area respond.
- NO CHANGE: path does not visibly affect this area.
- NOT TESTED.

## Required Final Visual Checks

Once a real plugin/HUD correction exists, re-test:

| Area | Checks | Result |
| --- | --- | --- |
| Boot/title | Intro, title screen, menu proportions | NOT TESTED |
| Character select | Portraits, names, selection cursor | NOT TESTED |
| Stage select | Stage preview and UI proportions | NOT TESTED |
| Gameplay | Character proportions, wider world visibility, health bars, names, timer, round markers, rage indicator, particle effects | NOT TESTED |
| Pause | Pause menu proportions, dark overlay coverage | NOT TESTED |
| Results | Result screen layout and text | NOT TESTED |
| Training mode | HUD and gameplay behavior | NOT TESTED |
| Arcade/story | Mode-specific UI and transitions, if practical | NOT TESTED |
| Cutscenes | Framing, subtitles/text, pre-rendered elements | NOT TESTED |

## Reporting Template

Record:

- Build or diagnostic configuration tested.
- PPSSPP version.
- Device and resolution.
- Display Layout setting.
- Save state or mode used to reproduce.
- Path classification observations.
- Screenshots or video if available.
- Any plugin log file, once a plugin exists.
