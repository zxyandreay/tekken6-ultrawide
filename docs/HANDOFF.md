# Handoff

Last updated: 2026-09-03

## Current objective

Prove whether a PPSSPP guest PRX can reproduce the known-good Tekken 6 20:9 CWCheat when it mirrors PPSSPP CWCheat's JIT invalidation/write ordering and refresh cadence. Do not resume HUD implementation until that is visually proven.

## Game / baseline

- Tekken 6 USA
- Disc ID `ULUS10466`
- Target device: POCO F5, 2400x1080, 20:9
- PPSSPP Display Layout: Stretch

Known-good CWCheat runtime pair starts:

- `0x08945F10`
- `0x08946794`
- `0x08946BC8`
- `0x08947D90`

Original pair:

```text
0x3C013FE3
0x34218E39
```

20:9 pair:

```text
0x3C01400E
0x342138E4
```

The CWCheat is user-verified to visually correct the 3D view.

## Plugin v0.1

FAILED/UNVERIFIED. 3D and HUD still looked stretched. Mixed unproven HUD experiments with an unproven PRX code-write path.

## Plugin v0.2 — decisive uploaded log

The user uploaded `Tekken6.PPSSPP.UltrawideFix.log` from v0.2.

The log proves:

1. `module_start` executed.
2. Live game module: `tekken`, text `0x08804000`, size `0x003F62A8`.
3. All four expected aspect sites were found correctly.
4. All four initially contained the original 16:9 pair.
5. All four were written to the exact 20:9 pair and immediate readback succeeded.
6. Shortly afterward the first site's high instruction appeared as `0x6806F70C`; the other words remained patched.

Important correction:

`0x6806F70C` is a PPSSPP JIT/emuhack marker, not Tekken restoring the original instruction. PPSSPP reserves the `0x68000000` opcode family as `MIPS_EMUHACK_OPCODE` for compiled/JIT block markers. Therefore v0.2's monitor incorrectly classified normal JIT behavior as a game-side reversion.

See:

- `docs/PLUGIN_V02_LOG_ANALYSIS.md`
- PPSSPP `Core/MIPS/MIPS.h`
- PPSSPP `Core/CwCheat.cpp`

## PPSSPP CWCheat behavior that v0.2 did not match

PPSSPP's CWCheat engine invalidates JIT/instruction-cache state before reading/writing a code-memory cheat address. Its source comments explain that JIT may overwrite guest instructions and that invalidation is required even before reads to restore them.

v0.2 wrote the pair first and invalidated afterward. It also only maintained the patch for a short diagnostic window.

## Plugin v0.3 — current implementation

`plugin/main.c` is now v0.3.

For each exact ULUS10466 site it performs:

1. `sceKernelIcacheInvalidateRange(address, 8)` FIRST,
2. read the restored guest instruction pair,
3. require original or already-target words,
4. write the requested aspect pair,
5. `sceKernelDcacheWritebackRange(address, 8)`,
6. no immediate post-write I-cache invalidation,
7. repeat continuously at `PatchIntervalMs` (default 77 ms).

This deliberately mimics PPSSPP's CWCheat ordering/cadence more closely than v0.2. It is diagnostic rather than intended final architecture.

Supplied INI:

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1
PatchIntervalMs = 77
DebugLogging = 1
```

GitHub Actions build for manifest v0.3 completed successfully.

## Next user test

Install v0.3, disable the old widescreen CWCheat, cold boot Tekken, PPSSPP Stretch, enter a fight.

Test `20:9` first.

If the visual result still appears unchanged, edit only:

```ini
ForceAspectRatio = 4:1
```

cold boot again and compare. 4:1 is an intentionally extreme diagnostic.

## Interpretation

### 20:9 visually matches the known-good CWCheat

PRX-side code patching foundation is proven. Stop repeated CWCheat-style writes and implement a cleaner runtime projection hook. Then resume HUD-scale tracing.

### 20:9 uncertain, 4:1 visibly changes 3D

PRX code writes are active. Investigate projection/aspect semantics or exact compensation rather than plugin loading.

### 4:1 still produces no visible 3D change while log reports successful repeated cycles

Do not spend more time emulating CWCheat writes. Move directly to a Warriors-style injection at Tekken's live perspective input.

Current best projection target from static analysis:

- generic perspective builder: `0x08ACA6C4`
- `$f12` is used as the aspect divisor in the builder
- known direct calls: `0x08863D20`, `0x08863D84`, `0x089467A8`, `0x08955494`

The next clean architecture should force the requested aspect at the active `$f12` path (or active callers) using a trampoline/inline wrapper, analogous in concept to The Warriors Fusion Fix, rather than repeatedly modifying inline switch constants.

## HUD status

Paused.

The generic orthographic 480x272 paths A/B/C were user-tested visible no-ops. The long-term objective is still to identify Tekken's true HUD-scale path, separate from full-screen masks/overlays, analogous to The Warriors' independent HUD scale injection.
