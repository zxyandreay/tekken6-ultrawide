# v1.2.0 HUD research test-build archive

This file inventories the recovered test artifacts used during the HUD/AutoHUD research that led to v1.2.0.

The artifacts were reconstructed from two sources:

1. the original deleted research history, which remained addressable by commit SHA; and
2. the operator's retained ZIP test builds, whose PRX hashes and embedded test notes were re-inspected after branch cleanup.

This archive records the experiment purpose and result/lesson. It does **not** store the binaries themselves in Git.

No local network addresses, debugger endpoints, device identifiers, or workstation paths are retained.

---

## Research origin and pre-composition diagnostics

The repository did not begin from a completed HUD-correction build. The earliest preserved state was a known-good 3D-only CWCheat with stretched HUD/UI and no identified HUD transform.

The following retained diagnostic packages belong to the transition from broad 2D hypotheses into direct battle-HUD ownership mapping.

### Tekken6-HUD-PathMap-v1

ZIP SHA-256: cd3757849e98307d588f81257f7ec315c9a67679efc97fc8e8ef4a404df35853

Purpose: redirect selected battle-HUD draw calls through a +32 PSP-pixel X-shift wrapper so ownership could be identified visually without yet applying safe-area scaling.

The package explicitly used one known HP-fill path as MAP 0 control and tested other direct sprite candidates separately.

A later retained CMain diagnostic records the result that 0x0892D56C / 0x0892D5B0 is the visible HP-fill renderer and that the older MAP 1-5 candidates did not affect the visible fight HUD.

### Tekken6-HUD-Ortho-GroupMap-v3

ZIP SHA-256: bf7365194d861460eacacd98f9e0dc7b637286014b0da10479b59ccb28bb14a7

Purpose: suppress orthographic UI compositor groups 9, 10, 12, 13, 14, 15, 16 and 17 independently to identify ownership of the static HP frame/shell and related battle UI.

A later retained Group 10 note records that MAP 2 / Group 10 hides the health bars.

### Tekken6-HUD-Group10-SafeArea-v4

ZIP SHA-256: 894718248677aa9775dec9470349bf7166e6390c59e746203e4b08bc4a8f4599

Purpose: first retained HP safe-area candidate after Group 10 ownership was identified.

The test installed a centered 16:9 orthographic projection only for Group 10 on a 20:9 output, using bounds -60..540.

The artifact proves the intended experiment. The exact device-visible result is not preserved strongly enough in the recovered evidence to state a conclusion.

### Tekken6-HUD-Group10-SafeArea-v5

ZIP SHA-256: 437909de210d3e5478218012ffc37569d9082ea8f9045ca42d4cc27dfe65a727

Purpose: move the Group 10 safe-area projection later, to the draw-list submission itself, and add an exaggerated 50%-width diagnostic if the normal safe-area transform was visually ambiguous.

Again, the retained artifact proves the hypothesis and test design; the precise device result is not claimed without stronger surviving evidence.

### Tekken6-HUD-CMain-PathMap-v2

ZIP SHA-256: aafc75856a22a1dcf219517512dce5ab920b89714e0623599f6d6eac7d912039

Purpose: identify which CMainTcb_t::Draw sub-renderer owns the static HP frame/background around the already-confirmed CGauge fill.

The retained note records these static ownership findings:

- tk::sprite::battle::CGaugeTcb_t::Draw = 0x0892C124
- tk::sprite::battle::CMainTcb_t::Draw = 0x0892BDAC

This diagnostic marks the transition from broad compositor-group tests to battle-object-specific ownership mapping.

---
## 1. Early frame-dump diagnostic set

### `Tekken6-HUD-FrameDump-Test-Cheats`

Recovered ZIP SHA-256:

```text
0bb70815097a1d65b534847c000dba9ec0cc4bce474aaebe8b052687b7a30ec2
```

This package did not contain a PRX. It contained a controlled CWCheat test set used to create three comparable PPSSPP frame dumps from the same fight:

