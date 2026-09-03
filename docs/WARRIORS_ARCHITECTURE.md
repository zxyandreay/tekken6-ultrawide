# The Warriors Fusion Fix architecture and the Tekken 6 plan

Last updated: 2026-09-03

## Why this reference matters

The Warriors PPSSPP Fusion Fix is useful because its widescreen solution is not a single global framebuffer/stretch patch. The source and Git history show two distinct game-code corrections:

1. a 3D/game aspect-ratio injection, and
2. a separate HUD-scale injection.

That distinction is the key architectural lesson for Tekken 6.

## Verified upstream history

The upstream WidescreenFixesPack history separates the work clearly:

- `ce977af5f2cba397be8e1a517c07a6f8fdc8b83e` — `the warriors: aspect ratio fix` — added `ForceAspectRatio` and an inline patch that supplies the selected aspect through FPU register `$f12`.
- `c93585d934f9562089892ef15ff311e7955799b4` — `the warriors: hud scale` — added a second pattern match and inline patch that supplies the same selected aspect through FPU register `$f1` at a HUD-specific code path.
- Later upstream work changed `auto` so the plugin can query PPSSPP for the actual display aspect ratio using `sceIoDevctl("kemulator:", EMULATOR_DEVCTL__GET_ASPECT_RATIO, ...)`.

The current source retains both independent injections.

## Current Warriors mechanism

Conceptually the plugin does this:

```text
PPSSPP/display aspect
        |
        +--> 3D aspect operand --> game/perspective rendering
        |
        `--> HUD scale operand --> 2D/HUD rendering
```

The relevant current-source logic is equivalent to:

```c
uintptr_t ptr_3d = pattern.get(0, "94 18 C1 E7 03 03 01 46", 4);
MakeInlineWrapper(ptr_3d,
    lui(t9, HIWORD(fAspectRatio)),
    ori(t9, t9, LOWORD(fAspectRatio)),
    mtc1(t9, f12)
);

float fHudScale = fAspectRatio;
uintptr_t ptr_hud = pattern.get(0, "02 00 02 46 00 00 C3 8F", -4);
MakeInlineWrapper(ptr_hud,
    lui(t9, HIWORD(fHudScale)),
    ori(t9, t9, LOWORD(fHudScale)),
    mtc1(t9, f1)
);
```

The important point is not the particular registers `$f12` and `$f1`; those are specific to The Warriors. The important point is that the developer found a live HUD-specific scale/aspect operand separate from the 3D aspect operand.

The plugin therefore does **not** preserve the HUD merely by leaving all 2D drawing untouched. It actively corrects a HUD scaling path.

## Why a PRX plugin is useful instead of only CWCheat

A fixed-address CWCheat could theoretically reproduce a fixed-ratio version if every required address and instruction were already known. The PRX format is not magic by itself.

The plugin is superior for this class of fix because it can:

- pattern-scan game code instead of relying only on brittle absolute offsets,
- inject multi-instruction MIPS snippets and trampolines,
- query PPSSPP for the current display aspect ratio at runtime,
- apply one aspect value to several different engine paths,
- make context/caller-aware decisions if different 2D categories need different treatment,
- validate signatures before patching,
- support multiple builds/regions with different patterns,
- log failures instead of blindly writing an approximate address.

WidescreenFixesPack's PSP injector exposes runtime memory/instruction writes, jumps/calls, NOPs, inline code stubs and trampolines. That is substantially more flexible than a static CWCheat list.

## What this changes for Tekken 6

### 3D side: already largely solved

Tekken 6 already has a verified 3D counterpart to the first Warriors patch. The working 20:9 cheat modifies four aspect-dispatch case-0 constants, and static analysis ties those dispatches to real perspective/camera projection paths.

The future plugin can replace those fixed CWCheat writes with pattern-verified runtime injection and obtain the requested aspect from PPSSPP or from its INI.

### HUD side: the real missing piece

The previous Tekken experiments were aimed too low or too globally:

- individual/broad sprite changes broke health bars and overlays,
- broad viewport/surface-state changes affected full-screen overlays,
- the three obvious 480x272 generic orthographic setup paths A/B/C produced no visible HUD/UI/menu change in user testing.

The Warriors reference says the next target should **not** be another generic `480 -> 600` projection change.

The research target should instead be:

> Find Tekken's equivalent of the Warriors HUD-scale operand: a live float/register/field used by the actual screen-space HUD/sprite renderer to determine horizontal scale/aspect.

That operand may live in a draw descriptor, sprite-batch setup, screen-coordinate conversion function, or higher-level UI renderer rather than in the generic orthographic matrix builder.

## Current Tekken candidate families

Static ranking against the decrypted `ULUS10466_EBOOT.BIN` now highlights two families more strongly than the rejected generic ortho paths:

### Candidate family 1: `0x08A3916C`–`0x08A396D8`

This code repeatedly constructs render/draw-state structures containing PSP-sized dimensions and submits them through common rendering helpers. Notable constants include multiple `480.0` and `272.0` loads. It also contains many floating-point stores and calls into `0x08ACE1E0` / `0x08ACE1F8` / `0x08ADB6A8`.

Status: **HYPOTHESIS / high-priority trace target**, not proven HUD code.

### Candidate family 2: `0x08AA62D8`–`0x08AA655C`

This is another active-looking render-state construction path with repeated `480.0` / `272.0` pairs, floating-point state, and repeated submission through `0x08ACE1E0` and `0x08ADB6A8`.

Status: **HYPOTHESIS / high-priority trace target**, not proven HUD code.

These are more analogous to the sort of live screen-space scale setup we need than the broad viewport function, but caller/data-flow analysis is still required before generating another user diagnostic.

## Planned Tekken plugin architecture

Once the HUD-specific operand/path is verified, the intended plugin should look conceptually like:

```text
Tekken6.PPSSPP.UltrawideFix

