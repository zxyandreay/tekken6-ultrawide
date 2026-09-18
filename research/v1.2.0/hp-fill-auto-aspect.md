# AutoHUD HP-fill investigation

This record follows the HP-fill regression that appeared during automatic-aspect HUD experiments from the gauge owner through final sprite submission.

---

## 1. Known-good fixed-ratio comparator

A known-good fixed-20:9 checkpoint was used as the comparator for the HP regression investigation.

Relevant validated behavior:

- both colored HP fill layers were visible;
- fill width depleted normally;
- both player sides used the same gauge renderer;
- the hook preserved stock renderer ownership and redirected only corrected XY/width state.

The two gauge-owner sites were:

```text
0x0892C1F0
0x0892C26C
```

Both ultimately entered:

```text
0x08928FF4
```

The fixed EXP6 20:9 coefficients were:

```text
horizontal shift = +/-1.3056111
f12 scale        = 1.0493455
```

The side discriminator lived at:

```text
t1 - 0x28
```

and resolved to:

```text
0 = P1
1 = P2
```

The hook copied source XY into module scratch, changed the scratch X, redirected `t1`, scaled `f12`, then entered the stock renderer.

---

# 2. AutoHUD history before runtime tracing

The first automatic-aspect builds introduced several unrelated regressions.

By EXP11, most font/mode behavior had been recovered, but HP fill remained absent.

## EXP11

EXP11 fixed a Gold Rush control-flow issue in the font path and preserved the compact texture-safe footprint.

Its HP path also changed how dynamic coefficients were stored/reached.

Result:

- Gold Rush `REWARD` restored;
- custom replacement textures preserved;
- HP fill still missing.

## EXP12

EXP12 tested whether direct `LWC1` coefficient loading was the problem.

It restored an EXP8-style transport:

```text
LW integer float bits
MTC1 into FPU register
```

and matched the known renderer-entry shape more closely.

Result: HP fill still missing.

## EXP13

EXP13 restored the EXP6-like live register/FPU sequence while reading dynamic coefficient values.

Result: HP fill still missing.

## EXP14

EXP14 was the decisive isolation build.

The complete HP gauge hook was copied byte-for-byte from the working EXP6 implementation, including the fixed 20:9 coefficients.

Everything else remained AutoHUD.

Result: HP fill still missing.

This proved that the regression could not be explained solely by:

- the dynamic coefficient equations;
- the coefficient storage location;
- `LWC1` versus `LW+MTC1`;
- the side discriminator;
- the visible source-level gauge-hook logic.

The investigation therefore moved downstream.

---

# 3. EBOOT mapping observation

The supplied ULUS10466 EBOOT is a decrypted MIPS ELF.

Its main load segment was:

```text
file offset : 0x001018
virtual base: 0x08804018
file size   : 0x003F62A8
memory size : 0x0045F02C
```

Some AutoHUD experiments used:

```text
0x08802310
0x08802314
```

for dynamic HP parameters.

Those addresses are below the EBOOT's mapped segment.

That made them suspicious from a static ownership perspective, but later runtime reads showed they were readable and did contain dynamic coefficients.

Important conclusion:

> being outside the EBOOT PT_LOAD did not prove the area was invalid PSP RAM, and it did not explain the captured missing-fill regression.

The actual failure was later found elsewhere.

---

# 4. Runtime comparison strategy

The central question became:

> What state reaches the stock HP renderer in working EXP6, and where does broken EXP14 first diverge?

The probe captured:

- live owner instructions;
- decoded hook target;
- pre-hook source pointer/state;
- side field;
- source XY;
- `f12`;
- renderer-entry pointer/XY/FPU state;
- JAL and tail-J call pairing;
- downstream lookup/builder/submission stages.

The important methodological constraint was to avoid broad hot-loop tracing.

Only the known HP owners and their corresponding renderer calls were paired.

---

# 5. MIPS call-pairing corrections

The probe itself uncovered important ABI details.

## JAL owner

At:

```text
0x0892C1F0
```

the delay slot is:

```text
move t1,s0
```

Therefore the `t1` value visible before the JAL can be stale.

The effective input to the hook is the post-delay-slot value from `s0`.

The JAL-generated return address is:

```text
0x0892C1F8
```

## Tail-J owner

At:

```text
0x0892C26C
```