```text
A - baseline, no HUD patch
B - hide health-bar group
C - shift HP fill +32 X
```

The diagnostic restored known stock calls first and then changed one narrow path at a time.

The important early idea was **differential rendering**:

- if hiding one slot/group removes the shell but leaves the fill, shell and fill are independent draw paths;
- if shifting one path moves only colored HP fill, that path owns the fill rather than the shell/background;
- frame dumps can then be correlated back to CPU owners instead of globally guessing at sprite code.

The "shift HP fill" test redirected the final HP packet submission through a tiny temporary +32 X transform before rejoining the stock submitter. This provided one of the earliest proofs that the colored fill could be moved independently of the rest of the HUD.

---

# 2. Battle-composition integration

### `Tekken6-HUD-Battle-Composition-v4-Test.zip`

```text
ZIP SHA-256:
1bd91176a1a77e86351ee05ea87bd7f0cdf8dcd4557790d2dd569a71b6a7919f

PRX SHA-256:
020c27b36ac1a2d293b8c0104fa049174bf4fbeb002b6b4cd41cf405ddd82737

PRX size:
4910 bytes

PT_LOAD:
p_filesz = 0x0BE4
p_memsz  = 0x0BF8
```

The retained ZIP does not contain a dedicated experiment note; its package README still describes the v1.1.0 automatic-3D baseline.

The corresponding recovered HUD notes place this build in the early battle-composition phase, before the later fixed `0x0EB0` compact checkpoint. The research at this stage was consolidating HP shell/fill, side strip/rank, and round-family corrections into one battle-HUD implementation.

Because the ZIP itself does not preserve a specific pass/fail note, no stronger device result is inferred from the artifact alone.

---

# 3. Round-win marker progression

## RoundWin v6

Artifact:

```text
Tekken6-HUD-RoundWin-v6-Test

ZIP SHA-256:
00f4c3f32b96864bb5842c9f13bf717a8781c1094671d4928b15a991dea0091b

PRX SHA-256:
b56e9bc438898a38bba2892df5e36be8c0300c918e78d9f6cd221e301e495498

PRX size:
5006 bytes
```

Purpose: fix only the first P2 earned-orb lower bound.

The retained test note records an exact one-word patch:

```text
slti t4,a2,274
    ->
slti t4,a2,273
```

The first authored P2 earned orb could occur at x=273, so the old lower bound excluded the immediate first-win draw even though the persistent next-round marker later appeared correctly.

Lesson:

> visually identical "earned orb" states can use slightly different authored coordinates or draw phases; a one-pixel ownership boundary can break only the immediate state.

The residual glow was intentionally not changed in v6.

## RoundWin v7

Artifact:

```text
Tekken6-HUD-RoundWin-v7-Test

ZIP SHA-256:
23a6d896769651a682c5782e53347dd7373a9e2e74166c8de3c6a8d6ca8da898

PRX SHA-256:
2e25d01deb26194a8854c13c18fba136271a4fc299233b79175f984243551917

PRX size:
5626 bytes

PT_LOAD:
p_filesz = p_memsz = 0x0EB0
```

v7 combined the validated first-orb correction with the separately researched winner-glow correction.

Recovered implementation:

```text
callsite:   0x08AC9C38
converter:  0x08AE94A4
vertex path: 0x80019E
quad:       4 vertices
UV:         exact 64x64 corners
transform:  x' = 0.8*x + 48
```

The hook temporarily transformed only the four source X values, called the original converter, then restored the source values.

Y, UV, color/alpha, Z, rotation, and animation lifetime remained stock.

This established that the visible winner glow was a separate renderer from the ordinary round-marker rectangle family even though both shared CENTER semantics.

---

# 4. Center timer progression

## CenterTimer v8

```text
ZIP SHA-256:
dde1575aee355a46a1b91023c6f158a823ecbee9121de13ee170dcbec03cd114

PRX SHA-256:
970592980da48a8ce8ae66551b29568ec4467983cf2cdd7d55fab9e496cf8c16

PRX size:
5626 bytes

PT_LOAD:
p_filesz = p_memsz = 0x0EB0
```

