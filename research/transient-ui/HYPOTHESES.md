# Transient-UI Renderer / Ownership Hypotheses

**Status:** ACTIVE RESEARCH / UNPROVEN

This document records the current working hypotheses for the future transient-UI HUD corrections.

Nothing in this file should be treated as an accepted renderer map until it is supported by runtime/frame-dump evidence and device validation.

The central distinction is:

> A future target may share the same **low-level renderer** as a solved battle-HUD element without sharing the same **semantic owner, callsite, or safe hook**.

That distinction must be preserved throughout the research.

---

## 1. Possible convergence levels

When comparing a future target with an already-solved HUD family, classify the relationship at the deepest proven level.

### Level 1 — same final submitter

Example:

```text
future target
current HUD
    \
     -> 0x08825EAC
```

This is weak evidence.

A global stock sprite submitter can serve many unrelated UI families. Reaching the same final submitter does not make it a safe common hook.

### Level 2 — same low-level builder

Examples:

```text
0x0892D9F8  shared slot builder
0x08AB9380  rectangle builder
0x08970A90  early text/glyph stage
```

This is more useful because authored geometry and/or resource identity may still survive.

It is still necessary to prove semantic ownership.

### Level 3 — same already-hooked callsite / dispatcher family

Examples:

```text
0x0892D56C / 0x0892D5B0
existing battle sprite dispatcher family
```

This is a strong result if the future target reaches the same boundary and retains enough discriminators to build a narrow predicate.

A future fix might then require only an additional classifier branch rather than a new game hook.

### Level 4 — same semantic owner / parent composition

This is the best case.

Example:

```text
one parent result/banner owner
        |
        +-- PERFECT
        +-- YOU WIN
        +-- YOU LOSE
```

If the owner still exposes authored geometry and mode/resource identity, one narrow transform may solve an entire family before it splits into final draw primitives.

---

## 2. Known renderer landmarks worth probing first

These are established from previous work and should be the first read-only census targets.

```text
shared slot builder        0x0892D9F8
rectangle builder          0x08AB9380

shared battle sprite calls
0x0892D56C
0x0892D5B0

stock sprite submitter     0x08825EAC

text early stage           0x08970A90
text packed/late stage     0x08970B24

timer renderer             0x0892D72C

winner-glow callsite       0x08AC9C38
winner-glow converter      0x08AE94A4
```

The first six are discovery targets for this research.

The timer and winner-glow paths are frozen accepted subsystems and should be used mainly as architectural references unless a future target independently proves it shares one of those owners.

---

## 3. Why reuse is plausible

The solved battle HUD already demonstrates several useful forms of renderer reuse.

### Shared slot-builder reuse

At `0x0892D9F8`, previous captures retained:

- JAL caller return for direct callers;
- slot;
- resource/family ID;
- descriptor pointer;
- flags;
- optional translation/scale pointers;
- authored descriptor geometry.

This makes it plausible that a future textured transient element could pass through the same builder while still being safely distinguishable.

### Shared battle sprite-dispatcher reuse

HP, side strips, and rank badges were proven to coexist at the `0x0892D56C / 0x0892D5B0` family with stable packet identity.

This demonstrates that one already-hooked boundary can host multiple exact semantic predicates.

A future battle-time element reaching this same dispatcher could potentially be added without a new game hook.

### Shared text-stage reuse

The early text stage at `0x08970A90` preserves:

- owner/backtrace context;
- authored X/Y;
- live X/Y scale;
- glyph pointer/code;
- font/render state.

This makes it a plausible discovery point for future prompt/countdown text, but not a globally safe transform.

---

## 4. Target-specific hypotheses

## 4.1 Promotion Chance

### Desired transform

```text
LEFT
```

### Current hypothesis

This is the strongest candidate for reuse of the existing battle-HUD infrastructure because it appears during active battle and behaves visually like a side-owned HUD element.

Probe first:

```text
0x0892D9F8
0x08AB9380
0x0892D56C
0x0892D5B0
```

Working possibilities:

1. another slot/resource family under the existing slot compositor;
2. another rectangle family;
3. another packet through the existing battle sprite dispatcher;
4. a separate but nearby battle owner that ultimately uses one of the same low-level renderers.

### Best-case implementation

```text
existing battle dispatcher
        |
        +-- current HP/rank/side families
        |
        +-- Promotion Chance -> LEFT
```

This could require no new game hook if exact identity survives.

### What would falsify the hypothesis

- no hits at the known battle builders/callsites while the element is visible;
- hits only at the global stock submitter with no useful surviving owner identity;
- renderer ownership belonging to a separate transient UI domain.

---

## 4.2 PERFECT

### Desired transform

```text
CENTER
```

### Current hypothesis

Likely a large textured quad or layered sprite family rather than ordinary font text.

It may share:

- the slot builder;
- the rectangle builder;
- a battle/result sprite owner;
- or only the final stock sprite submitter.

The useful result is not merely that it reaches `0x08825EAC`, but that it reaches one of the earlier known boundaries with caller/resource/geometry identity intact.

### Additional hypothesis

`PERFECT`, `YOU WIN`, and `YOU LOSE` may belong to one common transient-banner family.

This should be tested directly rather than implemented as three unrelated special cases.

---

## 4.3 YOU WIN / YOU LOSE

### Desired transform

```text
CENTER
```

### Current hypothesis

These may share the same owner and resource family as `PERFECT`.

Possible architecture:

```text
result/banner owner
      |
      +-- PERFECT
      +-- YOU WIN
      +-- YOU LOSE
      |
      v
shared sprite/rectangle path
```

The best result would be one common banner predicate at an existing hook or one shared parent owner.

### Important warning

A visually coherent banner may be composed from several layers.

