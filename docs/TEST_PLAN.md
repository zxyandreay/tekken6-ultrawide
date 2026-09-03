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
| `Fix3D = 0`, `FixHUD = 0` | Control case |
| `Fix3D = 1`, `FixHUD = 0` | Known-good 3D-only behavior to preserve |
| `Fix3D = 1`, `FixHUD = 1` | Future HUD experiment; not implemented yet |

## Result Labels

Use these labels for each area:

- PASS
- FAIL
- PARTIAL
- NOT TESTED

## Required Visual Checks

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

- Build or cheat configuration tested.
- PPSSPP version.
- Device and resolution.
- Display Layout setting.
- Save state or mode used to reproduce.
- Result table.
- Screenshots or video if available.
- Any plugin log file, once a plugin exists.