The timer research identified two owner calls:

```text
0x08929AF8
0x08929B44
```

to the original renderer:

```text
0x0892D72C
```

The first v8 wrapper reused the proven CENTER rectangle transform only while the two timer digits were rendered.

Device result: the timer disappeared.

That failure was not caused by the CENTER math.

## CenterTimer v8.1

```text
ZIP SHA-256:
557c0af14c732d2d3a3a2ba083f3beea57e22057a3bf260b2fa2e164be6e4634

PRX SHA-256:
8d0f8577361c8f95f58f4fc7e71549277397aea02c94223300491c3149b4ae65
```

v8.1 fixed the wrapper ABI by preserving the timer renderer's stack-passed fifth argument before calling `0x0892D72C`.

Lesson:

> preserving visible argument registers is insufficient when wrapping MIPS calls; stack arguments and delay-slot effects are part of the ABI contract.

The corrected timer behavior was subsequently accepted.

---

# 5. Character-name anchoring progression

## SideNames v9

```text
ZIP SHA-256:
e7d14537f294e6a665912f25b83eb51190d95c9e2968018e86582c0acdd9972d

PRX SHA-256:
b34153afce5249ae11b9d2acc4477f884d4f4b4b2789229ead72ffe60b4b9754

PRX size:
6046 bytes

PT_LOAD:
p_filesz = p_memsz = 0x1054
```

Target family:

```text
y = 28
height = 16
authored width = 64 or 128
```

Classification:

```text
authored X < 240 -> LEFT
authored X > 240 -> RIGHT
```

The top ARCADE/STORY/GHOST BATTLE header was intentionally excluded because it belonged to a separate batched font path.

This experiment proved the semantic classifier, but the larger v9 container/installer work introduced unrelated stability/layout concerns.

## SideNames v9.1

```text
ZIP SHA-256:
49bc6c63f4895b0608a53911aa69e59c8c22a9136c00f05bd756f73e541f2430

PRX SHA-256:
b299e35bf372c36395720de5e6a6eb42235b31d3809fe1380102b8e7132dab97

PRX size:
6046 bytes

PT_LOAD:
p_filesz = p_memsz = 0x1054
```

v9.1 removed the failed installer/trampoline chain and converted the new classification to branch-only control flow inside the existing rectangle hook.

The classifier used:

- no function calls;
- no new stack frame;
- no RA modification;
- relative branches back into the existing CENTER/side paths.

This separated the character-name semantic idea from the earlier trampoline failure.

## SideNames v9.2 CLEAN

```text
ZIP SHA-256:
409d1751339331b81f4e36154ebd22cf3d033a8aa3729e0a313214e3e6bf0aba

PRX SHA-256:
87af2db9b6211b5fda5f1d95847102dc99df69ddc662b9642f3091b0fd6adec7

PRX size:
5626 bytes

PT_LOAD:
p_filesz = p_memsz = 0x0EB0
```

v9.2 intentionally restarted from exact known-good v8.1 layout.

Only two existing MIPS instructions were changed in place.

The diagnostic classifier used the already scoped row identity:

```text
y=7   -> CENTER timer
y=10  -> SIDE player panel
y=27  -> CENTER round family
y=28  -> SIDE character names
```

The actual temporary implementation used even/odd row parity only as a minimal validation patch; the permanent semantic design remained explicit predicates.

This build became the compact rollback point used for later Practice/Gold research.

## Stable rollback

```text
Tekken6-HUD-v9.2-Stable-Rollback

ZIP SHA-256:
775830ffa8f6dac937c6928d98e86f58e00284a7297c3bf11455b46f03b14084

PRX SHA-256:
87af2db9b6211b5fda5f1d95847102dc99df69ddc662b9642f3091b0fd6adec7
```

This is byte-identical to the v9.2 CLEAN PRX and was retained specifically as a recovery point before further Practice/mode-font work.

---

