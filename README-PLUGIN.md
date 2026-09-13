# Tekken 6 Ultrawide Auto Aspect — v1.0.0 test build

This research build converts the existing ULUS10466 projection CWCheat into a PPSSPP PRX plugin.

## Scope

- Queries PPSSPP for the current landscape display aspect ratio.
- Converts the exact returned float into Tekken 6's existing `lui $at` / `ori $at,$at` projection constant.
- Patches only the four previously validated 3D projection paths.
- Leaves the camera and all HUD/menu rendering untouched.
- Refuses to patch if any projection pair does not match stock 16:9 or the already-computed target.

## Test setup

1. Disable the Tekken 6 aspect-ratio CWCheat entries. Keep camera cheats disabled for this first test as well.
2. Install the plugin folder under `PSP/PLUGINS/Tekken6Ultrawide/`.
3. Enable the plugin for Tekken 6 if PPSSPP does not enable it automatically.
4. Keep PPSSPP display scaling set to **Stretch**. The plugin changes the game's 3D projection; Stretch fills the physical display.
5. Launch USA Tekken 6 (`ULUS10466`) in landscape orientation using a normal boot for the first test.

Expected result on a 2400×1080 / 20:9 display: the 3D scene should match the old 20:9 cheat automatically, while the HUD remains horizontally stretched. That remaining HUD behavior is intentional for this milestone.
