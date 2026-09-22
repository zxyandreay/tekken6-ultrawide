# Transient-UI AutoHUD Handoff

**Status:** ACTIVE RESEARCH / PREPARATION

Canonical project rules live under `docs/`; this document contains topic-specific constraints and hypotheses.

## 1. Goal

Extend the current automatic Tekken 6 PPSSPP ultrawide HUD correction to selected transient/result UI while preserving the v1.2.1 architecture, compatibility, replacement-texture behavior, fast-forward behavior, and runtime stability.

The desired visual rule is semantic rather than global:

```text
large transient/result UI -> CENTER safe area
Promotion Chance          -> LEFT anchored
```

Do not globally scale all 2D UI.

The objective is to correct only proven owners/render families.

---

## 2. Authoritative baseline

Use the exact official v1.2.1 runtime binary as the parent for every first implementation candidate.

```text
PRX:
SHA-256 6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8

ELF/runtime layout:
file size             5626 bytes
PT_LOAD count         1
p_filesz              0x0EB0
p_memsz               0x0EB0
```

The readable source in `plugin/src/` is not an exact reconstruction of the compact accepted runtime. Do not silently replace the authoritative PRX with a source rebuild.

Generate experiments deterministically from the exact baseline and guard the input/output SHA-256.

---

## 3. Existing AutoHUD semantic model

Logical horizontal center:

```text
X_CENTER = 240
```

For current display aspect `A` and baseline aspect `B = 16/9`:

```text
s = B / A
```

Existing semantic transforms:

```text
LEFT:
x' = s*x

CENTER:
x' = 240 + s*(x - 240)

RIGHT:
x' = 480 - s*(480 - x)
```

For ordinary rectangular/sprite geometry, horizontal extent generally follows:

```text
w' = s*w
```

Do not change Y/height unless the target renderer proves a different requirement.

At approximately 20:9, `s` is approximately `0.8`, but future implementation must consume runtime AutoHUD parameters rather than hard-code 20:9 constants.

The current plugin already computes reusable runtime aspect parameters. Known v1.2.x parameter examples include:

```text
0x08802304  horizontal scale (float)

winner-glow path:
0x08802328  horizontal span
CENTER shift = span * 0.5
```

Other established hooks/helpers also consume dynamic AutoHUD values from the same runtime parameter block. Reuse the accepted parameter system; do not create a second aspect engine.

---

## 4. Target matrix and working hypotheses

### 4.1 PERFECT

Desired behavior:

```text
transform: CENTER
horizontal de-stretch: yes
vertical change: none expected
```

Working hypothesis:

- likely a large textured transient sprite/quad;
- may share an owner/resource family with YOU WIN / YOU LOSE;
- potentially cheap if identified by caller + texture/resource + geometry.

Do not assume it is text simply because it contains letters.

### 4.2 YOU WIN / YOU LOSE

Desired behavior:

```text
transform: CENTER
```

Working hypothesis:

- likely large result-banner sprites;
- may share the same owner with PERFECT;
- first task is to prove whether the banner is one quad, layered quads, or a parent composition.

The winner-glow investigation demonstrated that a visible effect may contain several visually related layers. Identify the exact rendered family before patching.

### 4.3 CONTINUE? + countdown

Desired behavior:

```text
transform: CENTER
```

Working hypotheses:

- `CONTINUE?` may be a textured banner;
- countdown may be a separate sprite/font path;
- they may share one parent result/continue-screen owner even if their final primitives differ.

Preferred solution:

- correct a common pre-composition owner if one exists;
- otherwise use narrow owner/state predicates for each child renderer.

Avoid global font transforms.

### 4.4 Post-win / Ghost Battle result composition

Observed composition includes:

- YOU WIN banner;
- WIN/LIFE/SPECIAL/TOTAL bonus labels and values;
- currency marker;
- EXIT panel;
- directional-pad prompt;
- character/opponent cards and ranks.

Desired visual result:

```text
entire authored result composition remains internally coherent
and is horizontally de-stretched into the centered safe area
```

Preferred hypothesis:

> A common parent or shared result-screen transform exists before the final primitives split into sprite/font/rectangle paths.

This is the highest-value thing to prove.

