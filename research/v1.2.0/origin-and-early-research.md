# Origin and early HUD-correction research

This document preserves the earliest recoverable HUD-correction research from the original repository history.

It is based on the old commits themselves and retained diagnostic packages. Where a result is not recoverable, the text says so rather than inferring an outcome.

## Earliest preserved baseline

The first research commit, f720d0157face81618f9b818e3d763977e55a6ae, records the actual starting point.

At that point:

- Tekken 6 USA (ULUS10466) had a known-good 20:9 3D CWCheat;
- PPSSPP was used with Stretch layout;
- the 3D scene could be widened correctly;
- HUD/UI remained stretched;
- no plugin source existed yet;
- no HUD transform had been identified.

The original HUD research goal was to find the highest practical level where Tekken 6 converts logical HUD, UI, or screen-space coordinates into output coordinates, so HUD/UI proportions could be preserved independently from 20:9 3D rendering.

The same baseline records an important historical negative result supplied before the repository work began: earlier individual-sprite/2D manipulation had caused pause-overlay problems, empty or incorrect health fills, blocky corruption, and inconsistent UI behavior.

That is why the research initially preferred a higher-level screen-space or projection solution over per-element patching.

## Mapping the known 3D patch first

The next work mapped the known CWCheat writes into the decrypted MIPS EBOOT and established the four 3D aspect sites.

The original 16:9 constant is approximately 0x3FE38E39 = 1.7777778. The known 20:9 cheat constant is approximately 0x400E38E4 = 2.2222223.

The four sites were then traced into perspective/projection code so the already-working 3D behavior could be understood before HUD work changed anything else.

## First HUD hypothesis: orthographic projection

The early branch identified a generic orthographic projection builder at 0x08ACA990 and three direct 480x272 setup paths.

For 20:9, the centered-safe-area hypothesis used a 600-unit virtual width with bounds -60..540. This was mathematically consistent with mapping the original 0..480 HUD into a centered 16:9 region after PPSSPP Stretch.

The branch deliberately tested the three orthographic paths independently.

Recovered result from the old research commits: all three isolated orthographic-path tests produced no visible change in HUD/UI/menus.

That rejected the first high-level hypothesis and the research explicitly pivoted from generic orthographic projection to the live screen-space/sprite coordinate path.

## Separate 3D and HUD correction architecture

The branch then studied The Warriors PPSSPP widescreen fix as an architectural reference.

The useful lesson was architectural rather than address-specific: a working widescreen implementation can use one game path for 3D projection and a separate HUD-specific scale path.

This motivated a search for Tekken-specific HUD scale, descriptor, and setter paths instead of assuming one global framebuffer or orthographic transform.

## Warriors-style HUD candidate ranking

Static analysis ranked functions that combined PSP-like 480/272 constants, floating-point setup, descriptor/state writes, and renderer/helper calls.

The highest-ranked candidates were traced more deeply. Candidate ranking was explicitly treated as evidence for where to probe, not proof of HUD ownership.

## First PRX/plugin experiments

An experimental PRX was added so the known 3D writes and HUD hypotheses could be tested at runtime.

The first plugin did not reproduce the already-known CWCheat behavior reliably. The branch therefore stopped HUD testing and diagnosed plugin execution first.

Recovered commits show a sequence of runtime verification, PPSSPP JIT/cache-order investigation, and a CWCheat-order diagnostic.

This established a critical rule: the runtime patch mechanism itself had to be proven before a negative HUD result could mean anything.

## Descriptor and property-setter tracing

After the runtime path was better understood, the branch returned to HUD ownership.

Static analysis traced candidate descriptor fields, X/Y or scale-like fields, property setters, and helper functions that construct or submit 2D state.

A focused v0.5 trace followed candidate HUD scale setters and 2D property helpers.

The exact device outcome for every intermediate candidate is not recoverable, so the current documentation does not promote any of them to validated HUD owners.

Their value was narrowing the search away from broad projection guesses and toward live 2D data flow.

## Native PSP 2D presentation path

The next phase traced a native PSP 2D presentation/viewport path.

Recovered commits show: trace native PSP 2D presentation path; run native 2D safe-area trace; follow native 2D transform trampoline; classify live flat viewport owner; add native PSP 2D safe area.

This proves that another high-level safe-area candidate was implemented and investigated. The recovered evidence does not justify claiming that this alone solved the battle HUD.

The later work moved to much narrower battle-HUD ownership tests.

## Transition to direct battle-HUD path mapping

Once the automatic 3D plugin was established, the research began mapping the battle HUD with controlled draw-call diagnostics.

### HUD Path Map

The retained Tekken6-HUD-PathMap-v1 package redirected selected 2D draw calls through a +32 PSP-pixel X-shift wrapper.

It did not attempt final scaling. It asked only which visible HUD element was owned by each exact call.

The retained CMain follow-up records the key result:

0x0892D56C / 0x0892D5B0 = visible HP fill renderer

and records that the old MAP 1-5 candidates did not affect the visible fight HUD.

### Orthographic UI group mapping

The retained Ortho-GroupMap-v3 package independently suppressed compositor groups 9, 10, 12, 13, 14, 15, 16 and 17.

A later retained test note records that Group 10 hides the health bars.

This linked a compositor group to health-bar presentation without assuming it owned every sub-element.

### Group 10 safe-area candidates

Two retained tests then attempted a centered 16:9 projection specifically around Group 10.

One installed the safe-area projection before the Group 10 render block. A follow-up moved the change to the Group 10 draw-list call and also supplied an exaggerated 50%-width diagnostic.

These artifacts prove the hypothesis and test design. Their exact user-visible result is not preserved strongly enough in the recovered evidence to state a final conclusion here.

### CMain path mapping

The retained CMain diagnostic records:

- tk::sprite::battle::CGaugeTcb_t::Draw = 0x0892C124
- tk::sprite::battle::CMainTcb_t::Draw = 0x0892BDAC

The experiment suppressed individual CMain sub-renderers to identify the shell/trough/frame around the already-confirmed CGauge fill.

This marks the transition from broad UI-group hypotheses to battle-object ownership.

## What changed after this point

From this stage onward, the successful research strategy became increasingly local:

- identify the visual family;
- prove its owner;
- capture authored geometry;
- determine LEFT/CENTER/RIGHT semantics;
- patch only the narrow path that owns it;
- regression-test unrelated HUD and overlays.

The later fight-HUD, timer, winner-glow, character-name, Practice/Gold, memory-footprint, and AutoHUD investigations are documented in the rest of the v1.2.0 archive.

The important historical point is that the project did not begin from a finished fixed-ratio HUD implementation.

It began from a known-good 3D-only patch with unknown HUD ownership, then moved through failed high-level projection hypotheses, screen-space/descriptor/native-2D tracing, direct battle-HUD ownership mapping, per-family correction, and only later automatic HUD generalization.
