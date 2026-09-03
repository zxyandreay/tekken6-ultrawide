# Tekken 6 PPSSPP Ultrawide Fix — v0.3 CWCheat-order diagnostic

Last updated: 2026-09-03

## Why this build exists

The v0.2 PRX definitely loaded, found the correct live Tekken module, found the same four addresses used by the working CWCheat, and initially wrote the exact 20:9 instruction pairs successfully. However, the user's 3D view still looked stretched.

The uploaded v0.2 log also exposed a PPSSPP-specific detail: the first patched instruction later became `0x6806F70C`. This is not Tekken restoring the original aspect code. PPSSPP reserves `0x68000000` opcodes as JIT/emuhack markers placed into guest code at compiled block starts.

PPSSPP's own CWCheat engine invalidates JIT/instruction-cache state **before** reading or writing a cheat code address. v0.2 wrote first and invalidated afterward.

v0.3 therefore answers one narrower question:

> If the PRX mirrors PPSSPP CWCheat's invalidation-before-write ordering and continuously reapplies the four known-good aspect writes at approximately the same cadence, does the 3D view finally match the known-good CWCheat?

HUD correction is still intentionally disabled.

## Install

Replace the entire previous plugin folder with the v0.3 package so these files exist:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
├── Tekken6.PPSSPP.UltrawideFix.prx
├── Tekken6.PPSSPP.UltrawideFix.ini
└── plugin.ini
```

Supported game:

```text
ULUS10466
```

## Supplied configuration

```ini
[MAIN]
ForceAspectRatio = 20:9
Enable3D = 1
PatchIntervalMs = 77
DebugLogging = 1
```

`PatchIntervalMs = 77` intentionally approximates PPSSPP's default CWCheat refresh interval for this diagnostic build.

## PPSSPP test conditions

1. Disable the existing Tekken 6 ultrawide CWCheat.
2. Keep PPSSPP Display Layout = `Stretch`.
3. Ensure `Enable plugins` is enabled for Tekken 6.
4. Fully close PPSSPP.
5. Do not manually load an old savestate for the first test.
6. Launch Tekken 6 normally and enter a fight.
7. Compare character proportions and visible horizontal field of view against the known-good CWCheat result.

## Expected log header

```text
=== Tekken6.PPSSPP.UltrawideFix v0.3 CWCheat-order diagnostic ===
Plugin module_start reached successfully
```

The plugin first invalidates each exact aspect site so PPSSPP can restore any JIT/emuhack first opcode before it inspects the code.

The initial restored words should be the original pair:

```text
0x3C013FE3 0x34218E39
```

Then the patch thread should report four writes using the 20:9 pair:

```text
0x3C01400E 0x342138E4
```

followed by:

```text
3D: first CWCheat-order cycle patched all four sites
```

## Important: do not interpret 0x68xxxxxx as a Tekken code reversion

PPSSPP can replace the first guest instruction of a compiled JIT block with an internal `0x68xxxxxx` emuhack marker. The v0.2 monitor treated this as a failure; that interpretation was wrong.

v0.3 does not attempt to verify correctness by expecting literal patched opcodes to remain visible at all times. Instead, before each repeated write it asks PPSSPP to invalidate the relevant code range first, matching CWCheat's ordering more closely.

## If 20:9 still looks unchanged

Do one exaggerated diagnostic without changing the PRX:

Edit:

```ini
ForceAspectRatio = 20:9
```

to:

```ini
ForceAspectRatio = 4:1
```

Fully close PPSSPP and launch Tekken again.

A 4:1 projection value should create an unmistakably different 3D view if these four live code sites are actually governing the active rendering path under PRX-side patching.

### Result interpretation

- **20:9 works:** PRX foundation is proven. Resume HUD-scale research.
- **20:9 seems uncertain, but 4:1 visibly changes the 3D view:** PRX patching works; the remaining issue is choosing the correct compensation/aspect behavior, not plugin loading.
- **Even 4:1 produces no visible change while the log says all four sites are patched:** stop emulating CWCheat writes. Move to a true Warriors-style runtime hook that forces the aspect value at the live perspective projection input (`$f12`) or the active call sites.

## What to send back

After the v0.3 test, send:

```text
PSP/PLUGINS/Tekken6.PPSSPP.UltrawideFix/
Tekken6.PPSSPP.UltrawideFix.log
```

and state:

```text
20:9: changed / unchanged
4:1: changed / unchanged   (only if 20:9 remains uncertain)
```

A gameplay screenshot for each tested ratio is useful but optional.

## HUD status

No HUD fix is active in v0.3. HUD work resumes only after a PRX can produce a visually confirmed 3D aspect change.
