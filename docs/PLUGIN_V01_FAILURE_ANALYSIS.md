# First plugin visual failure analysis

Last updated: 2026-09-03

## User result

The first `Tekken6.PPSSPP.UltrawideFix` build was tested on the target POCO F5 with PPSSPP Stretch.

Observed result:

- `HUDMode = 0`: 3D still appeared horizontally stretched; HUD/UI also stretched.
- `HUDMode = 1`: 3D still appeared horizontally stretched; HUD/UI also stretched.

Therefore the first PRX did **not** successfully reproduce the known-good CWCheat 3D correction in the user's runtime. Because the verified CWCheat does correct the 3D scene on the same game/build, HUD conclusions from that PRX are not trustworthy until plugin loading and 3D runtime patching are proven.

## What was wrong with the confidence level of v0.1

The v0.1 source compiled successfully, but compilation did not prove that its writes were reaching and remaining in the live Tekken module. The implementation had several weaknesses compared with The Warriors Fusion Fix architecture:

1. It used four fixed absolute addresses instead of locating the live game module and pattern/signature-scanning its text.
2. It patched only once at `module_start` and had no delayed readback to prove the instructions remained patched during early boot.
3. Its log did not explicitly prove that PPSSPP had started the PRX before performing the game-code logic.
4. It mixed an unverified HUD experiment into the first runtime build before the PRX 3D path itself had been independently validated.
5. It did not record the loaded module list/text ranges, so a relocation/load-timing mismatch could not be diagnosed from the user's result alone.

These are implementation/diagnostic shortcomings. They do not invalidate the static address mapping: the repository independently verified that the known CWCheat maps to the four instruction pairs in the decrypted ULUS10466 EBOOT. The missing proof was that the PRX was finding and modifying the corresponding **live runtime code** on the user's PPSSPP session.

## PPSSPP/plugin facts checked after the failed test

Current PPSSPP plugin loading code:

- discovers PRX plugins through `PSP/PLUGINS/<plugin>/plugin.ini`,
- matches the current DISC_ID from `[games]`,
- requires the per-game plugin setting to be enabled,
- starts the PRX before allowing the waiting game module to continue,
- displays a `Loaded plugin: ...` OSD message when startup succeeds.

The manifest format used by this project matches the same general format as The Warriors plugin (`type = prx`, filename, nonzero version, `memory = 93`, and `ULUS10466 = true`).

PPSSPP also exposes `sceKernelIcacheInvalidateRange`; its HLE implementation invalidates the corresponding translated/JIT code range. The revised plugin uses this precise range invalidation after every modified instruction pair instead of relying only on a broad global cache call.

## v0.2 diagnostic correction

The revised plugin now follows the important Warriors-style architectural idea more closely:

### 1. Locate the live game module instead of assuming its base

At runtime it calls:

- `sceKernelGetModuleIdList`
- `sceKernelQueryModuleInfo`

and records module names, text addresses, and text sizes in the plugin log.

### 2. Find the verified 3D aspect sites by signature

The four known aspect case-0 pairs have a verified relative layout:

- site 1: `+0x0000`
- site 2: `+0x0884`
- site 3: `+0x0CB8`
- site 4: `+0x1E80`

Each site is originally:

```text
0x3C013FE3
0x34218E39
```

For 20:9 each should become:

```text
0x3C01400E
0x342138E4
```

v0.2 scans loaded executable text for this four-site relative signature. Only after that signature is verified does it write the requested aspect.

A fixed ULUS10466-address fallback still exists, but it is allowed only if **all four known addresses already contain either the original pair or the requested target pair**. It does not blindly write unknown memory.

### 3. Immediate readback

After each write v0.2 reads the two instructions back and logs the exact values. A successful build must report four successful readbacks.

### 4. Precise JIT/I-cache invalidation

After each 8-byte instruction pair:

```c
sceKernelDcacheWritebackRange(address, 8);
sceKernelIcacheInvalidateRange(address, 8);
```

is used so PPSSPP invalidates translated code specifically for the patched range.

### 5. Early-boot verification

A short diagnostic worker checks the four sites every 250 ms during the first few seconds of boot. If the instructions are restored/changed, it logs that fact and attempts to reapply the verified patch.

This is primarily diagnostic. It will tell us whether startup order or another runtime action is undoing the patch.

### 6. Fresh startup proof

v0.2 deletes the prior plugin log and writes this immediately when `module_start` is reached:

```text
=== Tekken6.PPSSPP.UltrawideFix v0.2 runtime diagnostic ===
Plugin module_start reached successfully
```

If a new log with that header does not appear, the PRX did not start and the problem is installation/PPSSPP plugin loading rather than Tekken's aspect code.

## HUD status after the failure

HUD correction is intentionally disabled in v0.2.

The previous `HUDMode` candidates are still only static hypotheses. It is not useful to interpret their visual behavior while the PRX has not yet proven that it can reproduce the already-known working 3D patch.

Correct order now:

1. prove PRX is loaded,
2. prove live four-site 3D writes/readback,
3. prove 3D visually matches the known-good CWCheat,
4. only then resume Warriors-style HUD-scale tracing and runtime testing.

## Required user evidence from v0.2

For the next test, use a cold game boot (no manual/automatic savestate load for the first diagnostic) and provide:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log
```

That log will distinguish among:

- plugin never loaded,
- config not found,
- live Tekken module/signature not found,
- write/readback failure,
- early-boot patch reversion,
- successful runtime patch but unexpected visual behavior.

Until that evidence is available, the exact cause of the v0.1 visual no-op should be treated as unresolved rather than guessed.