The winner-glow investigation proved that the visible effect and the actual target primitive can be different related layers.

Do not accept a hook simply because one visible layer moved.

---

## 4.4 CONTINUE? prompt

### Desired transform

```text
CENTER
```

### Current hypotheses

Three architectures are plausible.

#### A. Textured banner

```text
CONTINUE?
   -> sprite/rectangle path
```

This may share the same family as the large result banners.

#### B. Font-rendered prompt

```text
CONTINUE?
   -> 0x08970A90 text path
```

If so, use owner/glyph/state identity rather than a global font transform.

#### C. Mixed composition

```text
CONTINUE? prompt -> sprite
countdown        -> font/numeric renderer
```

This would require two narrow rules but may still reuse existing hooks.

---

## 4.5 CONTINUE countdown

### Desired transform

```text
CENTER
```

### Current hypothesis

The countdown may not share the prompt's renderer.

It could be:

- font/glyph based;
- a numeric sprite family;
- a timer-like dedicated renderer;
- a child of the same continue-screen parent.

Do not assume the existing round-timer renderer owns it merely because both are large centered numbers.

The timer path should remain frozen unless runtime evidence directly proves shared ownership.

---

## 4.6 Post-win / Ghost Battle result composition

### Desired transform

```text
CENTER-safe-area composition
```

### Current hypothesis

The final screen probably uses several primitive/render families, for example:

```text
YOU WIN              -> sprite/rectangle
bonus labels          -> font
bonus values          -> font/numeric
currency marker       -> font
EXIT                  -> sprite/rectangle
direction prompt      -> sprite
character cards       -> sprite
rank graphics         -> sprite
```

Therefore it is likely that many children share low-level renderers with solved battle HUD while not sharing one existing semantic owner.

### Highest-value hypothesis

Search for a common parent or layout owner before the children split.

Ideal architecture:

```text
ResultScreen / result-layout owner
              |
        CENTER transform
              |
      +-------+--------+
      |       |        |
    text    cards    prompts
```

If such a parent exists, it is preferable to multiple child hooks.

### Fallback

If the screen is genuinely fragmented:

- split it into independent renderer families;
- keep each predicate narrow;
- do not create one broad "result screen" rule at a global submitter.

---

## 5. Important negative evidence

Previous stock census results already prove that Tekken 6 has multiple UI rendering domains.

During pause, these known battle paths did not capture the pause UI:

```text
0x0892D9F8
0x08AB9380
0x08970A90
0x08970B24
```

The observed `0x08825EAC` pause-phase samples were underlying battle HP packets, not the pause UI itself.

During character select:

- known slot/rectangle/stock-sprite paths did not establish ownership of the actual character-select widgets;
- the broad early text stage fired, but sampled text was not sufficient to map the UI.

Therefore:

> "Visible during or after battle" does not guarantee reuse of the solved battle-HUD owners.

The future targets must be measured.

---

## 6. Preferred discovery order

Use the cheapest/highest-reuse candidates first.

### T1 — Promotion Chance

Reason:

- active-battle element;
- strongest chance of existing battle-owner reuse;
- simple LEFT semantics.

### T2 — PERFECT

Reason:

- isolated large center overlay;
- likely easy to identify in frame-dump A/B.

### T3 — YOU WIN / YOU LOSE

Reason:

- compare directly against PERFECT;
- test the shared-banner-family hypothesis.

### T4 — CONTINUE?

Reason:

- census both sprite/rectangle and text paths;
- separate prompt from countdown if needed.

### T5 — result composition

Reason:

- most likely to be fragmented;
- first search for a parent layout owner before child-level hooks.

---

## 7. Possible implementation outcomes

### Outcome A — existing hook reuse

Best case.

```text
existing hook
   |
   +-- existing families
   +-- future target classifier
```

Expected impact:

- smallest new resident code;
- lowest ABI risk;
- easiest fit within existing 136-byte headroom.

### Outcome B — same low-level renderer, new safe callsite

Still good.

A new callsite wrapper may be required, but transform math and runtime aspect parameters can be reused.

### Outcome C — mixed sprite/text composition

Likely for CONTINUE or result UI.

Use one narrow rule per renderer family and share the same dynamic AutoHUD parameters.

### Outcome D — separate UI subsystem

If none of the known paths retain the target, perform a fresh owner-discovery pass.

Do not broaden existing battle predicates to compensate.

---

## 8. Memory / code-space implications

Current accepted detached capacity:

```text
0x0604..0x0647   72 bytes
0x0C00..0x0C3F   64 bytes
-------------------------
136 bytes
```

This is enough to make reuse of existing hooks especially attractive.

If several targets share one existing hook, the likely incremental need is:

- compact classifier logic;
- small identity/rule data;
- no second aspect engine;
- no duplicate LEFT/CENTER math.

A shared transient classifier remains a plausible target architecture:

```text
existing AutoHUD parameters
          |
          v
transient classifier
   |              |
   |              +-- Promotion Chance -> LEFT
   |
   +-- banner/result family -> CENTER
```

This remains only a design hypothesis until ownership captures identify what fields survive at the chosen boundary.

---

## 9. Evidence required before promotion to findings

A hypothesis can move to `findings/` only after all of the following are established:

1. exact visible primitive/family identified;
2. CPU owner or safe renderer boundary identified;
3. authored/source geometry available at that point;
4. stable target identity fields recorded;
5. neighboring non-target draws captured;
6. predicate shown to reject those neighbors;
7. hook ABI/delay-slot behavior documented;
8. dynamic LEFT/CENTER behavior demonstrated on device;
9. existing v1.2.1 regression matrix passes;
10. custom replacement textures/fonts and fast-forward remain intact.

Until then, keep the statement in this file as a hypothesis.