the delay slot is:

```text
addiu sp,sp,0x20
```

The renderer pairing therefore has to account for:

```text
renderer SP = owner SP + 0x20
```

while preserving the incoming RA semantics of the tail jump.

These corrections were necessary before comparing EXP6 and EXP14 meaningfully.

---

# 6. JIT-aware instruction reading

Raw memory reads sometimes showed words that did not resemble the expected J/JAL instructions.

PPSSPP's debugger disassembly path was then used because it resolves the emulated instruction stream in a JIT-aware way.

Lesson:

> raw code bytes under a JIT are not always the right source for determining the guest instruction being executed.

This prevented false conclusions about hook corruption.

---

# 7. EXP14 full-HP capture

The first successful EXP14 capture showed both sides and both owner paths reaching the gauge hook.

Representative state:

```text
P1 effective source X = +98
P2 effective source X = -98
```

After the restored EXP6 transform:

```text
P1 renderer X = +99.3056107
P2 renderer X = -99.3056107
```

Full-HP width input:

```text
f12 ~= 191
```

Renderer width:

```text
~200.424988
```

This matches:

```text
191 * 1.0493455
```

A transient reduced-width Practice capture also showed a smaller P2 width being scaled and reaching the renderer.

This rejected:

- "hook not installed";
- "side field invalid";
- "scratch pointer never used";
- "HP width multiply never runs";
- "renderer never receives corrected HP geometry".

The missing fill had to be later.

---

# 8. Known-good fixed-ratio downstream path

The next probe followed a known-good call from the fixed-ratio comparator farther downstream.

Observed flow:

```text
0x08928FF4   HP renderer entry
0x08929064   lookup call
0x0892906C   lookup return
0x089290B0   packet-builder call
0x0892D56C   packet-builder final submission call
0x08825EAC   stock sprite submission
0x089290B8   renderer return
```

Working full-HP packets had approximately:

```text
P1 X:   206.305603
P2 X:   273.694397
Y:      21
Z:      1000
width:  ~200.425
height: 32
flags:  0xEA1
```

Texture IDs were layer-specific and resolved successfully.

The two full-health HP layers carried different final alpha values, so an alpha-zero capture in one layer was not by itself evidence of the missing-fill bug.

All four working HP paths returned:

```text
v0 = 1
```

from stock submission.

---

# 9. First causal divergence in EXP14

The exact failure appeared in a downstream side-strip/rank hook that every packet passed through before stock submission.

The AutoHUD rewrite had shortened that hook by eight bytes.

Five rejection branches still targeted the old common bypass destination.

Representative logic:

```text
if packet does not belong to side-strip/rank target
    branch to common forwarding path
```

HP packets have:

```text
packet Y = 21
```

so they intentionally reject out of the side-strip/rank-specific path.

In EXP6, the old common rejection target contained:

```text
J 0x08825EAC
NOP
```

In EXP14, the dynamic rewrite moved the normal forwarding jump earlier, but the old target became:

```text
NOP
NOP
```

followed by the next import stub.

The stale branches were therefore still valid MIPS branches, but they landed in the wrong place.

This is why the gauge hook looked correct yet the sprite disappeared.

---

# 10. Runtime confirmation of the stale bypass

At the side-hook gate, HP packets showed:

```text
packet Y = 21
expected side/rank Y = 56
```

The rejection branch was taken.

Instead of reaching the stock submitter, the broken route fell through the stale target and entered the following import stub.

The renderer then returned an error-like result instead of the successful:

```text
v0 = 1
```

seen in EXP6.

This also explained several misleading symptoms:

- caller-saved registers became sentinel/junk values;
- malformed log strings appeared;
- downstream state looked corrupted.

Those were consequences of executing the wrong import path, not evidence that the HP gauge inputs themselves were wrong.

The first causally relevant difference was therefore the stale branch destination.

---

# 11. EXP15 repair

EXP15 changed exactly one aligned word at PRX VA:

```text
0x092C
```

Before:

```text
NOP
```

After:

```text
J 0x08825EAC
```

The delay slot remained NOP.

No coefficient changed.

No new branch target was introduced.

No relocation entry touched the patch.

The PRX remained:

```text
file size = 5626 bytes
one PT_LOAD
p_filesz = 0x0EB0
p_memsz  = 0x0EB0
```

