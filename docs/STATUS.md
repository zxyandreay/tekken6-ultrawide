# Status

Last updated: 2026-09-03

## Current Phase

Phase 5B: the first isolated orthographic-path hypothesis has been tested and rejected for the visible HUD/UI/menus. Research now pivots to the live screen-space/sprite coordinate path.

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
- Added `tools/analyze_projection_paths.py` and isolated diagnostic INI.
- User tested Path A, B, and C independently on the POCO F5 with 20:9 + Stretch.
- **All three A/B/C tests produced no visible change in HUD/UI/menus.**
- Recorded A/B/C as a reproducible negative result rather than continuing blind ortho experiments.
- Added `tools/find_screen_space_candidates.py` to scan for broader PSP logical-coordinate code around 480/272, centers, and 512x320-style virtual dimensions.
- Kept `0x08864B74 -> 0x08AC5BA8` out of the first ortho solution but promoted the distinct `0x08AC5BA8` family for renewed static analysis now that A/B/C did not affect visible UI.

## Current Blocker

The repository's EBOOT can be analyzed locally, but the next useful ranking of live screen-space candidates requires running the new scanner against the decrypted EBOOT and inspecting its report.

The primary open question is now whether Tekken's visible HUD uses:

- pre-transformed/sprite vertices,
- a separate matrix family such as `0x08AC5BA8`,
- a screen-coordinate conversion helper,
- or a transform applied after the three generic orthographic setup paths.

## Current Experimental Status

The A/B/C diagnostic has completed its purpose and should not be repeated unless a newly identified screen points back to one of those paths.

No PRX plugin HUD patch is active yet. The safe baseline remains the working 20:9 3D CWCheat only.

## Last Known-Good Behavior

`ULUS10466.ini` remains the safe baseline: working 20:9 3D correction only, with HUD/UI still stretched when PPSSPP Display Layout is set to Stretch.

Do not replace or weaken that baseline while HUD research continues.

## Latest Build Status

No plugin source or PRX build output exists yet. This remains intentional; user testing disproved the first orthographic ownership hypothesis, so building a hook around those call sites now would encode the wrong abstraction.

## Next Required Local Analysis

After syncing the repository, run:

```bash
python -m pip install -r requirements.txt
python tools/find_screen_space_candidates.py --output diagnostics/SCREEN_SPACE_CANDIDATES.md
```

Then review/commit the generated report so the next analysis pass can rank candidate live HUD/sprite paths without guessing.

## User Validation Still Required

No further A/B/C visual testing is required now. Future user-side diagnostics should only be created after static analysis identifies a stronger live 2D/screen-space candidate.

All final visual behavior must still be validated in PPSSPP; static analysis alone is not proof of correctness.