# 6. First integrated Practice/Gold attempt and texture regression

## ModeHUD v10

```text
ZIP SHA-256:
49e77dbfafcc30c1d0244cc6f106789f2f4a71f590c3d082a684caad62615dda

PRX SHA-256:
f43630943fb9cd83a2ceeb144133537ce223dede5a2e414dd8ba295a03e28c87

PRX size:
6836 bytes

Program LOADs:
LOAD 0: p_filesz=p_memsz=0x0EB0 at vaddr 0
LOAD 1: p_filesz=p_memsz=0x0474 at vaddr 0x2000
```

v10 integrated all then-known normal battle HUD corrections with Practice/Gold mode behavior.

To avoid enlarging the validated first LOAD, it added a second executable LOAD at module-relative vaddr `0x2000`.

The retained test note explicitly asks for replacement-texture and fast-forward regression checks.

Observed research outcome: custom replacement textures regressed again.

This showed that merely keeping LOAD0 at `0x0EB0` was not sufficient if the total resident module mapping changed.

## ModeHUD v10.1 PSPDEV

```text
ZIP SHA-256:
084e30ffe08806e82a412a687dc158d329d0049da20dc625ba508083cf99dc4f

PRX SHA-256:
5ec858ea0f7a06a7b4c9130e978adef2b993bf8c41c7ec07d40ad25d60f08206

PRX size:
6870 bytes

one PT_LOAD:
p_filesz = 0x12BC
p_memsz  = 0x12D0
```

This build tested whether the v10 failure came from hand-editing the ELF/program-header structure.

v10.1 was rebuilt with the normal PSPDEV toolchain into one conventional LOAD.

The custom-texture regression still motivated a controlled A/B rather than accepting "hand-edited ELF" as the root cause.

## TextureAB v10.2 NoFontHook

```text
ZIP SHA-256:
52dd3481a596d96c6ed186069fd00e16824e6205c71830a76d612cf547036411

PRX SHA-256:
c85d86eee31fdb804e692dedc68dafb76b8ddb6c72a2b638d2c0b490b0093ffd

PRX size:
6766 bytes

one PT_LOAD:
p_filesz = 0x1284
p_memsz  = 0x12D0
```

This controlled the runtime memory-size variable while disabling execution of the global mode-font hook.

The hook code remained linked and a BSS pad kept allocation equal to v10.1.

Interpretation planned by the test:

- textures recover -> executed font hook is causal;
- textures still fail -> enlarged module allocation/memory layout is causal.

The subsequent memory-size-only A/B established the second result.

## v9.2 MemSize A/B

```text
ZIP SHA-256:
bbd2c7d76759c6dc8caa810bd0102e51afd03d2ab2c025af20c3e5b6de09e270

PRX SHA-256:
c23dc427940a2f985da708e2dd4c663eee4ba3ecdb129cb20f188c9078774285

PRX file size:
5626 bytes

p_filesz:
0x0EB0

p_memsz:
0x12D0
```

This was the strongest control because the PRX was the exact known-good v9.2 code with only the ELF `p_memsz` changed from `0x0EB0` to `0x12D0`.

All code, hooks, sections, relocations, entry point, and payload bytes were unchanged.

Device testing reproduced the custom font/text replacement-texture regression.

Conclusion:

> resident module allocation size alone was enough to perturb the game's/PPSSPP's dynamic texture replacement behavior.

This established the hard design rule for later compact builds:

```text
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

---

# 7. Compact Practice/Gold experiments

## ModeCompact EXP1

```text
ZIP SHA-256:
c23ee847309acfeafedc3714249ad91607a87f275cd5414d8ffa7263526b930f

PRX SHA-256:
eacafc988b04d14e567cb23fdf08d1de2cdf15da731e2a349876bbd8d9cdc81f

PRX size:
5626 bytes