Validated EXP15 PRX SHA-256:

```text
54c47d12b991ac093c8311986a24ba307efb42056ea0f313bc66f46e695d7d74
```

Device result: colored HP fill returned.

Runtime result: all four HP paths reached stock submission and returned:

```text
v0 = 1
```

This closed the missing-fill regression.

---

# 12. EXP15 was not yet true dynamic HP

EXP15 repaired control flow but intentionally retained the EXP6 fixed 20:9 HP hook.

Its embedded constants were:

```text
shift: 1.3056111
scale: 1.0493455
```

The AutoHUD initializer, however, was already computing aspect-derived values.

For a live display close to 20:9, the captured runtime values were slightly different from exact 20:9 because the actual reported aspect was slightly different.

That was desirable evidence that the AutoHUD initializer was genuinely dynamic.

The remaining task was to make the gauge **consume** those values without disturbing the rest of the compact binary.

---

# 13. General HP equations

Let:

```text
s = (16/9) / detected_aspect
d = 1 - s
```

Derived from the AutoHUD binary:

```text
hp_shift = 6.528055667877197 * d
hp_scale = 1.0 + 0.24672749638557434 * d
```

At 16:9:

```text
hp_shift = 0
hp_scale = 1
```

At exact 20:9:

```text
hp_shift = 1.3056111
hp_scale = 1.0493455
```

This demonstrated that the EXP6 constants were the 20:9 instance of a continuous function.

---

# 14. EXP16 self-patching attempt

The first post-EXP15 design tried to preserve the hot gauge hook exactly and patch its embedded float immediates once during initialization.

Architecturally, that was attractive:

- no extra hot-path loads;
- no additional resident memory;
- proven EXP6-shaped hook;
- dynamic coefficients.

The implementation used the initializer's return address as a relocation-safe anchor to the gauge instruction words.

HP worked.

But the patch reused initializer instructions thought to be dead.

Device testing showed that those instructions still participated in text/font setup.

Regressions:

- Practice combo/hit text disappeared;
- Gold Rush `REWARD` disappeared;
- Gold Rush `ATTACK VARIATION` disappeared;
- some main-menu text disappeared.

EXP16 was rejected.

Lesson:

> in a compact hand-integrated PRX, code that looks dead relative to one path may still feed an unrelated subsystem.

---

# 15. EXP17 dynamic coefficient reads

EXP17 restarted from exact EXP15.

The initializer was left byte-for-byte intact.

Only the gauge coefficient transport changed.

Instead of constructing the fixed 20:9 float constants, the hook loaded the already-computed dynamic HP values.

The repaired downstream forwarding path remained unchanged.

The rest of the EXP6-shaped gauge behavior also remained unchanged.

Device regression result:

- HP fill present;
- partial/full behavior normal;
- Practice combo/hit text restored;
- Gold Rush target labels restored;
- main-menu text restored;
- Arcade, Story, Ghost Battle, Practice, and Gold Rush passed;
- replacement textures/fonts remained active.

EXP17 PRX SHA-256:

```text
311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75
```

This became v1.2.0.

---

# 16. What the HP investigation taught

The important methodological lessons are broader than the one bug.

## 16.1 A restored local hook can still fail downstream

EXP14 proved that copying a working hook byte-for-byte does not prove the draw will survive later shared code.

## 16.2 Compare at the same stage

EXP6 and EXP14 were compared at:

- owner;
- renderer entry;
- lookup return;
- packet builder;
- side-hook gate;
- stock submitter;
- renderer return.

That progression turned a vague "HP is missing" symptom into one exact branch-target defect.

## 16.3 Preserve delay-slot semantics

The JAL and tail-J owners both depended on delay-slot effects.

Ignoring them produced incorrect pairing and false pointer/register interpretations.

## 16.4 Do not over-interpret junk registers

The apparent register corruption in EXP14 was downstream fallout from falling into an unintended import stub.

It was not the cause.

## 16.5 Control-flow layout is part of binary correctness

Shortening a compact hook without recomputing all internal branch destinations is enough to break unrelated packets that only use its rejection path.

This was the root cause of the HP-fill regression.

## 16.6 Fix causality before generalization

EXP15 repaired the known causal bug first.

Only after that repair was validated did the research return to the dynamic HP objective.

That sequencing is why EXP17 could be interpreted cleanly.
