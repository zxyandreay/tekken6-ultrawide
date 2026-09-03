# Status

Last updated: 2026-09-03

## Current Phase

Phase 3: mapping the existing working 3D patch.

## Completed

- Inspected the local project directory.
- Confirmed the local folder was not already a Git repository.
- Initialized a new Git repository on `main`.
- Configured `origin` as `https://github.com/zxyandreay/tekken6-ultrawide.git`.
- Fetched from `origin`; no remote branches were advertised at the time of setup.
- Read `ULUS10466.ini` and documented the known cheat baseline.
- Computed SHA-256 hashes for the ISO, EBOOT, and INI.
- Verified `ULUS10466_EBOOT.BIN` is a 32-bit little-endian MIPS ELF executable, not encrypted `~PSP` data.
- Added `.gitignore` rules to protect disc images and temporary extracted assets.
- Pushed the initial baseline checkpoint to `origin/main` at `f720d0157face81618f9b818e3d763977e55a6ae`.
- Verified the CWCheat-to-EBOOT mapping for all eight known 3D aspect instruction writes.
- Added `tools/analyze_eboot.py` for repeatable ELF header inspection and known aspect address mapping.

## Current Blocker

None. Next work is MIPS disassembly around the four verified aspect pairs.

## Current Experimental Status

No plugin or runtime patching experiment has been started in this repository. Static address mapping has begun.

## Last Known-Good Behavior

User-provided baseline: `ULUS10466.ini` contains a working 20:9 3D CWCheat for Tekken 6 USA (`ULUS10466`). The known-good state is 3D aspect correction only; HUD/UI is still expected to stretch under PPSSPP Stretch layout.

## Latest Build Status

No plugin source or build output exists yet.

## User Validation Still Required

All visual behavior must be validated by the user in PPSSPP on the POCO F5 or an equivalent 2400x1080 20:9 setup. Static analysis and successful builds are not proof of visual correctness.