PT_LOAD:
p_filesz = p_memsz = 0x0EB0
```

EXP1 repacked existing winner-glow logic to create just enough code space and installed a narrow internal glyph hook at the later font stage.

Ownership requirements included:

```text
render context = traced battle context
saved caller return = 0x08973C84
stock packed scale = 100/100
```

Targets:

```text
Practice:
x < 200
104 <= y < 140

Gold REWARD:
270 <= x < 380
y = 25

Gold ATTACK VARIATION:
x >= 128
y = 73
```

Gold money/value strings were deliberately excluded.

EXP2's retained note records that EXP1 proved the compact `0x0EB0` integration could preserve custom Tekken replacement textures.

## ModeCompact EXP2

```text
ZIP SHA-256:
0836bdd39799811bd20174f035f5bec9ef507307c9aa994b3e35081cdb6d22a7

PRX SHA-256:
3a5f19fcacb80118e3c9978faaca87a37136698dbabf1e01f99bed3696779ab3
```

EXP2 removed EXP1's late-only font interception and moved the scale change earlier to:

```text
0x08970A90
```

where Tekken first loads horizontal text percentage.

Stable owner checks:

```text
saved caller return = 0x08973C84
saved a1 = 1
stock scale = 100
```

Practice:

```text
100 -> 80 horizontal scale
```

Gold:

```text
x += 120
then 80% scale

0.8*(x+120) = 0.8*x + 96
```

The early-stage change produced the desired visible glyph de-stretch, but the Practice infinity rule was based on the wrong inferred pre-transform identity.

## ModeCompact EXP3

```text
ZIP SHA-256:
c359b3fee561102523ef8ad926e402ad3aec2150750c73f221f280e0d22c204e

PRX SHA-256:
4f27caf587b122a846d0be2f8502da11b0ebc3a11cb0c526cfc2285fe4357a21
```

EXP3 changed only the Practice infinity recognition.

The reliable stock-entry signature was:

```text
x = 166
y = 6
width = 51
height = 32
```

Correction:

```text
x = 214
```

The mode-font experiment remained identical to EXP2.

Device comparison later established:

- visible Practice/Gold de-stretch was good;
- Practice infinity was good;
- Gold placement was wrong.

## ModeCompact EXP4

```text
ZIP SHA-256:
ef316a4281a107f0b94a65eb0b73e604d352c73b99fc6957cb8ca3fee892d622

PRX SHA-256:
5994089dfa90df4a11587be1d1168631434ec340841f9864361de4c9bd7846cd
```

EXP4 addressed mixed renderer state.

Static review showed EXP2/EXP3 changed the live scale at `0x08970A90` while a later fast-path still observed the old packed 100/100 state.

EXP4 therefore removed the early jump and wrapped the later:

```text
0x08970B24
```

path, synchronizing:

```text
packed X scale: 100 -> 80
live scaleX:     100 -> 80
cached width factor: *0.8
```

Gold still used source +120.

Device comparison showed:

- Practice infinity good;
- Gold placement good;
- stability good;
- target text still looked horizontally stretched because important geometry had already been derived from 100% scale.

## InfinityOnly EXP5

```text
ZIP SHA-256:
34e73964e0e0adab1de69cc65ce5ff76b8579b42625fbd38147e3f2532365faa

PRX SHA-256:
44c80a417e3602d4e9b8553cdcf89be9348e208582c28c0e3b7a9dcfd8ee3ea2
```

EXP5 deliberately removed the mode-font correction and retained only the validated Practice infinity rule.

It served as the stable fallback while the font architecture was still unresolved.

## ModeCompact EXP6

```text
ZIP SHA-256:
f2f0b3a75559adc9c68bb8a70dde6fa7891573145fd5d2b4a4ac40ab784b5efd

PRX SHA-256:
38c9b2ebc86201263300d9a0503b7bd0b382e287c9a7010eef53d6834f400f9f

PRX size:
5626 bytes

