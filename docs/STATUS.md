# Status

Last updated: 2026-09-03

## Current Phase

Phase 5: classify Tekken 6's 2D/HUD orthographic projection paths before implementing a runtime plugin HUD fix.

## Completed

- Inspected the local project directory and initialized the research repository on `main`.
- Configured `origin` as `https://github.com/zxyandreay/tekken6-ultrawide.git`.
- Read `ULUS10466.ini` and documented the known-good cheat baseline.
- Computed SHA-256 hashes for the ISO, EBOOT, and INI.
- Verified `ULUS10466_EBOOT.BIN` is a 32-bit little-endian MIPS ELF executable, not encrypted `~PSP` data.
- Added `.gitignore` rules protecting disc images and temporary extracted assets.
- Verified the CWCheat-to-EBOOT mapping for all eight known 3D aspect instruction writes.
- Added repeatable ELF, disassembly, and MIPS xref analysis helpers.
- Documented the four six-entry aspect dispatch tables.
- Identified generic perspective projection builder `0x08ACA6C4` and four direct callers.
- Tied aspect dispatches 1-3 directly to perspective/camera projection setup.
- Identified generic orthographic projection builder `0x08ACA990`.
- Identified exactly three direct 480x272 orthographic setup paths at calls `0x08863258`, `0x088634E4`, and `0x088644B8`.
- Verified right-X `480.0` loads at `0x08863230`, `0x088634A0`, and `0x08864494`.
- Added `tools/analyze_projection_paths.py` to reproduce projection-call scanning without Capstone.
- Added `diagnostics/ULUS10466_ORTHO_PATH_TEST.ini` for isolated one-path-at-a-time PPSSPP classification.
- Documented why the earlier centered `[-60, 540]` global 2D experiment could mathematically preserve ordinary HUD proportions yet break full-screen overlays: a 0..480 overlay no longer covers a 600-wide logical projection.
- Rejected the previous `0x08864B74` path as a first-line orthographic HUD target because it calls `0x08AC5BA8`, not `0x08ACA990`.

## Current Blocker

Static analysis cannot reliably tell which visible screen groups use orthographic paths A, B, and C. The next high-value step is user-side PPSSPP testing of the isolated diagnostics to classify battle HUD, menus, pause overlays/fades, and other 2D groups.

## Current Experimental Status

No PRX plugin patch is active yet. The repository now contains a deliberately minimal diagnostic INI. Each diagnostic changes only one right-X bound from `480.0` to `600.0`; it is designed to make the affected 2D group obviously narrower/left-aligned under Stretch so its ownership can be identified without broad sprite hooks.

This diagnostic is not intended for normal play and is not a final HUD correction.

## Last Known-Good Behavior

`ULUS10466.ini` remains the safe baseline: working 20:9 3D correction only, with HUD/UI still stretched when PPSSPP Display Layout is set to Stretch.

Do not replace or weaken that baseline while diagnostic work continues.

## Latest Build Status

No plugin source or PRX build output exists yet. Plugin implementation should wait until the three orthographic paths are visually classified well enough to separate ordinary HUD from full-screen overlays.

## User Validation Still Required

The user should test `diagnostics/ULUS10466_ORTHO_PATH_TEST.ini` on the POCO F5 with PPSSPP Stretch, enabling only one of Path A/B/C at a time. Record which visible elements change on title/menu, character select, gameplay HUD, pause overlay, and results screens.

All final visual behavior must be validated in PPSSPP; static analysis alone is not proof of correctness.
