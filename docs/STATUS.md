# Status

Last updated: 2026-09-03

## Current Phase

Phase 6A: first PPSSPP PRX implementation and controlled HUD classification testing.

The project has moved from static-only HUD research to a real plugin build. The 3D aspect component is based on the already user-verified ULUS10466 aspect patch. The HUD portion remains experimental and is intentionally split into isolated candidate groups so testing can classify which live 2D path owns ordinary HUD versus masks/overlays.

## Completed

- Verified `ULUS10466_EBOOT.BIN` as a decrypted 32-bit little-endian MIPS ELF suitable for static analysis.
- Verified all four known 3D aspect-dispatch patch sites and tied them to perspective/camera projection.
- Preserved the known-good 20:9 CWCheat baseline.
- Identified generic perspective builder `0x08ACA6C4` and generic orthographic builder `0x08ACA990`.
- User tested three direct 480x272 orthographic paths A/B/C; all were visible no-ops for the tested HUD/UI/menu screens.
- Added broader screen-space and Warriors-style candidate analysis tools.
- Ranked two stronger live 2D/render-state candidate families:
  - Group A around `0x08A3916C–0x08A396D8`.
  - Group B around `0x08AA62D8–0x08AA655C`, currently suspected to be mask-like.
- Added `docs/WARRIORS_ARCHITECTURE.md` documenting the separate 3D-aspect and HUD-scale architecture used by The Warriors Fusion Fix.
- Added a self-contained PSP PRX implementation under `plugin/`.
- Added PPSSPP manifest/config packaging for `ULUS10466` only.
- Added a GitHub Actions PSPSDK build using `pspdev/pspdev:latest`.
- Fixed the initial PSPSDK cache-invalidation compile issue.
- **GitHub Actions run 2 completed successfully and produced a packaged PRX artifact.**

## Plugin Behavior

### Verified 3D path

The plugin patches these four ULUS10466 locations at runtime:

- `0x08945F10`
- `0x08946794`
- `0x08946BC8`
- `0x08947D90`

Before writing, it verifies that each location still contains the expected `lui at,...` + `ori at,at,...` instruction shape. The default test config uses exact `20:9` for the POCO F5.

### Experimental HUD path

`HUDMode = 1` patches three 480.0 LUI loads in candidate Group A to 600.0:

- `0x08A39288`
- `0x08A392F4`
- `0x08A39360`

`HUDMode = 2` isolates Group B:

- `0x08AA6314`
- `0x08AA63B8`
- `0x08AA64C0`

`HUDMode = 3` applies both groups.

These HUD writes are guarded by opcode/value checks. They are not yet considered a final HUD fix.

## Current Reliability Statement

- **3D aspect:** high confidence for this exact ULUS10466 executable because it reproduces the known-good user-tested patch and verifies instruction signatures before writing.
- **HUD/UI:** experimental. The current repository findings are sufficient for a controlled plugin test, not sufficient to claim Warriors-level HUD reliability yet.

## Current Build

Successful workflow:

- Workflow: `Build PPSSPP plugin`
- Run: `2`
- Commit: `10ea8db60763bb293f65694cf0c5a5bf3337d215`
- Artifact: `Tekken6-PPSSPP-UltrawideFix`

Package contents:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
TESTING.md
```

## Required User Test Order

1. Disable the old Tekken 6 widescreen CWCheat.
2. Keep PPSSPP Display Layout = Stretch.
3. Test `HUDMode = 0` first to verify the PRX reproduces the known-good 20:9 3D view.
4. Test `HUDMode = 1` and record changes to health bars, timer, names, menus, pause screen, and fades.
5. Test `HUDMode = 2` separately to classify the mask-like path.
6. Only test `HUDMode = 3` if Groups A and B show complementary behavior.
7. Send the generated plugin log after any mismatch or unexpected result.

Detailed instructions are in `docs/PLUGIN_TEST.md`.

## Next Development Step

Use the user's PPSSPP results to classify Group A and Group B. If Group A controls ordinary HUD while Group B owns masks/overlays, replace the diagnostic `HUDMode` system with a proper caller/context-aware `FixHUD` implementation. If neither group affects the visible HUD, reject them and continue tracing higher-level screen-space descriptor/caller paths rather than returning to the already rejected generic orthographic paths.