If a common owner exists, transform the composition once.

If the screen is fragmented across unrelated renderers, treat it as multiple subproblems and do not force a global screen-row rule.

### 4.5 Promotion Chance

Desired behavior:

```text
transform: LEFT
horizontal de-stretch: yes
bottom-left ownership preserved
```

Working hypothesis:

- likely a distinct textured label/sprite;
- may be identifiable by unique resource/texture + bottom-left geometry;
- should be one of the cheapest candidates once ownership is proven.

---

## 5. Current code-space / memory constraints

The accepted v1.2.1/EXP4A binary has two proven detached general-purpose free regions:

```text
0x0604..0x0647   72 bytes
0x0C00..0x0C3F   64 bytes
-------------------------
accepted total   136 bytes
```

Additional startup-inline opportunity:

```text
0x03F0..0x03F7   8 bytes
```

The 8 startup bytes are not a general code cave and must not be added to the 136-byte free-space total.

Important interpretation:

> 136 bytes is accepted module-side headroom, not the total number of hooks the game can support.

Game callsites can be patched in place. The scarce resource is module-resident helper/classifier/table code and any new installer logic/state.

Prefer:

1. reuse of an existing accepted choke point;
2. a shared transient-UI dispatcher;
3. table/data-driven classification;
4. one new narrow wrapper only when no existing owner can safely carry the correction.

Do not grow `p_memsz` simply because 136 bytes becomes inconvenient.

Earlier enlarged test artifacts correlated with replacement-texture failures and abnormal fast-forward behavior. Keep the one-LOAD `0x0EB0` footprint as a hard constraint unless a dedicated memory-layout experiment proves otherwise.

---

## 6. Potential compact architecture

If ownership research shows that several targets converge through one shared sprite/rectangle path, a plausible future design is:

```text
existing AutoHUD dynamic parameters
            |
            v
shared transient-UI classifier
    |                   |
    |                   +-- Promotion Chance -> LEFT
    |
    +-- result/banner family -> CENTER
           PERFECT
           YOU WIN
           YOU LOSE
           CONTINUE
           result-screen pieces
```

A data-driven classifier may fit the accepted caves better than many independent comparison chains.

Conceptual allocation only:

```text
72-byte region -> compact dispatcher/helper
64-byte region -> rule records / small table
```

Do not commit to a table format before real capture data shows which discriminators survive at the chosen hook.

Useful rule fields may include some combination of:

- caller/return address;
- resource/family ID;
- descriptor pointer/family;
- texture/CLUT identity;
- primitive/vertex type;
- authored X/Y;
- width/height;
- mode/state;
- transform mode LEFT/CENTER/RIGHT.

Use the smallest set that uniquely owns the intended draw.

---

## 7. Known renderer/choke points from previous work

These addresses are established landmarks, not proof that the future targets use them.

```text
shared slot builder        0x0892D9F8
rectangle builder          0x08AB9380
shared stock sprite submit 0x08825EAC

existing shared sprite calls:
0x0892D56C
0x0892D5B0

timer renderer             0x0892D72C

text early stage           0x08970A90
text packed/late stage     0x08970B24

winner-glow callsite       0x08AC9C38
winner-glow converter      0x08AE94A4
```

The stock renderer census already showed that pause UI did not appear through several known battle-HUD paths. Therefore absence from a known hook is useful evidence: start a new owner-discovery pass rather than forcing the target into the battle classifier.

---

## 8. Frozen v1.2.1 subsystems

Do not modify these while discovering transient UI unless the experiment is explicitly about that subsystem.

- automatic 3D aspect correction;
- HP shell and colored fill;
- side strips;
- rank badges;
- character-name anchoring;
- center timer;
- persistent round markers;
- immediate earned round markers;
- winner/earned-round rotating glow;
- Practice infinity/text corrections;
- Gold Rush target labels;
- one-hook Practice/Gold helper;
- EXP4A compact slot-scope wrapper.

Winner-glow is especially frozen.

Accepted winner-glow ownership includes:

```text
callsite        0x08AC9C38
converter       0x08AE94A4
correct 64x64 packed UV identity
winner-row Y ownership
full P1/P2 round-family X ownership
dynamic CENTER transform
temporary source-X transform + restore
```

