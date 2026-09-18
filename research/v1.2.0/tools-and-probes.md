# v1.2.0 research tools and probe methodology

These tools were used to answer narrow ownership, geometry, ABI, and control-flow questions during HUD reverse engineering.

---

## 1. Frame-dump A/B diagnostics

### Frame-dump cheat set

Purpose:

- create reproducible baseline/modified PPSSPP frame dumps;
- isolate which draw group owns a visible HUD element;
- prove that HP shell and colored fill are independent paths.

Important A/B states:

```text
A control
B hide health-bar group
C shift HP fill only
```

This was the earliest high-value technique because it reduced the problem from "the HUD is stretched" to "this exact draw family owns this exact visual."

---

## 2. `ppdmp_hud_diff.py`

Purpose:

- compare PPSSPP frame-dump draw calls between controlled states;
- group candidate draws by geometry, texture/format, and state;
- identify rectangles whose visibility or position changes only in the patched capture.

Used for:

- HP shell family;
- side HUD;
- center/round candidates;
- initial battle composition.

Method:

1. capture a stock/control frame;
2. change one diagnostic patch;
3. capture again;
4. diff draw calls rather than visually guessing;
5. correlate unique geometry back to CPU-side owner code.

---

## 3. Round-win capture and analysis

### `ppsspp_round_win_capture.mjs`

Purpose:

- collect runtime state around the newly earned round marker;
- distinguish the immediate earned orb from the persistent next-round marker.

### `ppdmp_round_win_analysis.py`

Purpose:

- compare neutral, P1-win, and P2-win frames;
- isolate the ordinary round-marker rectangle from the residual animated glow.

This work led to two independent fixes:

- one-pixel P2 late-orb lower bound;
- separate winner-glow converter correction.

---

## 4. Side-label capture and analysis

### `ppsspp_side_labels_capture.mjs`

Purpose:

- record stable top-HUD rectangles in Arcade/Story/Ghost;
- correlate authored positions with P1/P2 semantic ownership.

### `ppdmp_side_labels_analysis.py`

Purpose:

- group persistent labels by Y/height/width;
- identify the character-name family separately from the shared top battle header.

This established:

```text
character name:
y=28
height=16
width=64 or 128

authored X < 240 -> LEFT
authored X > 240 -> RIGHT
```

The analyzer also helped prove that the top ARCADE/STORY/GHOST header belonged to a different font path and should not be changed by the rectangle classifier.

---

## 5. Center-timer owner tracing

The timer investigation relied on static callsite verification plus a narrow runtime scope wrapper.

Important owner calls:

```text
0x08929AF8
0x08929B44
```

Original target:

```text
0x0892D72C
```

The first implementation disappearing entirely led to ABI inspection and the fifth stack-argument discovery.

This subsystem is a useful example of why "correct transform math" and "correct hook ABI" must be validated separately.

---

## 6. Practice/Gold mode-HUD capture

The Practice and Gold Rush investigation used a sequence of increasingly narrow tools.

### Mode HUD capture/analyzer

Purpose:

- capture the Practice statistics panel and Gold Rush rows;
- group glyphs by authored X/Y and scale state;
- separate target labels from money/currency/floating-value rows.

### Per-glyph analyzer

Purpose:

- stop reasoning about an entire batch;
- identify individual glyph row geometry and the portion of `ATTACK VARIATION` that an initial X gate missed.

This was what justified broadening the upstream Gold X gate while keeping caller/owner checks narrow.

---

## 7. Mode-font owner probes

Several debugger probes progressively traced the shared text pipeline.

Research progression:

1. identify the batch by geometry;
2. stop before the critical delay slot;
3. support the active PPSSPP debugger stepping protocol;
4. trace the producer/caller context;
5. trace Practice source writer;
6. trace Gold glyph context;
7. identify the shared glyph ABI;
8. audit whether a compact hook could be safely scoped.

The final stable owner checks used combinations such as:

```text
saved caller return
saved a1
stock horizontal scale
target x/y row
```

rather than a global "all text" transform.

This work produced the EXP2–EXP6 early/late font-stage architecture.

---

## 8. WebSocket smoke test

A small debugger smoke test was used before arming expensive probes.

Purpose:

- verify that PPSSPP remote debugging is reachable;
- request version/game status;
- distinguish transport failure from probe logic failure.

Research rule:

> never interpret a probe timeout as a game/rendering finding until basic debugger transport and game identity are independently verified.

---

## 9. HP fill path probe