requestedAspect = explicit X:Y OR PPSSPP current display aspect

Fix3D:
    pattern-find verified Tekken aspect dispatch sites
    inject requestedAspect into the 3D projection paths

FixHUD:
    pattern-find verified live HUD scale path
    inject/derive HUD compensation there
    avoid changing full-screen overlay/fade behavior unless separately classified
```

Suggested eventual INI:

```ini
[MAIN]
ForceAspectRatio = auto
Fix3D = 1
FixHUD = 1
DebugLogging = 1
```

A fixed `20:9` option can remain available, but `auto` should use PPSSPP's current display-aspect query in the same general way as The Warriors.

## Critical difference to preserve

Do not assume `fHudScale = aspectRatio` is the correct Tekken formula merely because The Warriors uses that relationship. Engine semantics differ.

For Tekken we must first identify what the candidate value means and then derive the correct transformation from its actual data flow. A theoretical 16:9-to-20:9 horizontal compensation of `0.8` is only a mathematical clue, not a patch value until the engine path is understood.

## Why overlays are a special case

The Warriors appears to have a convenient HUD-scale location that produces a good result for that game's 2D presentation. Tekken may be less convenient.

If Tekken's ordinary HUD and full-screen dark/fade overlays share the same low-level sprite path, the final PRX may need caller/context-aware behavior:

- ordinary HUD: compensate horizontal scale/position,
- full-screen overlay: preserve full-output coverage,
- pre-rendered video: generally leave alone unless separately required.

This is another reason to prefer a plugin once the correct path is known.

## Upstream licensing

ThirteenAG/WidescreenFixesPack is MIT licensed. Architectural ideas can be reimplemented independently. If substantial upstream source such as injector/pattern code is copied or adapted, retain the required MIT copyright/license notice and attribution.

## Immediate next work

1. Rank live Tekken screen-space/render-state functions using `tools/find_warriors_style_hud_candidates.py`.
2. Trace callers/data flow for `0x08A3916C`–`0x08A396D8` and `0x08AA62D8`–`0x08AA655C`.
3. Look specifically for a float/register that affects horizontal HUD scale independently of final viewport dimensions.
4. Create a new one-variable diagnostic only after a candidate is strong enough to produce an interpretable visual result.
5. Do not return to A/B/C generic orthographic diagnostics or the broad viewport patch as the main HUD strategy.
