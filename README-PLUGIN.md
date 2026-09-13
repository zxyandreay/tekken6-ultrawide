# Tekken 6 Ultrawide Auto Aspect — v1.1.0 development build

This research branch converts the existing ULUS10466 projection CWCheat from the public v1.0.0 release into a PPSSPP PRX plugin with automatic display-aspect detection.

## Current milestone

- Queries PPSSPP for the current landscape display aspect ratio.
- Converts the exact returned float into Tekken 6's existing `lui $at` / `ori $at,$at` projection constant.
- Patches only the four previously validated 3D projection paths.
- Leaves the camera and all HUD/menu rendering untouched.
- Refuses to patch if any projection pair does not match stock 16:9 or the already-computed target.

## v1.1.0-dev2 fix

The first test candidate incorrectly treated `PPSSPP_DEVCTL_IS_EMULATOR` as an output-value query and waited for PPSSPP to write `1` into a buffer. PPSSPP's API actually reports emulator presence through the devctl return code: `0` means the command is supported/running under PPSSPP. The bad check caused the plugin to exit before applying any Tekken projection patch.

## Test setup

1. Disable every Tekken 6 aspect-ratio CWCheat entry. Keep camera cheats disabled for this isolated test.
2. Replace the previous test plugin folder with the new `PSP/PLUGINS/Tekken6Ultrawide/` folder.
3. Enable the plugin for Tekken 6 if PPSSPP does not enable it automatically.
4. Keep PPSSPP display scaling set to **Stretch**.
5. Launch USA Tekken 6 (`ULUS10466`) in landscape orientation from a normal cold boot.

Expected result on a 2400×1080 / 20:9 display: the 3D scene should match the old 20:9 CWCheat automatically, while the HUD remains horizontally stretched. HUD correction is intentionally outside this milestone.
