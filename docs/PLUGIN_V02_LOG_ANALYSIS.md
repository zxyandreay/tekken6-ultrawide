# Plugin v0.2 Runtime Log Analysis

Date: 2026-09-03

## User result

The user reported that the v0.2 plugin still looked horizontally stretched with PPSSPP Display Layout set to Stretch.

## What the uploaded log proves

The v0.2 log is decisive about several points:

1. The PRX loaded and `module_start` executed.
2. The live Tekken module was found at text address `0x08804000`, size `0x003F62A8`.
3. All four verified ULUS10466 aspect sites were found at the expected runtime addresses.
4. All four sites initially contained the original `16:9` instruction pair.
5. v0.2 wrote `0x3C01400E 0x342138E4` to all four sites and immediate readback succeeded.
6. Shortly afterward, the first site changed from the literal patched `lui` instruction to `0x6806F70C`, while the low `ori` half remained patched.

The important observation is that `0x6806F70C` is not Tekken restoring the original aspect instruction. PPSSPP reserves the `0x68000000` opcode family as `MIPS_EMUHACK_OPCODE` for JIT blocks / emulator-internal translated-code markers. Therefore v0.2's monitor incorrectly classified the first site's normal PPSSPP JIT marker as a game-side reversion.

## Why this still matters for the failed visual result

PPSSPP's own CWCheat implementation calls its JIT/instruction-cache invalidation path **before** reading or writing code memory. The source comment explicitly explains that JIT can overwrite guest instructions with emuhack opcodes and that invalidation is needed even before reads so the original guest instruction is restored.

v0.2 used the opposite ordering for its initial writes:

1. direct guest-memory write
2. data-cache writeback
3. instruction/JIT invalidation

That is not behaviorally identical to PPSSPP CWCheat, despite writing the same instruction words.

The uploaded log therefore changes the diagnosis:

- plugin loading: VERIFIED working
- runtime addresses: VERIFIED correct
- target instruction words: VERIFIED correct
- v0.2 monitor's 'reverted' interpretation: REJECTED; `0x68xxxxxx` is a PPSSPP JIT/emuhack marker
- PRX patch ordering relative to PPSSPP's CWCheat engine: DIFFERENT and now the primary implementation variable to isolate

## v0.3 strategy

v0.3 is intentionally a diagnostic implementation that mirrors PPSSPP CWCheat's ordering more closely:

For each of the four exact ULUS10466 sites:

1. call `sceKernelIcacheInvalidateRange()` first
2. read the restored guest instruction pair
3. require the original or already-target pair
4. write the 20:9 pair
5. call `sceKernelDcacheWritebackRange()`
6. do **not** immediately invalidate the same range again after writing

The plugin repeats this on a configurable interval, default `77 ms`, matching PPSSPP's default CWCheat refresh interval closely. This is intentionally conservative and may be less efficient than the eventual final plugin. Its purpose is to answer one question reliably:

> Can a PRX reproduce the known-good Tekken 6 CWCheat visually when it mirrors CWCheat's code-patching cadence and JIT invalidation order?

## Interpretation of v0.3 test

### If v0.3 now produces the correct 3D view

The failure was primarily a PRX/JIT patching-order/cadence issue. The next version should replace continuous re-patching with a cleaner Warriors-style runtime hook, ideally forcing the aspect value at the live projection input rather than repeatedly modifying four inline constants.

### If v0.3 still looks unchanged

Test the same plugin with `ForceAspectRatio = 4:1` as an exaggerated diagnostic. If even 4:1 causes no visible 3D change while the log shows all four restored/write cycles succeeding, then the four constant sites are not sufficient when modified from a guest PRX at runtime, even though the same addresses work through PPSSPP's internal CWCheat engine. The project should then stop trying to emulate CWCheat and move directly to a Warriors-style projection hook at the actual perspective-builder input (`$f12`) or its active callers.

## HUD status

HUD work remains paused. No HUD candidate should be evaluated until the PRX can visibly reproduce a known-good 3D aspect change.
