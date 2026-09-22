# Transient-UI Research / Probe Workflow

**Status:** ACTIVE RESEARCH / PREPARATION

Reusable debugger utilities now live under `tools/research/probes/`.

This is the preferred operating procedure for the next HUD-correction study.

The objective is to identify renderer ownership before writing a patch.

---

## 1. Prepare clean controls

Use Tekken 6 USA:

```text
ULUS10466
```

Record:

- PPSSPP version/build;
- device;
- display aspect;
- graphics backend if relevant;
- replacement-texture state;
- remote debugger IP/port;
- game mode and exact target screen/state.

### Stock control

For a pristine ownership census:

- disable `Tekken6Ultrawide.prx`;
- disable aspect/HUD/camera cheats;
- restart Tekken 6;
- verify the plugin module is absent;
- verify known stock instructions with JIT replacements disabled for reads.

### v1.2.1 control

Use the exact accepted release PRX:

```text
6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8
```

Use this second control to answer whether an existing AutoHUD hook already sees the future target and to compare target/non-target runtime state.

Do not infer ownership from only one control.

---

## 2. Verify debugger transport before interpreting failures

Reuse the existing smoke-test discipline.

Before any capture:

1. verify TCP/WebSocket reachability;
2. verify PPSSPP version;
3. verify game ID;
4. verify CPU status;
5. verify whether the plugin module should or should not be present.

A debugger timeout is not a rendering result.

PPSSPP can keep a TCP listener while the debugger service is not actually responsive. Re-establish transport before diagnosing game behavior.

---

## 3. Capture phases for this project

Create a future transient-UI census with at least these phases.

### Phase T1 — PERFECT

State:

- active battle finishing with PERFECT banner clearly visible.

Capture before/during/after if possible.

Goal:

- identify every draw uniquely appearing with the PERFECT overlay.

### Phase T2 — YOU LOSE

State:

- loss result with large YOU LOSE banner visible.

Goal:

- compare owner/resource/geometry with PERFECT and YOU WIN.

### Phase T3 — YOU WIN / post-win result

Use two sub-phases.

#### T3a — banner only / transition

Capture the large YOU WIN overlay as soon as it appears.

#### T3b — result composition

Capture the screen containing:

- bonus rows;
- totals/currency;
- EXIT;
- direction prompt;
- character/opponent cards.

Goal:

- prove whether a common parent/choke point exists before the composition splits.

### Phase T4 — CONTINUE?

Capture:

- CONTINUE? prompt;
- at least two countdown values if possible.

Goal:

- determine whether prompt and numeric countdown share owner/state or need separate rules.

### Phase T5 — Promotion Chance

Capture:

- indicator visible in battle;
- same battle state where the indicator is absent if reproducible.

Goal:

- identify a narrow bottom-left owner/resource/geometry signature suitable for LEFT anchoring.

---

## 4. Frame-dump A/B method

Before broad CPU breakpoint work, use PPSSPP frame dumps when practical.

For each target:

1. capture a nearby control frame where the target is absent;
2. capture a frame where the target is visible;
3. diff draw calls;
4. record candidate target primitives.

Useful fields:

```text
primitive type
vertex type
vertex count
screen bbox
UV
texture address/format
texture hash
CLUT address/hash
blend/depth state
draw order
```

Do not identify ownership solely by visual resemblance.

A visible banner may consist of several layered submissions.

The winner-glow research is the reference lesson: eight visually related submissions could participate in one visible effect.

---

## 5. Known CPU census targets

Start with known paths because they are already understood:

```text
0x0892D9F8  shared slot builder
0x08AB9380  rectangle builder
0x08970A90  early text/glyph stage
0x08970B24  packed/late text stage
0x0892D56C  shared sprite call family
0x0892D5B0  shared sprite call family
0x08825EAC  stock sprite submission
```

Use strict sample caps on hot paths.

Also record backtrace/RA around the final submission.

If no known path owns the target, that is useful evidence. Do not force the target into an existing classifier.

Move to broader owner discovery.

---

## 6. CPU state to record

At a candidate owner/hook point, capture enough state to reconstruct both identity and ABI.

Recommended minimum:

```text
PC
RA
SP
backtrace
a0-a3
t0-t9 when relevant
s0-s7 when relevant
f12 and live FPU values when relevant
stack arguments
source/descriptor pointer
resource/family ID
authored X/Y
width/height
orientation/side
primitive/vertex metadata
texture/CLUT identifiers where traceable
mode/state flags
```

Read source memory around descriptor/packet pointers.

Capture neighboring non-target draws through the same owner.

The predicate is only safe when both target inclusion and non-target exclusion are understood.

---

## 7. Delay-slot and ABI audit before patch design

Disassemble the exact stock EBOOT around the proposed hook.

For every candidate hook document:

```text
hook address
stock word
delay-slot word
instruction after delay slot
J/JAL/tail-J behavior
incoming RA meaning
stack pointer state
all stack arguments
register/FPU inputs
observable return state
```

Never write the first experimental patch before this sheet is complete.

Specific historical warnings:

