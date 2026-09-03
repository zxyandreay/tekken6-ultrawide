# Status

Last updated: 2026-09-03

## Current Phase

Phase 6C: reproduce PPSSPP CWCheat's JIT invalidation/write behavior from a PRX before resuming HUD work.

## What is verified

- Tekken 6 USA `ULUS10466`.
- `ULUS10466_EBOOT.BIN` is a decrypted 32-bit little-endian MIPS ELF suitable for static analysis.
- The known-good 20:9 CWCheat visually fixes the 3D view on the user's POCO F5 when PPSSPP Display Layout is set to Stretch.
- The four exact CWCheat/runtime aspect sites are:
  - `0x08945F10`
  - `0x08946794`
  - `0x08946BC8`
  - `0x08947D90`
- Original instruction pair at each site:
  - `0x3C013FE3`
  - `0x34218E39`
- Exact 20:9 pair:
  - `0x3C01400E`
  - `0x342138E4`
- Generic orthographic Paths A/B/C were user-tested visible no-ops for HUD/UI/menu screens.
- The Warriors Fusion Fix uses separate 3D aspect and HUD-scale hooks; Tekken still needs its actual HUD-scale equivalent identified.

## v0.1 result

FAILED/UNVERIFIED. Both 3D and HUD appeared stretched. It used fixed addresses and mixed HUD experiments into the first PRX test.

## v0.2 result and uploaded log

The user's v0.2 log proves:

1. the PRX loaded successfully,
2. the live Tekken module was present at `0x08804000`, size `0x003F62A8`,
3. all four exact aspect sites were found correctly,
4. all four sites initially contained the original pair,
5. all four sites were written to the exact 20:9 pair and immediate readback succeeded,
6. the first site's high word later became `0x6806F70C` while the low word remained patched.

The important correction is that `0x6806F70C` is not a Tekken-side reversion. PPSSPP reserves the `0x68000000` opcode family for JIT/emuhack block markers. Therefore v0.2's monitor incorrectly interpreted normal PPSSPP JIT behavior as a restored/changed game instruction.

See `docs/PLUGIN_V02_LOG_ANALYSIS.md`.

## Why v0.3 exists

PPSSPP's own CWCheat engine invalidates JIT/instruction-cache state **before** reading/writing a cheat code address. v0.2 wrote first, then invalidated.

v0.3 changes the order to mirror CWCheat more closely:

1. `sceKernelIcacheInvalidateRange()` first,
2. inspect the restored guest instruction,
3. write the requested aspect pair,
4. `sceKernelDcacheWritebackRange()`,
5. repeat continuously at a configurable cadence (default 77 ms).

This deliberately prioritizes behavioral equivalence with the known-good CWCheat over elegance. If it works visually, the next version should replace repeated writes with a cleaner Warriors-style hook.

## Current v0.3 package

Supplied INI:

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1
PatchIntervalMs = 77
DebugLogging = 1
```

HUD correction is still disabled.

## Required user test

1. Disable the Tekken widescreen CWCheat.
2. Keep PPSSPP Display Layout = Stretch.
3. Enable plugins for Tekken 6.
4. Cold boot the game and enter a fight.
5. Test v0.3 at `20:9`.
6. If the 20:9 result is still visually unchanged/uncertain, edit only:

```ini
ForceAspectRatio = 4:1
```

and cold boot again.

Interpretation:

- 20:9 correct: PRX runtime foundation proven; resume HUD research.
- 4:1 visibly changes 3D: PRX patching is active; investigate aspect semantics/compensation.
- 4:1 still no visible change while the log reports successful cycles: stop emulating CWCheat writes and move to a true Warriors-style projection hook at the live `$f12` perspective input or active callers.

After testing, send the new plugin log. Detailed steps are in `docs/PLUGIN_TEST.md`.
