# Handoff

Last updated: 2026-09-03

## Current Objective

Prove why the first Tekken 6 PPSSPP PRX did not reproduce the already-known working 20:9 CWCheat on the user's POCO F5, then resume HUD research only after the PRX 3D path is proven.

## Latest user result

The user tested the first plugin build with both `HUDMode = 0` and `HUDMode = 1`.

Observed:

- 3D remained horizontally stretched in both cases.
- HUD/UI remained horizontally stretched in both cases.

This invalidates the earlier assumption that the first PRX 3D path was already runtime-proven. Treat plugin v0.1 as FAILED/UNVERIFIED.

The static analysis remains valid: the existing CWCheat is still the known-good visual baseline.

## Verified 3D baseline

Game:

- Tekken 6 USA
- Disc ID `ULUS10466`

Known-good CWCheat 20:9 writes:

- `0x20145F10 -> 0x3C01400E`
- `0x20145F14 -> 0x342138E4`
- `0x20146794 -> 0x3C01400E`
- `0x20146798 -> 0x342138E4`
- `0x20146BC8 -> 0x3C01400E`
- `0x20146BCC -> 0x342138E4`
- `0x20147D90 -> 0x3C01400E`
- `0x20147D94 -> 0x342138E4`

Mapped runtime pair starts:

- `0x08945F10`
- `0x08946794`
- `0x08946BC8`
- `0x08947D90`

Relative layout from first site:

- `+0x0000`
- `+0x0884`
- `+0x0CB8`
- `+0x1E80`

Original pair at all four sites:

```text
0x3C013FE3
0x34218E39
```

20:9 pair:

```text
0x3C01400E
0x342138E4
```

## Why plugin v0.1 was not sufficient

It compiled, but it did not establish runtime proof. Important shortcomings:

- fixed absolute addresses rather than live module discovery/pattern scanning,
- no log of loaded game-module text address/size,
- no immediate exact readback of all four modified pairs,
- no delayed verification to catch startup reversion,
- unverified HUD writes were mixed into the first plugin test.

See `docs/PLUGIN_V01_FAILURE_ANALYSIS.md`.

## v0.2 implementation now in repository

`plugin/main.c` has been rewritten around a runtime verification path inspired by the important part of The Warriors architecture: locate the live game code and patch only verified signatures.

### Startup proof

The plugin removes the previous log and immediately writes:

```text
=== Tekken6.PPSSPP.UltrawideFix v0.2 runtime diagnostic ===
Plugin module_start reached successfully
```

If a fresh file containing this header does not exist after launch, the PRX did not start. Investigate:

- wrong PPSSPP memstick folder,
- plugins disabled for the game,
- plugin load failure,
- wrong/unsupported DISC_ID.

### Module discovery

v0.2 calls:

- `sceKernelGetModuleIdList`
- `sceKernelQueryModuleInfo`

and logs module names, `text_addr`, and `text_size`.

### Live four-site signature

Instead of assuming a fixed module base, it searches sufficiently large loaded module text for four original/target aspect pairs at the verified relative spacing above.

Only a complete four-site signature is accepted.

### Safe fallback

The known ULUS10466 absolute addresses remain only as a fallback. The plugin first verifies all four contain either the exact original or exact requested pair. If any one fails, no fallback write occurs.

### Patch/JIT handling

For each 8-byte pair:

```c
sceKernelDcacheWritebackRange(address, 8);
sceKernelIcacheInvalidateRange(address, 8);
```

PPSSPP's current HLE implementation maps `sceKernelIcacheInvalidateRange` to deferred invalidation of the translated/JIT code range.

The plugin then reads both instructions back and logs them.

### Early-boot monitor

A short worker checks the four sites every 250 ms for roughly three seconds. If the target pair is changed/reverted, it logs the event and reapplies the verified patch while the diagnostic thread remains alive.

This exists to expose startup order/reversion issues. It is not yet intended as the final plugin architecture.

## HUD status

HUD correction is disabled in v0.2.

Do not interpret or resume the old `HUDMode` A/B experiments until the PRX successfully reproduces the known-good 3D baseline.

The long-term HUD objective remains finding Tekken's equivalent of The Warriors' separate HUD-scale operand/path. The A/B/C generic orthographic paths remain user-tested no-ops for visible HUD/UI/menus.

## Next user test

Use the new v0.2 artifact.

Configuration:

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1
DebugLogging = 1
```

Test conditions:

- old Tekken widescreen CWCheat disabled,
- PPSSPP Display Layout = Stretch,
- cold game boot,
- no manual savestate load,
- disable auto-load savestate for this diagnostic if enabled.

Then obtain:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log
```

## How to interpret the next log

### No fresh log

PRX did not start. Fix plugin install/loading first.

### Header exists but four-site signature not found

The user's live executable layout differs from the static build assumptions, or module discovery/loading is not what expected. Use logged module addresses/sizes and pre-scan known-address pairs to resolve it.

### Four writes/readbacks succeed but monitor reports reversion

Something after `module_start` is restoring/changing the code. Investigate startup sequencing/savestate behavior.

### Four writes/readbacks succeed and remain stable, but 3D is still visually stretched

This is the most important unexpected case. Compare PPSSPP CWCheat execution/JIT invalidation semantics with PRX writes and verify the actual active projection path/runtime code. Do not jump to HUD work.

### 3D visually matches the CWCheat

The plugin loader/3D path is proven. Resume Warriors-style HUD-scale tracing from the static candidate research.