PT_LOAD:
p_filesz = p_memsz = 0x0EB0
```

EXP6 combined the strongest parts of EXP3 and EXP4.

Stage 1:

```text
0x08970A90
target horizontal scale 100 -> 80
```

Stage 2:

```text
0x08970B24
packed X scale -> 80
Practice authored X unchanged
Gold authored X += 120
```

No second cached-factor multiplication was applied at the late stage because the early scale had already caused Tekken to derive the correct horizontal factor.

This produced the accepted fixed-20:9 mode-HUD behavior.

This later fixed-ratio build became a known-good comparison artifact during AutoHUD debugging; it was not the starting baseline of the research.

---

# 8. AutoHUD experiments: partial record before EXP11

The retained artifact set begins at EXP11, but later research notes preserve several important facts about EXP7–EXP10.

The exact binaries/test notes for every one of these early AutoHUD experiments were not recovered, so this section deliberately records only what later notes prove.

## EXP8

Later binary comparison established that EXP8 kept the HP-fill hot hook in the same effective EXP6 instruction/register shape and changed the coefficients by startup self-patching.

It was therefore a useful later comparison point even though the broader AutoHUD line still had unrelated mode/font issues.

## EXP9–EXP10

The EXP9–EXP13 line experimented with runtime coefficient loads/storage inside hot hooks.

Later EXP11 notes establish two distinct regressions inherited through EXP9/10:

1. Gold font path:
   two Gold branches could enter at the runtime font-percentage load while skipping the scratch-base setup, so stale `v0` was used and `REWARD` became broken/widely spaced.

2. HP transport:
   later builds changed how the dynamic HP coefficients reached FPU registers, including new relocation-dependent/internal-storage variants.

EXP10 did not repair the observed device behavior.

This period taught the project not to assume one regression had one cause.

---

# 9. AutoHUD EXP11–EXP14

## EXP11 — targeted regression repair

```text
ZIP SHA-256:
bc6cda7dbaf625e895151a1dca2aeb8267442cf4c5946c3b4c33aa3f382d22ba

PRX SHA-256:
7bcbd1cfec96063c8f5e0d9bf2a8ac9489952910f931544f2fca0b7202696ed1

PRX size:
5626 bytes
PT_LOAD p_filesz=p_memsz=0x0EB0
```

EXP11 fixed the Gold branch-entry problem by routing both target branches through the scratch-base setup before the percentage load.

It also revised HP parameter transport to avoid the new relocation dependency introduced earlier.

Device result preserved by EXP12 notes:

- Gold `REWARD` restored;
- custom textures preserved;
- HP fill still missing.

This cleanly isolated the remaining problem to the HP path.

## EXP12 — HP transport repair attempt

```text
ZIP SHA-256:
70e9aef441f56a65f6be1aedccc0f459c157ccf945e57ff8f6b88af8dfa04456

PRX SHA-256:
4f186cd0c56bc18c2a8b815d897b60448b13ab1c23ead24335916d1aa3e40b56
```

EXP12 focused on the difference between the earlier working EXP8 coefficient handoff and EXP9–11.

It restored:

```text
LW integer bits
MTC1 to FPU
```

instead of direct `LWC1` transport.

The final f12 multiply was placed in the stock jump delay slot to reproduce the known renderer-entry shape.

HP fill still did not return.

This rejected "LWC1 versus LW+MTC1" as the sole cause.

## EXP13 — exact-shape HP repair attempt

```text
ZIP SHA-256:
03f85f3026306efe855aaff21911f1f9ced163655388dd9294bf4e91ee274640

PRX SHA-256:
63a457f33745dfe6b26d9df30aadd44d163264516f3f2a8246222ebf93534b4b
```

EXP13 was based on the observation that EXP8 had preserved the EXP6 hook shape and changed only coefficients.

EXP13 therefore restored the EXP6-style live register/FPU sequence while still consuming aspect-derived parameters from the AutoHUD parameter block.

HP fill still remained missing.

This made another coefficient-transport rewrite increasingly unlikely to be productive.

## EXP14 — complete gauge-hook isolation

```text
ZIP SHA-256:
66f0f4286d5f829c8c9f2e6b5e67be39d96c3733c5cf154b2e6be6820930ce6f

