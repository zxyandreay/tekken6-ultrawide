# Handoff

Last updated: 2026-09-03

## Current Objective

Continue careful reverse engineering of Tekken 6 USA (`ULUS10466`) rendering paths. Static analysis has now separated the main perspective-projection architecture from three PSP-native 480x272 orthographic projection setup paths.

The immediate objective is no longer broad HUD patching. It is to **visually classify orthographic paths A, B, and C** in PPSSPP so a future PRX plugin can apply safe-area compensation to ordinary HUD/UI without shrinking full-screen overlays/fades.

The long-term goal remains a PPSSPP plugin named `Tekken6.PPSSPP.UltrawideFix` that:

- reproduces the known working 20:9 3D aspect correction,
- preserves HUD/UI/2D proportions,
- keeps full-screen overlays covering the full output,
- avoids previous sprite-level HUD regressions,
- keeps the ISO untouched and undistributed.

## Verified So Far

### Input and executable

- The local ISO is read-only project input and must never be committed.
- `ULUS10466.ini` contains the known working 20:9 3D CWCheat and separate camera toggles.
- `ULUS10466_EBOOT.BIN` is a decrypted/static-analysis-suitable 32-bit little-endian MIPS ELF executable.
- The EBOOT has one load segment:
  - file offset `0x00001018`
  - virtual address `0x08804018`
  - file size `0x003F62A8`
  - memory size `0x0045F02C`
  - flags `0x00000007`
- No section headers are present.

### Existing 3D aspect system

- CWCheat-to-EBOOT mapping is verified for all eight known 3D aspect instructions.
- The four patched constants are case/index `0` in four six-entry aspect dispatch tables; case/index `5` loads a custom aspect from a structure field.
- Direct xrefs:
  - `0x08945ED4`: 6 direct `j`/`jal` xrefs.
  - `0x089466EC`: one direct tail `j` at `0x08956E20`.
  - `0x08946B6C`: direct `jal` at `0x08863CA4` and `0x08863F28`.
  - `0x08947834`: no direct `j`/`jal` found.

### Perspective builder

- Generic perspective projection builder: `0x08ACA6C4`.
- Direct calls:
  - `0x08863D20`
  - `0x08863D84`
  - `0x089467A8`
  - `0x08955494`
- `aspect_dispatch_2` directly supplies the selected aspect to the builder at `0x089467A8`.
- The function around `0x0895540C` calls `aspect_dispatch_1` at `0x08955440`, then uses its result as the perspective aspect at `0x08955494`.
- The function around `0x08863C4C` obtains projection fields through helper/getter calls including `aspect_dispatch_3` and then calls the same perspective builder.

This is strong architectural confirmation that the known 20:9 CWCheat changes real perspective/camera projection behavior rather than merely stretching final output.

### Orthographic builder / likely 2D coordinate setup

- Generic orthographic projection builder: `0x08ACA990`.
- Static math matches a standard orthographic matrix built from six float bounds in `$f12`-`$f17`.
- Exactly three direct calls were found:
  - Path A `0x08863258`
  - Path B `0x088634E4`
  - Path C `0x088644B8`
- All three callers establish X `0..480` and Y `272..0`, i.e. PSP-native logical 2D coordinates.
- Right-X `480.0` loads:
  - A: runtime `0x08863230`, file `0x00060230`, CWCheat `0x20063230`, original `0x3C0143F0`
  - B: runtime `0x088634A0`, file `0x000604A0`, CWCheat `0x200634A0`, original `0x3C0143F0`
  - C: runtime `0x08864494`, file `0x00061494`, CWCheat `0x20064494`, original `0x3C0143F0`
- The resulting matrices feed/branch into matrix routine `0x08ACAB14` at `0x0886327C`, `0x088634F4`, and `0x088644D4`.

### Explanation of previous HUD failure

A centered 16:9 safe area inside 20:9 has a virtual logical width of 600:

- `480 * (20 / 16) = 600`
- centered around 240 -> X bounds `[-60, 540]`

Earlier experiments applied this type of projection change broadly. The math can preserve ordinary HUD proportions, but a full-screen quad still authored at X `0..480` then covers only 480 of the 600 logical units. This explains the observed side gaps/broken dark pause overlay when all 2D rendering was globally treated as safe-area HUD.

The likely final solution therefore needs **selective treatment**, not a global ortho shrink.

### Rejected first-line target

- Previous experiment area around `0x08864B74` does not call `0x08ACA990`; it calls `0x08AC5BA8`.
- Do not include it in the first orthographic HUD solution without separate evidence.

## Important Hashes

