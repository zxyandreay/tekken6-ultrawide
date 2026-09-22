# Origin and early HUD-correction research

## Initial state

HUD research began from a known-good 20:9 3D CWCheat for Tekken 6 USA (ULUS10466).

At this point:

- 3D rendered correctly at 20:9;
- HUD/UI remained stretched under PPSSPP Stretch;
- no plugin existed;
- no HUD transform or HUD-scale path had been identified.

Earlier sprite-level experiments had already produced pause-overlay problems, incorrect or empty health fills, blocky corruption, and inconsistent UI behavior.

The first objective was therefore to find the highest practical level where Tekken converts logical HUD/UI coordinates into output coordinates, rather than patching individual sprites blindly.

## Map the working 3D path first

The four known CWCheat aspect writes were mapped into the decrypted MIPS EBOOT.

The original aspect constant is:

```text
0x3FE38E39 ~= 1.7777778 = 16:9
```

The working 20:9 value is:

```text
0x400E38E4 ~= 2.2222223 = 20:9
```

Tracing these sites established the known perspective/projection path before any HUD changes were attempted.

## Hypothesis 1 — orthographic safe-area projection

A generic orthographic projection builder was identified at:

```text
0x08ACA990
```

Three direct 480x272 setup paths were found.

For a centered 16:9 HUD inside a 20:9 stretched output, the proposed logical width was:

```text
480 * (20/16) = 600
```

with horizontal bounds:

```text
-60 .. 540
```

### Test

Patch each direct orthographic path independently and compare HUD, menus, and overlays.

### Observation

All three isolated paths produced no visible HUD/UI/menu change.

### Conclusion

The visible HUD was not controlled by these three direct orthographic setup paths.

### Next step

Trace live screen-space and sprite-coordinate paths instead of continuing global orthographic experiments.

## Hypothesis 2 — separate HUD scale path

The Warriors PPSSPP widescreen fix was studied as an architectural comparison because it separates:

```text
display aspect
  -> 3D projection path
  -> HUD-specific scale path
```

The useful idea was to search for a Tekken-specific HUD scale or descriptor path independent of the known 3D projection sites.

Static analysis ranked functions that combined:

- 480/272-style screen constants;
- floating-point operations;
- descriptor/state writes;
- renderer/helper calls.

The rankings were used only to choose probe targets; they were not treated as ownership proof.

## First PRX runtime tests

An experimental PRX was introduced to reproduce the known 3D patch and test HUD candidates at runtime.

The first plugin did not reliably reproduce the already-working CWCheat result.

HUD testing was paused until the runtime patch path itself was understood.

The next tests focused on:

- locating the live Tekken code region;
- verifying writes and readback;
- PPSSPP JIT/cache behavior;
- matching the invalidation/order behavior of the working CWCheat path.

### Conclusion

A negative HUD result is meaningful only after the runtime patch mechanism is independently verified.

## Descriptor and property-setter tracing

With the runtime patch path under control, analysis returned to candidate 2D ownership.

The next static probes traced:

- descriptor fields;
- X/Y or scale-like members;
- property setters;
- helper functions that construct or submit 2D state.

A focused trace followed likely X/Y scale setters and related 2D property helpers.

These tests narrowed the candidate space but did not establish one universal HUD-scale owner.

## Hypothesis 3 — native PSP 2D presentation path

A native PSP 2D presentation/viewport path was then traced through:

- the presentation setup;
- a transform trampoline;
- the flat viewport owner;
- a centered safe-area hook.

This provided another high-level place to test a 16:9 safe-area transform.

It did not become the complete battle-HUD solution, so the research moved further down the rendering stack.

## Direct battle-HUD ownership mapping

The next phase stopped asking for one global HUD transform and instead identified the owners of visible battle elements.

### HUD Path Map

`Tekken6-HUD-PathMap-v1` redirected selected draw calls through an exaggerated +32 PSP-pixel X shift.

The purpose was ownership identification, not final scaling.

A known HP-fill path served as a control while other candidate calls were tested independently.

### Result

The visible HP fill renderer was identified at:

```text
0x0892D56C
0x0892D5B0
```

The other MAP 1–5 candidates did not move the visible fight HUD.

This established that the colored HP fill had a narrow renderer path that could be studied separately.

## Orthographic compositor-group mapping

`Tekken6-HUD-Ortho-GroupMap-v3` independently suppressed compositor groups:

```text
9, 10, 12, 13, 14, 15, 16, 17
```

### Result

Group 10 hid the health bars.

This linked a compositor group to health-bar presentation, but did not yet identify the individual shell/fill owners inside that presentation.

## Group 10 safe-area tests

Two tests applied a centered 16:9 projection specifically around Group 10.

### First test

Install the safe-area projection before the Group 10 render block.

### Second test

Move the projection change to the Group 10 draw-list call and add an exaggerated 50%-width diagnostic.

### Result

Not recorded in the experiment notes.

The research subsequently moved to battle-object ownership instead of continuing group-wide projection changes.

## CMain / CGauge ownership

The next diagnostic mapped battle objects directly.

Static ownership:

```text
tk::sprite::battle::CGaugeTcb_t::Draw = 0x0892C124
tk::sprite::battle::CMainTcb_t::Draw  = 0x0892BDAC
```

The test suppressed individual CMain sub-renderers to identify the static HP frame/trough around the already-confirmed CGauge fill.

This was the point where the HUD model changed from “one 2D layer” to a set of independent render families with different owners.

## Working method from this point

The rest of the HUD correction followed the same pattern:

1. identify one visible family;
2. prove its owner;
3. capture authored geometry;
4. determine LEFT/CENTER/RIGHT semantics;
5. patch only that owner/path;
6. verify unrelated HUD and overlays remain unchanged.

That method led to the later HP shell/fill, side strip/rank, round marker, winner glow, timer, character-name, Practice/Gold Rush, and AutoHUD work.