Do not reclaim or repurpose interior winner-glow bytes.

---

## 9. Critical lessons from previous failures

### 9.1 No global 2D transform

Different screens use different renderers and semantic ownership.

A visually similar result is not proof of shared ownership.

### 9.2 First-state validation is not enough

The historical winner-glow work appeared solved after first P1/P2 wins but later slot states were never tested.

For every transient target, test all meaningful state variants:

- first appearance;
- later/repeated appearance;
- P1/P2 or win/lose variants;
- alternate mode variants;
- transition in/out.

### 9.3 Correct math does not prove correct owner

The EXP3A V7Math diagnostic applied correct 20:9 math to the wrong glow layer and changed the visual effect without fixing the true spinner.

Prove the renderer/primitive identity before interpreting a position change as success.

### 9.4 Direct static xrefs are not enough to declare interior code dead

Do not reclaim bytes inside an integrated live renderer solely because no direct branch target is found.

Prefer removing/relocating a whole independently understood helper with enumerated callers.

### 9.5 Preserve ABI and delay slots

Previous experiments failed because of register/ABI assumptions.

Before changing a hook:

- record the exact stock instruction;
- record its delay slot;
- identify J versus JAL versus tail-J semantics;
- identify live input registers/FPU registers;
- identify stack arguments, including fifth+ arguments;
- identify which registers/state the caller observes after return.

Do not assume caller-saved registers are free just because the ABI normally permits clobbering. Preserve the behavior of the exact replaced path.

### 9.6 Never hard-code the PRX runtime load address

Use relocation-safe module-local addressing or proven PC-relative/local techniques.

A previous hard-coded PRX VA experiment crashed when the HUD became active.

### 9.7 Persistent text state is dangerous

The Practice/Gold work showed that mutating shared `s6` render fields can affect unrelated text.

Prefer bounded stack scratch or temporary source changes with explicit restore.

### 9.8 Installer loops must agree

When a compact table changes record stride/end, every validation/install/cache walker must use the same stride/end.

The EXP2S black-screen startup hang came from one forgotten walker.

### 9.9 Cache maintenance is part of correctness

Any startup installer that patches executable game code must preserve the accepted instruction/data cache invalidation behavior.

### 9.10 Module layout is a compatibility constraint

Replacement textures and fast-forward are mandatory regression canaries.

Do not grow the accepted LOAD segment casually.

---

## 10. Hook design decision tree

For each target:

### Step A — prove final draw identity

Obtain:

- primitive;
- vertex type/count;
- texture and CLUT identity where available;
- screen-space bbox;
- UV;
- mode/state timing.

### Step B — find CPU owner

Determine:

- renderer/callsite;
- return address/backtrace;
- resource/family ID;
- descriptor/source pointer;
- authored geometry before final conversion.

### Step C — find earliest safe transform point

Prefer the earliest point where both are true:

1. authored X/width or source vertices are still available;
2. semantic ownership can be uniquely identified.

Do not hook globally just because it is convenient.

### Step D — choose semantic transform

```text
Promotion Chance -> LEFT
center transient family -> CENTER
```

### Step E — prove non-target rejection

Capture neighboring draws through the same renderer and prove that the predicate rejects them.

### Step F — design smallest patch

Prefer:

- existing hook extension;
- compact shared helper;
- exact rule table;
- no new global state.

### Step G — deterministic build

Builder must:

- require exact parent SHA-256;
- verify every expected stock/module word before patching;
- verify frozen regions remain byte-identical;
- verify one PT_LOAD and `0x0EB0` sizes;
- print output SHA-256;
- reject unexpected binary differences.

---

## 11. Release strategy

Do not choose a release number before implementation scope is known.

A future release should promote the exact device-validated research artifact, not a later reconstruction.

Before any merge to `main`:

1. freeze exact PRX hash;
2. run full existing v1.2.1 regression matrix;
3. run all new transient-UI acceptance states;
4. verify custom textures/fonts;
5. verify fast-forward;
6. verify PT_LOAD remains `0x0EB0`;
7. document owner/hook/predicate and known limitations;
8. merge durable research/tools into main only after the implementation is accepted.

Until then, keep all implementation work on this research branch or descendants.
