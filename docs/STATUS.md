# Status

Last updated: 2026-09-03

## Current Phase

Phase 6B: diagnose why the first PPSSPP PRX build did not reproduce the already-known working 3D CWCheat before doing any further HUD experimentation.

## User-verified result of plugin v0.1

Target:

- Tekken 6 USA `ULUS10466`
- POCO F5 2400x1080 / 20:9
- PPSSPP Display Layout = Stretch

Result:

- `HUDMode = 0`: both 3D and HUD/UI still appeared horizontally stretched.
- `HUDMode = 1`: both 3D and HUD/UI still appeared horizontally stretched.

This means v0.1 did **not** prove that its runtime writes reached/remained in the live Tekken executable. The previously stated confidence in the PRX 3D path was therefore too high. The static EBOOT/CWCheat mapping remains verified, but the first PRX runtime implementation is now classified as FAILED/UNVERIFIED.

## What remains verified

- `ULUS10466_EBOOT.BIN` is a decrypted 32-bit little-endian MIPS ELF suitable for static analysis.
- The known-good CWCheat maps to four exact aspect case-0 instruction pairs in the EBOOT.
- The four verified runtime addresses for the tested ULUS10466 build are:
  - `0x08945F10`
  - `0x08946794`
  - `0x08946BC8`
  - `0x08947D90`
- Original pair at every site:
  - `0x3C013FE3`
  - `0x34218E39`
- Exact POCO F5 20:9 pair:
  - `0x3C01400E`
  - `0x342138E4`
- The known CWCheat visually fixes the 3D view when enabled.
- Generic orthographic Paths A/B/C were user-tested no-ops for visible HUD/UI/menus.
- The Warriors Fusion Fix architecture uses separate live 3D-aspect and HUD-scale paths; Tekken still needs its actual HUD-scale equivalent identified.

## v0.1 implementation weaknesses now acknowledged

Compared with The Warriors architecture, v0.1:

- used fixed absolute game-code addresses,
- did not identify the live Tekken module,
- did not pattern/signature-scan the live module text,
- did not prove post-write instruction persistence during early boot,
- mixed unverified HUD candidates into the first plugin test before the PRX 3D path had been independently proven.

See `docs/PLUGIN_V01_FAILURE_ANALYSIS.md`.

## v0.2 diagnostic plugin

The source has been revised to isolate and prove the runtime 3D path first.

v0.2 now:

1. creates a fresh log immediately when `module_start` is reached,
2. enumerates loaded PSP modules with `sceKernelGetModuleIdList`,
3. logs module names/text addresses/text sizes,
4. scans executable text for the verified four-site aspect signature using relative offsets:
   - `+0x0000`
   - `+0x0884`
   - `+0x0CB8`
   - `+0x1E80`
5. uses the fixed ULUS10466 addresses only as a four-site signature-checked fallback,
6. writes the requested aspect only after verification,
7. uses `sceKernelDcacheWritebackRange` + `sceKernelIcacheInvalidateRange` for each 8-byte code pair,
8. immediately reads each pair back and logs the exact values,
9. verifies/reapplies the four pairs during the first few seconds of boot to expose early reversion/load-order problems.

HUD correction is deliberately disabled in this build. It will not resume until v0.2 proves that the PRX itself reproduces the known-good 3D patch.

## Required next user test

Use the newly built v0.2 package with:

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1
DebugLogging = 1
```

Requirements:

- disable the Tekken CWCheat for the test,
- PPSSPP Stretch,
- cold boot the game,
- do not manually load a savestate and disable auto-load savestate for this diagnostic if enabled.

After launch, send:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/Tekken6.PPSSPP.UltrawideFix.log
```

If that fresh log does not exist, diagnose PPSSPP plugin loading/install location/settings rather than Tekken rendering.

If the log shows all four target pairs present and stable but the 3D view is still stretched, then the next investigation must compare the PRX runtime/JIT behavior against PPSSPP's CWCheat invalidation path rather than guessing at HUD code.