PRX SHA-256:
a6ccbbe59d3440cd657132d05d0968702a86ce8b89909b14a0c7bfd6670f7a46
```

EXP14 copied the complete device-validated EXP6 HP gauge hook byte-for-byte back into the AutoHUD build.

It intentionally restored the fixed 20:9 values:

```text
shift +/-1.3056111
scale 1.0493455
```

Everything else remained AutoHUD.

HP fill **still** remained missing.

This was the decisive isolation result:

> the missing HP fill was outside the gauge hook.

That result triggered the downstream runtime packet-tracing investigation documented in [`hp-fill-auto-aspect.md`](hp-fill-auto-aspect.md).

---

# 10. EXP15 control-flow repair

EXP15 was produced after runtime tracing found stale rejection branches in the shortened side-strip hook.

Exactly one forwarding instruction was restored at PRX VA `0x092C`:

```text
NOP
  ->
J 0x08825EAC
```

The PRX remained:

```text
5626 bytes
one PT_LOAD
p_filesz=p_memsz=0x0EB0
```

Validated EXP15 PRX SHA-256:

```text
54c47d12b991ac093c8311986a24ba307efb42056ea0f313bc66f46e695d7d74
```

The colored HP fill returned and all four HP paths reached stock submission successfully.

EXP15 repaired the draw path, but the HP gauge still used fixed EXP6 20:9 constants.

---

# 11. EXP16 and EXP17

## EXP16 DynamicHP

```text
ZIP SHA-256:
52378d11f3eb605ea05f4d863556160d21c4dfcc4028e449fd82cd8da8134db6

PRX SHA-256:
f6cb1f8ed9d8e2fe36f80d197be14997f480a8cc15b6967f74aae3472f007f38
```

EXP16 attempted to preserve the EXP6-shaped hot hook and self-patch its HP constants at startup.

HP worked.

However, it reused initializer instructions that were not actually dead.

Device result:

- Practice combo/hit text disappeared;
- Gold Rush `REWARD` disappeared;
- Gold Rush `ATTACK VARIATION` disappeared;
- some main-menu text disappeared.

EXP16 was rejected.

## EXP17 DynamicHPReads

```text
ZIP SHA-256:
b0561483647c39f895011b44c1ed31a8473c0ed3d7c16740bf3ac575a344ee74

PRX SHA-256:
311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75
```

EXP17 restarted from exact EXP15.

The entire initializer was preserved.

Only the HP coefficient transport changed so the gauge consumed the already-computed dynamic shift/scale values.

The device regression sweep passed:

- HP fill;
- Practice combo/hit text;
- Practice infinity;
- Gold Rush target labels;
- Arcade;
- Story;
- Ghost Battle;
- main-menu text stability;
- replacement textures/fonts.

This PRX became the v1.2.0 release artifact.

---

# 12. Duplicate retained artifacts

Two copies of the same EXP6 ZIP were supplied during reconstruction:

```text
Tekken6-HUD-v9.3-ModeCompact-EXP6(5).zip
Tekken6-HUD-v9.3-ModeCompact-EXP6(7).zip
```

They are byte-identical:

```text
ZIP SHA-256:
f2f0b3a75559adc9c68bb8a70dde6fa7891573145fd5d2b4a4ac40ab784b5efd
```

This is useful provenance confirmation rather than two separate experiments.

---

# 13. What the artifact sequence demonstrates

The retained builds show a consistent research methodology:

1. isolate one renderer/owner;
2. build the smallest possible test;
3. preserve a known-good rollback;
4. record exact PRX hash;
5. test device behavior;
6. avoid interpreting unrelated regressions as proof about the target feature;
7. control ELF/module footprint independently from hook execution;
8. use later A/B builds to challenge previous causal assumptions;
9. freeze known-good checkpoints before opening a new subsystem;
10. only generalize fixed 20:9 behavior after the entire battle HUD was understood.

The v1.2.0 release is therefore the end of a long chain of falsifiable experiments rather than a single aspect-ratio formula.