- timer failure exposed a missing fifth stack argument;
- HP work required respecting JAL vs tail-J path differences;
- EXP2 register assumptions corrupted winner composition;
- hard-coded PRX runtime VA caused a HUD-time crash.

---

## 8. Finding the right transform point

The best hook is usually not the global final submitter.

Prefer a pre-split owner where:

- source/authored geometry is still available;
- semantic identity survives;
- the number of unrelated draws is small.

### For center banners

Ideal state:

```text
target identity known
authored x/w known
before final vertex conversion
```

Apply dynamic CENTER only to horizontal geometry.

### For result-screen composition

First search for a parent transform/owner.

If all children derive from one parent offset/scale, correct the parent once.

Only fall back to per-child renderer rules if no shared owner exists.

### For Promotion Chance

Prefer exact resource/texture + geometry + owner state, then apply LEFT.

---

## 9. Patch experiment sequence

Do not implement all targets simultaneously.

Recommended order:

### EXP-T1

One easiest large center banner only, preferably PERFECT or YOU LOSE after owner proof.

Purpose:

- validate the chosen transient renderer and dynamic CENTER math.

### EXP-T2

Add the sibling banner family only if T1 proves shared ownership.

Examples:

- PERFECT;
- YOU WIN;
- YOU LOSE.

### EXP-T3

CONTINUE? prompt.

Add countdown separately unless capture proves common parent ownership.

### EXP-T4

Promotion Chance only.

Use LEFT semantics.

### EXP-T5

Post-win result composition.

Attempt common-parent correction first.

If fragmented, split into independent experiments rather than one broad rule.

Never bundle an optimization/refactor with a new HUD correction experiment.

---

## 10. Dynamic-aspect requirement

No production candidate may use fixed:

```text
0.8
48
96
```

as hard-coded 20:9 correction values.

Fixed constants are allowed only as explicit diagnostics.

Production candidates must consume the existing AutoHUD runtime aspect parameters and preserve automatic behavior.

At approximately 20:9, the dynamic output should naturally approximate the fixed values, but the implementation remains aspect-derived.

---

## 11. Binary/layout guard requirements

Every builder should verify:

```text
input PRX SHA-256
expected words at every modified module/game site
one PT_LOAD
p_filesz = 0x0EB0
p_memsz  = 0x0EB0
file size/layout invariants
frozen winner-glow bytes unchanged
existing accepted helpers unchanged unless explicitly targeted
expected free-space usage only
```

If a new helper consumes part of the accepted 136-byte capacity, document exact start/end and remaining capacity.

Do not label candidate bytes as permanently free until the resulting build passes device validation.

---

## 12. Full regression matrix for every implementation candidate

Minimum existing baseline checks:

- cold boot / title / menus;
- Arcade;
- Story;
- Ghost Battle;
- Practice;
- Gold Rush;
- HP full/partial/low;
- P1/P2 side strips and ranks;
- character names;
- timer;
- persistent round markers;
- first and later P1 winner glow;
- first and later P2 winner glow;
- visible winner-glow rotation;
- Practice infinity and combo/damage text;
- Gold Rush REWARD / ATTACK VARIATION;
- custom replacement textures/fonts;
- fast-forward.

New target-specific checks are added on top.

A build that fixes a transient target but regresses replacement textures or fast-forward is rejected.

---

## 13. New target acceptance criteria

### PERFECT / YOU WIN / YOU LOSE

Pass only if:

- horizontal stretch is removed;
- visual center remains logical X=240;
- vertical placement is unchanged;
- animation/layers remain intact;
- related non-target overlays are unchanged.

### CONTINUE?

Pass only if:

- prompt is centered/de-stretched;
- countdown remains centered relative to prompt;
- multiple countdown values work;
- no general font/UI regression occurs.

### Result composition

Pass only if:

- left bonus block, center EXIT controls, and right cards preserve relative layout;
- complete composition fits the intended centered safe area;
- no clipping is introduced;
- transitions/animations remain correct;
- result screen in neighboring battle modes remains sane.

### Promotion Chance

Pass only if:

- graphic is horizontally de-stretched;
- left/bottom ownership is preserved;
- it does not drift toward screen center;
- neighboring bottom/side HUD remains unchanged.

---

## 14. Evidence discipline

For every experiment record:

```text
hypothesis
exact parent artifact/hash
exact changed instructions
why those instructions are safe
capture evidence
device result
accepted/rejected
new PRX hash
free-space change
regression result
```

If a result was not tested, write:

```text
Result: not recorded
```

Do not convert an assumption into a checkpoint.

First-state success is not enough to declare a family solved.

---

## 15. Stop conditions

Stop patching and return to ownership research when:

- a target moves but animation changes unexpectedly;
- one state works and later states fail;
- unrelated UI moves;
- custom textures stop replacing;
- fast-forward changes;
- target does not hit the expected owner;
- exact target primitive is not proven;
- the patch would require growing `0x0EB0` without a separate layout study.

The safest next step after an ambiguous result is usually another narrow probe, not another broader patch.