### `ppsspp_hp_fill_path_probe.mjs`

Purpose:

- compare a known-good fixed-ratio build with a broken AutoHUD build at the exact gauge owner/renderer boundary.

Captured:

- live owner words;
- decoded hook target;
- effective source pointer;
- side field;
- source XY;
- `f12`;
- renderer-entry XY/FPU/GPR state;
- JAL versus tail-J pairing.

Key corrections made during probe development:

### JAL owner

```text
0x0892C1F0
delay slot: move t1,s0
return:     0x0892C1F8
```

The effective hook input had to use the post-delay-slot state.

### Tail-J owner

```text
0x0892C26C
delay slot: addiu sp,sp,0x20
```

Pairing had to account for the changed stack pointer and preserved incoming RA.

The probe disproved the hypothesis that EXP14's gauge hook was not running.

---

## 10. HP renderer/downstream probe

### `ppsspp_hp_renderer_probe.py`

Purpose:

- follow a matched HP packet beyond the gauge renderer until final stock submission;
- locate the first causally meaningful divergence.

Stages:

```text
renderer entry
texture/descriptor lookup return
packet-builder call
packet-ready
side-hook gate
stock submission
renderer return
```

This probe established the known-good HP packet path and found that the broken AutoHUD candidate never reached stock submission.

It then showed that HP packets were taking a stale side-hook rejection branch into the wrong fall-through region.

This was the probe that turned the missing HP fill from a coefficient hypothesis into a one-word control-flow repair.

---

## 11. JIT-aware disassembly

PPSSPP's debugger disassembly path was used when raw memory did not show the expected guest instructions.

Reason:

- JIT bookkeeping can alter the raw representation around active code;
- the guest instruction semantics are better validated through the debugger's instruction-aware disassembly.

Rule adopted:

> use raw bytes for binary artifact comparison, but use JIT-aware disassembly to determine what guest code PPSSPP is actually executing.

---

## 12. Hook-site verification

### `verify_hud_hook_sites.py`

Purpose:

- check stock game instructions before installing hooks;
- reject unsupported/revision-mismatched code rather than patching blindly.

This was especially important for:

- HP gauge owners;
- timer calls;
- winner glow callsite;
- mode-font stages.

Research policy:

> every fixed-address hook should have a stock-word expectation before it is considered safe.

---

## 13. Candidate generators

The late AutoHUD work used deterministic offline binary generators rather than ad-hoc editing.

### EXP15 bypass candidate generator

Purpose:

- take the exact EXP14 artifact;
- verify its checksum/layout;
- change only the stale common forwarding word;
- reject unexpected binary differences.

### EXP16 DynamicHP generator

Purpose:

- start from exact validated EXP15;
- test startup self-patching of HP coefficient immediates;
- preserve the compact layout.

Result:

- HP worked;
- text/font regression proved reused initializer instructions were still live;
- architecture rejected.

### EXP16 startup verifier

Purpose:

- read live gauge coefficient instructions;
- reconstruct detected aspect;
- compare actual patched float bits to expected aspect-derived HP values.

This separated "self-patch math works" from "the rest of the build is regression-free."

### EXP17 DynamicHPReads generator

Purpose:

- restart from exact EXP15;
- preserve the entire initializer;
- change only the HP coefficient transport;
- verify exact six-word diff and layout invariants.

This candidate became v1.2.0 after device validation.

---

# 14. Probe cleanup rules

Several practical rules emerged during remote-debugger research:

- use execution breakpoints only where necessary;
- remove breakpoints on success, failure, timeout, and cancellation;
- resume the CPU after a stopped probe unless the test requires a paused state;
- record raw output before the next test action;
- avoid broad conditions in hot render loops;
- pair caller/renderer state using RA/SP/thread context;
- do not trust stale pre-delay-slot registers;
- treat malformed unsolicited debugger logs as transport noise unless they correlate with guest execution;
- confirm game ID before applying address-specific logic.

---

# 15. Experimental philosophy

The toolchain became most effective when every probe answered one narrow question.

Examples:

```text
Does this draw own HP shell or fill?
Does the immediate first P2 orb use x=273?
Does the timer wrapper preserve every ABI argument?
Is this name rectangle LEFT or RIGHT owned?
Does early scale change glyph width before geometry is derived?
Does the broken AutoHUD candidate reach the same HP renderer state as the known-good fixed-ratio build?
Does the packet reach stock submission?
```

That approach avoided large speculative rewrites and produced the sequence of falsifiable experiments documented in the build archive.