- ISO SHA-256: `45E9EAA105AFDA7C44204909E7FA22321236C89158BD7D26B52ABA2F2E0794C8`
- `ULUS10466_EBOOT.BIN` SHA-256: `E0ED418952C51032796EBC54584592A9F6075495229F6D12D5065F3186BCB55F`
- `ULUS10466.ini` SHA-256: `C82619333B621B22ACD86A23F595FC344CC181879F4D963E381D45C10E1C4D77`

## Known 3D Patch Addresses

Known 20:9 3D CWCheat write pairs:

- `0x20145F10` runtime `0x08945F10`, file `0x00142F10` -> `0x3C01400E`
- `0x20145F14` runtime `0x08945F14`, file `0x00142F14` -> `0x342138E4`
- `0x20146794` runtime `0x08946794`, file `0x00143794` -> `0x3C01400E`
- `0x20146798` runtime `0x08946798`, file `0x00143798` -> `0x342138E4`
- `0x20146BC8` runtime `0x08946BC8`, file `0x00143BC8` -> `0x3C01400E`
- `0x20146BCC` runtime `0x08946BCC`, file `0x00143BCC` -> `0x342138E4`
- `0x20147D90` runtime `0x08947D90`, file `0x00144D90` -> `0x3C01400E`
- `0x20147D94` runtime `0x08947D94`, file `0x00144D94` -> `0x342138E4`

Known restore/original pair at each site constructs `0x3FE38E39` using `0x3C013FE3` + `0x34218E39`.

Optional camera site remains out of scope for initial plugin work:

- `0x1015350C`, values `0x3F80`, `0x3F81`, `0x3F82`, `0x3F83`

## Analysis Helpers

- `python tools/analyze_eboot.py`
- `python tools/disassemble_aspect_sites.py --before 0x40 --after 0x80` (requires Capstone)
- `python tools/find_mips_xrefs.py 0x08945ED4 0x089466EC 0x08946B6C 0x08947834`
- `python tools/analyze_projection_paths.py` (standard library only)

## Diagnostic Artifact

`diagnostics/ULUS10466_ORTHO_PATH_TEST.ini` contains:

- known-good 20:9 3D patch,
- isolated Path A/B/C `600-wide` tests,
- ortho restore,
- full original restore.

The diagnostic changes only one `480.0` right-X load to `600.0` at a time. It deliberately leaves the left bound at 0 so the affected UI group becomes obviously narrower/left-aligned. This is a classification tool, **not a final visual fix**.

## Still Uncertain

- Which visible screens/elements use orthographic Path A, B, and C.
- Whether battle HUD and full-screen overlays share any of those paths.
- Whether menus and fight HUD use separate path combinations.
- Exact indirect ownership of the larger aspect/projection path containing `0x08947834`.
- Whether the eventual plugin should patch selected call sites, wrap `0x08ACA990` based on caller, or use another higher-level context signal.

## Current Plugin Status

No plugin source exists yet and no PRX build exists yet.

This is intentional: static analysis now provides a clean diagnostic that should classify the 2D paths before runtime hooks are designed. Preserve the known-good 3D-only mode.

The Warriors PPSSPP Fusion Fix remains an architectural reference for pattern scanning/runtime injection. Its upstream WidescreenFixesPack is MIT licensed; if substantial code is adapted later, preserve the required MIT notice/attribution.

## Next Recommended Experiment

User-side test on POCO F5:

1. Sync repository main.
2. Copy `diagnostics/ULUS10466_ORTHO_PATH_TEST.ini` to PPSSPP's `PSP/Cheats/ULUS10466.ini` temporarily (back up normal cheat file first).
3. Set PPSSPP Display Layout to Stretch.
4. Enable `Screen - 20:9 Ultrawide`.
5. Enable **only Path A** and note changes across title/menu, character select, fight HUD, pause menu, pause dark overlay, fades, and results.
6. Restore ortho paths, then repeat independently for B and C.
7. Report observations/screenshots using `docs/TEST_PLAN.md` categories.

The most important observation is whether a path controls ordinary HUD without controlling full-screen overlay/fade geometry. That path would be the strongest candidate for safe-area compensation in the first plugin prototype.

## Known Dead Ends

- Broad/individual sprite manipulation caused pause overlay, health-bar, and block-artifact regressions.
- Applying centered 600-wide safe-area projection indiscriminately to all 2D paths is not acceptable because full-screen overlays authored for 0..480 can stop covering the sides.
- Do not return to `0x08864B74` as an orthographic target unless its separate `0x08AC5BA8` call path is independently understood.

## User Testing Required

No final visual claim is proven until the user tests in PPSSPP. Follow `docs/TEST_PLAN.md` for the isolated A/B/C classification before writing the first HUD plugin hook.

## Last Pushed Checkpoint Before This Handoff

`dfcc84b336ac9f4af7299eb33a4a91b51bdc7529` - `test: document orthographic path classification`
