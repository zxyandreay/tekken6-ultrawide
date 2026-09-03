# Handoff

Last updated: 2026-09-03

## Current Objective

Continue careful reverse engineering of Tekken 6 USA (`ULUS10466`) rendering paths. The initial baseline checkpoint has been pushed; the current active research thread is mapping the known 3D aspect patch sites.

The long-term goal is a PPSSPP plugin named `Tekken6.PPSSPP.UltrawideFix` that:

- reproduces the known working 20:9 3D aspect correction,
- preserves HUD/UI/2D proportions,
- avoids previous sprite-level HUD regressions,
- keeps the ISO untouched and undistributed.

## Verified So Far

- Local folder initially contained only:
  - `Tekken 6 (USA) (En,Ja,Fr,De,Es,It,Ko,Ru).iso`
  - `ULUS10466.ini`
  - `ULUS10466_EBOOT.BIN`
- The ISO is read-only project input and must never be committed.
- `ULUS10466.ini` contains the known working 20:9 3D CWCheat and separate camera toggles.
- `ULUS10466_EBOOT.BIN` is a decrypted/static-analysis-suitable 32-bit little-endian MIPS ELF executable.
- The EBOOT has one load segment:
  - file offset `0x00001018`
  - virtual address `0x08804018`
  - file size `0x003F62A8`
  - memory size `0x0045F02C`
  - flags `0x00000007`
- No section headers are present, so function names/sections should not be expected from ordinary ELF section data.
- Initial baseline checkpoint pushed to `origin/main` at `f720d0157face81618f9b818e3d763977e55a6ae`.
- CWCheat-to-EBOOT mapping has been verified for the eight known 3D aspect instructions.
- `tools/analyze_eboot.py` reproduces the ELF summary, pattern counts, and address mapping.
- `tools/disassemble_aspect_sites.py` dumps Capstone disassembly and six-entry aspect dispatch tables.
- `tools/find_mips_xrefs.py` scans direct `j`/`jal` references and literal 32-bit pointer words.
- The four patched constants are case/index `0` in four aspect dispatch tables; case/index `5` loads a custom aspect from a structure field.
- Direct xrefs found so far:
  - `0x08945ED4`: 6 direct `j`/`jal` xrefs.
  - `0x089466EC`: one direct `j` tail-call at `0x08956E20`.
  - `0x08946B6C`: two direct `jal` xrefs at `0x08863CA4` and `0x08863F28`.
  - `0x08947834`: no direct `j`/`jal` xrefs found.

## Important Hashes

- ISO SHA-256: `45E9EAA105AFDA7C44204909E7FA22321236C89158BD7D26B52ABA2F2E0794C8`
- `ULUS10466_EBOOT.BIN` SHA-256: `E0ED418952C51032796EBC54584592A9F6075495229F6D12D5065F3186BCB55F`
- `ULUS10466.ini` SHA-256: `C82619333B621B22ACD86A23F595FC344CC181879F4D963E381D45C10E1C4D77`

## Known Addresses

Known 20:9 3D CWCheat write pairs, with verified EBOOT file offsets:

- `0x20145F10` runtime `0x08945F10`, file `0x00142F10` -> `0x3C01400E`
- `0x20145F14` runtime `0x08945F14`, file `0x00142F14` -> `0x342138E4`
- `0x20146794` runtime `0x08946794`, file `0x00143794` -> `0x3C01400E`
- `0x20146798` runtime `0x08946798`, file `0x00143798` -> `0x342138E4`
- `0x20146BC8` runtime `0x08946BC8`, file `0x00143BC8` -> `0x3C01400E`
- `0x20146BCC` runtime `0x08946BCC`, file `0x00143BCC` -> `0x342138E4`
- `0x20147D90` runtime `0x08947D90`, file `0x00144D90` -> `0x3C01400E`
- `0x20147D94` runtime `0x08947D94`, file `0x00144D94` -> `0x342138E4`

Known restore/original 3D write pairs:

- `0x20145F10` -> `0x3C013FE3`
- `0x20145F14` -> `0x34218E39`
- `0x20146794` -> `0x3C013FE3`
- `0x20146798` -> `0x34218E39`
- `0x20146BC8` -> `0x3C013FE3`
- `0x20146BCC` -> `0x34218E39`
- `0x20147D90` -> `0x3C013FE3`
- `0x20147D94` -> `0x34218E39`

Optional camera site, not initial plugin scope:

- `0x1015350C`, values `0x3F80`, `0x3F81`, `0x3F82`, `0x3F83`

## Still Uncertain

- Containing functions for the four 3D aspect patch sites.
- Why four locations are required.
- Whether the four locations represent different projection modes, different callers, or different copies of related setup code.
- Exact function names and caller chains.
- HUD/screen-space transform location.
- Whether gameplay HUD, menus, overlays, and videos share any transform path.

## Current Plugin Status

No plugin source exists yet.

No plugin build command exists yet.

Analysis helpers:

- `python tools/analyze_eboot.py`
- Install disassembly dependency with `python -m pip install -r requirements.txt`.
- `python tools/disassemble_aspect_sites.py --before 0x40 --after 0x80`
- `python tools/find_mips_xrefs.py 0x08945ED4 0x089466EC 0x08946B6C 0x08947834`

No `dist/` output exists yet.

## Next Recommended Experiment

The initial checkpoint is pushed and `tools/analyze_eboot.py` exists. Next:

1. Inspect callers around direct xrefs, especially `0x0894B2FC`, `0x0894BCB0`, `0x0894C69C`, `0x0894CB1C`, `0x08955268`, `0x08955440`, `0x08956E20`, `0x08863CA4`, and `0x08863F28`.
2. Identify indirect callers or table owners for the larger `0x08947834` projection-like function.
3. Derive relocation-stable byte signatures around each patch site.
4. Only then study plugin architecture and safe runtime patching.

## Known Dead Ends

User-provided historical dead end:

- Previous attempts to manipulate individual 2D/sprite elements caused HUD and overlay corruption. Avoid repeating that strategy without a clearly different abstraction and test plan.

## User Testing Required

No visual claims are proven until the user tests in PPSSPP. Use `docs/TEST_PLAN.md` once a plugin or new cheat experiment exists.

## Last Pushed Commit

Initial baseline checkpoint: `f720d0157face81618f9b818e3d763977e55a6ae`.
