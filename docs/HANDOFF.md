# Handoff

Last updated: 2026-09-03

## Current Objective

Continue reverse engineering of Tekken 6 USA (`ULUS10466`) rendering paths with the long-term goal of a PPSSPP plugin that provides true ultrawide 3D rendering while preserving HUD/UI proportions.

The first runtime classification experiment is now complete: the three direct 480x272 orthographic setup paths A/B/C did **not** visibly affect HUD/UI/menus on the target POCO F5. Do not build the plugin around those three paths.

The immediate objective is now to identify the **actual live screen-space/sprite coordinate path** used by visible Tekken HUD and menus.

## Verified So Far

### Input and executable

- The local ISO is read-only project input and must never be committed.
- `ULUS10466.ini` contains the known working 20:9 3D CWCheat and separate camera toggles.
- `ULUS10466_EBOOT.BIN` is a decrypted/static-analysis-suitable 32-bit little-endian MIPS ELF executable.
- EBOOT load segment:
  - file offset `0x00001018`
  - virtual address `0x08804018`
  - file size `0x003F62A8`
  - memory size `0x0045F02C`
  - flags `0x00000007`
- No section headers are present.

### Existing 3D aspect system

- CWCheat-to-EBOOT mapping is verified for all eight known 3D aspect instructions.
- The four patched constants are case/index `0` in four six-entry aspect dispatch tables; case/index `5` loads a custom aspect from a structure field.
- Perspective projection builder: `0x08ACA6C4`.
- Direct perspective calls:
  - `0x08863D20`
  - `0x08863D84`
  - `0x089467A8`
  - `0x08955494`
- The known 20:9 cheat changes real perspective/camera projection behavior; it is not merely final framebuffer stretching.

### Orthographic builder and rejected ownership hypothesis

- Generic orthographic projection builder: `0x08ACA990`.
- Three direct PSP-native 480x272 setup calls:
  - Path A call `0x08863258`, right bound load `0x08863230`
  - Path B call `0x088634E4`, right bound load `0x088634A0`
  - Path C call `0x088644B8`, right bound load `0x08864494`
- All three establish X `0..480`, Y `272..0`.
- `diagnostics/ULUS10466_ORTHO_PATH_TEST.ini` changed each right bound independently from 480 to 600.

### VERIFIED USER TEST: A/B/C are not the visible HUD/UI path

Target test setup:

- POCO F5
- 2400x1080 / 20:9
- PPSSPP Display Layout = Stretch
- known-good 20:9 3D patch enabled

User tested Path A, B, and C independently.

Result:

- Path A: no visible change in HUD/UI/menus.
- Path B: no visible change in HUD/UI/menus.
- Path C: no visible change in HUD/UI/menus.

A 480->600 horizontal projection change would be visibly large if a tested UI group actively used that path, so A/B/C should not be used as the first HUD hook target.

Possible interpretations still open:

1. those paths serve other/unvisited rendering categories,
2. they are initialization/utility paths,
3. visible HUD uses pre-transformed/sprite vertices,
4. visible HUD uses a different matrix family,
5. a later transform overrides those matrices.

### Distinct path worth renewed analysis

- Code around `0x08864B74` calls `0x08AC5BA8`, not the generic ortho builder.
- It was previously rejected as an orthographic target, correctly.
- Now that A/B/C are no-ops for visible UI, the separate `0x08AC5BA8` family is worth analyzing as a possible screen-space/sprite transform path.

## Important Hashes

- ISO SHA-256: `45E9EAA105AFDA7C44204909E7FA22321236C89158BD7D26B52ABA2F2E0794C8`
- `ULUS10466_EBOOT.BIN` SHA-256: `E0ED418952C51032796EBC54584592A9F6075495229F6D12D5065F3186BCB55F`
- `ULUS10466.ini` SHA-256: `C82619333B621B22ACD86A23F595FC344CC181879F4D963E381D45C10E1C4D77`

## Known 3D Patch Addresses

20:9 write pairs:

- `0x20145F10` -> `0x3C01400E`
- `0x20145F14` -> `0x342138E4`
- `0x20146794` -> `0x3C01400E`
- `0x20146798` -> `0x342138E4`
- `0x20146BC8` -> `0x3C01400E`
- `0x20146BCC` -> `0x342138E4`
- `0x20147D90` -> `0x3C01400E`
- `0x20147D94` -> `0x342138E4`

Original pair at each site constructs `0x3FE38E39` using `0x3C013FE3` + `0x34218E39`.

Optional camera site remains out of initial plugin scope:

- `0x1015350C`, values `0x3F80`, `0x3F81`, `0x3F82`, `0x3F83`

## Analysis Helpers

Existing:

- `python tools/analyze_eboot.py`
- `python tools/disassemble_aspect_sites.py --before 0x40 --after 0x80`
- `python tools/find_mips_xrefs.py 0x08945ED4 0x089466EC 0x08946B6C 0x08947834`
- `python tools/analyze_projection_paths.py`

New after the A/B/C negative test:

- `python tools/find_screen_space_candidates.py --output diagnostics/SCREEN_SPACE_CANDIDATES.md`

The new scanner searches the decrypted EBOOT for likely PSP logical screen constants and nearby MIPS call structure around:

- 480 / 272
- 240 / 136
- 512 / 320
- 256 / 160

It is a broad candidate generator, not proof of HUD ownership.

## Current Plugin Status

No plugin source/PRX exists yet.

This remains intentional. Building a runtime hook before identifying the live screen-space path would repeat the same mistake as previous broad HUD experiments.

Preserve the working 3D-only CWCheat as the safe baseline.

## Next Required Local Step

Because the decrypted EBOOT is available in the user's local repository, run the new scanner locally after syncing:

```bash
python -m pip install -r requirements.txt
python tools/find_screen_space_candidates.py --output diagnostics/SCREEN_SPACE_CANDIDATES.md
```

Then commit/push `diagnostics/SCREEN_SPACE_CANDIDATES.md` so the next analysis pass can inspect actual candidate functions and rank them.

Suggested commit command:

```bash
git add diagnostics/SCREEN_SPACE_CANDIDATES.md
git commit -m "research: add screen-space candidate report"
git push origin main
```

After that, inspect:

1. candidate functions that combine 480/272 or 512/320 dimensions,
2. nearby call families shared by multiple candidates,
3. `0x08AC5BA8` and its callers,
4. code that constructs pre-transformed vertices or sprite positions,
5. functions likely shared by health bars/text/menu panels while avoiding global full-screen overlays.

Do not create a new visual diagnostic until static evidence identifies a stronger live path.

## Known Dead Ends / Negative Results

- Broad individual-sprite manipulation caused pause overlay, health-bar, and block-artifact regressions.
- A/B/C direct generic orthographic paths are now user-tested no-ops for the visible HUD/UI/menu screens tested.
- Do not spend more user time repeating A/B/C unless a newly identified untested screen gives specific reason.
- Do not treat `0x08864B74` as an ortho-builder call; it belongs to the separate `0x08AC5BA8` path.

## User Testing Required

No immediate new visual test is required. First generate and inspect the static screen-space candidate report.

Any later candidate HUD patch must still be validated on the POCO F5 under PPSSPP Stretch before being called successful.
