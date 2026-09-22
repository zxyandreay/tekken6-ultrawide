# Operator / Analyst Research Workflow

**Status:** ACTIVE RESEARCH / WORKING PROTOCOL

This document defines the collaboration model used for interactive reverse-engineering work on this branch.

The role names describe responsibilities, not specific people or tools. A contributor may perform either role, and the roles may change between sessions.

The objective is to keep runtime operation, evidence interpretation, implementation, and validation clearly separated so results remain reproducible.

---

## 1. Roles

### Operator

The Operator controls the live PPSSPP/game environment and reproduces requested runtime states.

Typical responsibilities:

- run PPSSPP on the target device;
- start the correct Tekken 6 build and plugin state;
- enable or disable cheats/plugins exactly as requested;
- enter a requested game mode or battle state;
- arm probes at the requested moment;
- perform short actions such as a combo, round win, loss, low-HP state, or transition;
- collect terminal/debugger output without editing it;
- provide screenshots or visual observations when requested;
- test candidate PRXs on the target device;
- verify regressions such as fast-forward and replacement textures;
- report what was actually observed rather than what was expected.

The Operator is the authority for physical-device behavior.

### Analyst / Engineer

The Analyst/Engineer turns static and runtime evidence into testable renderer hypotheses and implementation candidates.

Typical responsibilities:

- inspect EBOOT/PRX disassembly and binary layout;
- analyze frame dumps, logs, runtime captures, and screenshots;
- identify candidate owners, builders, callsites, and predicates;
- audit MIPS ABI, delay slots, stack arguments, and register state;
- design narrow read-only probes;
- design deterministic binary builders;
- produce one-variable experimental PRXs;
- compare accepted/rejected candidates;
- maintain exact hashes and binary-layout guards;
- document conclusions, uncertainty, regressions, and next steps.

The Analyst/Engineer must not treat an untested assumption as a device result.

---

## 2. Core research loop

Use this loop for each unresolved target.

```text
1. Analyst defines one narrow question
            |
            v
2. Analyst prepares exact probe / command / state request
            |
            v
3. Operator reproduces the requested state
            |
            v
4. Operator returns raw output + visual observations
            |
            v
5. Analyst interprets evidence
            |
      +-----+------+
      |            |
  insufficient   hypothesis supported
      |            |
      v            v
new narrow probe  one-variable candidate build
                   |
                   v
            Operator device test
                   |
             +-----+------+
             |            |
          rejected      accepted
             |            |
             v            v
       archive lesson   findings + next target
```

Do not skip directly from a visual hypothesis to a broad patch when a read-only measurement can answer the question first.

---

## 3. Analyst-to-Operator request format

Every runtime request should be executable without requiring the Operator to interpret renderer internals.

A good request contains:

```text
Purpose:
What single question the probe is answering.

Prerequisites:
Plugin/cheat state, mode, debugger state, and any required clean restart.

Command:
Exact command to run.

Game state:
Exact screen/mode/health/round condition to reach.

Action:
What to do after the probe arms.

Stop condition:
What event ends the capture.

Return:
Exactly which terminal output, log, screenshot, or observation is needed.
```

Example structure:

```text
Purpose:
Check whether Promotion Chance reaches the known shared slot builder.

Prerequisites:
Stock game, plugin disabled, no HUD cheats.

Command:
node <probe> <IP:PORT>

Game state:
Ghost Battle with Promotion Chance not yet visible.

Action:
Press Enter when instructed, then trigger Promotion Chance.

Stop condition:
Probe reports capture complete.

Return:
Paste the complete terminal output unchanged and say whether the
Promotion Chance indicator was visible during the capture.
```

Avoid vague requests such as 'test this for a while' when an exact state can be specified.

---

## 4. Operator-to-Analyst result format

Preserve raw evidence.

Preferred response:

```text
Command:
<exact command used>

Environment:
PPSSPP build / device / plugin state if changed from previous test

Observed game state:
<what was visibly on screen>

Raw output:
<complete terminal/debugger output>

Visual result:
<what visibly changed or did not change>

Unexpected behavior:
<crash, freeze, missing texture, wrong animation, etc.>
```

Do not clean up, reorder, summarize, or silently omit debugger lines unless the raw log is also preserved.

If the requested state was not reached, report that explicitly.

---

## 5. Evidence authority

Different evidence answers different questions.

### Static binary evidence

Best for:

- exact instructions;
- branches and delay slots;
- call graph candidates;
- literal/resource tables;
- PRX layout;
- relocation behavior.

Static evidence can prove what code exists, but not that a visual target uses it at runtime.

### Runtime capture

Best for:

- active owner/caller;
- live packet/descriptor identity;
- authored geometry;
- stack/register state;
- state-dependent routing.

Runtime hits must be tied to a known visible game state.

### Frame-dump evidence

Best for:

- final primitive identity;
- texture/CLUT;
- UV;
- bbox;
- draw order;
- layered effects.

A visually related primitive is not automatically the semantic owner.

### Device observation

Best for:

- final visual correctness;
- animation behavior;
- transition behavior;
- replacement textures/fonts;
- fast-forward;
- crashes or mode-specific regressions.

For visible behavior, device observation is the final acceptance authority.

---

## 6. Result vocabulary

Use explicit result states.

### ACCEPTED

The target behavior is device-validated and the baseline regression matrix passes.

### REJECTED

The experiment produced an incorrect result, regression, crash, or disproved hypothesis.

### SUPERSEDED

The experiment was useful but a later implementation or interpretation replaced it.

### DIAGNOSTIC

The build/probe intentionally changes behavior only to answer a question and is not a release candidate.

### RESULT NOT RECORDED

The test was prepared or run but no reliable device result is available.

### INCONCLUSIVE

The evidence does not distinguish competing hypotheses.

Never convert `not tested` into `passed`, and never convert `target moved` into `correct owner confirmed` without verifying the actual target layer and behavior.

---

## 7. One question per probe

Prefer probes that answer one narrow question.

Good examples:

- Does Promotion Chance hit `0x0892D9F8`?
- Which caller/resource tuple appears only while PERFECT is visible?
- Does CONTINUE text pass `0x08970A90`?
- Do YOU WIN and YOU LOSE share the same owner?
- Does the result composition expose one parent X transform?

Avoid probes that simultaneously patch geometry, rewrite state, sample many hot renderers indefinitely, or infer ownership from raw hit count.

A failed narrow probe is useful evidence. A broad noisy probe may be impossible to interpret.

---

## 8. One architectural variable per candidate build

When moving from measurement to a PRX experiment, change one thing whenever possible.

```text
EXP-T1: PERFECT only
EXP-T2: same renderer + YOU WIN/LOSE family
EXP-T3: CONTINUE prompt only
EXP-T4: Promotion Chance LEFT ownership
EXP-T5: result-screen parent or first child family
```

Do not combine a new HUD correction, code-space optimization, renderer refactor, and memory-layout change in the same experiment.

If the build fails, the cause should be attributable.

---

## 9. Candidate-build handoff

Every candidate given to the Operator should include:

```text
Candidate ID:
EXP-Tn / descriptive name

Parent:
exact accepted PRX SHA-256

New PRX:
exact SHA-256

Purpose:
one sentence

Expected visible change:
what should move / de-stretch / stay fixed

Known untouched areas:
what must remain identical

Test sequence:
short ordered list

Regression checks:
custom textures
fast-forward
existing solved HUD
startup / mode transitions
```

The Operator should not need to infer what a successful test looks like.

---

## 10. Device-validation discipline

A target is not accepted from a single screenshot if it has meaningful state variants.

Test all relevant states.

Examples:

### Winner-like transient overlays

- first occurrence;
- later occurrence;
- win/lose variants;
- transition in/out;
- animation intact.

### Promotion Chance

- visible;
- absent/control state;
- P1/left ownership preserved;
- neighboring bottom HUD unchanged.

### CONTINUE

- at least two countdown values;
- prompt centered;
- number centered relative to prompt;
- transition into/out of screen.

### Result composition

- all major child groups remain coherent;
- no clipping;
- no unintended movement of unrelated UI;
- neighboring modes remain sane.

---

## 11. Regression canaries

Every candidate that modifies runtime code must preserve the accepted baseline.

Minimum canaries:

- cold boot;
- normal gameplay;
- HP full/partial/low;
- side strips and ranks;
- character names;
- timer;
- persistent round markers;
- first/later P1 winner glow;
- first/later P2 winner glow;
- glow animation;
- Practice;
- Gold Rush;
- custom replacement textures/fonts;
- fast-forward.

If a candidate fixes the target but breaks one of these, it is rejected unless the experiment was explicitly diagnostic.

---

## 12. Raw evidence and interpretation must stay separate

Keep raw capture separate from interpretation.

```text
Observed:
RA=..., a1=..., X=..., texture=...

Interpretation:
Likely transient banner owner.

Uncertainty:
Only PERFECT was captured; YOU WIN/LOSE not yet compared.

Next test:
Capture YOU LOSE at the same boundary.
```

This prevents later contributors from mistaking an early interpretation for measured fact.

---

## 13. Session handoff / contributor change

Before ending a research session, leave enough state for another contributor to continue without reconstructing the experiment.

Minimum handoff:

```text
Branch and HEAD commit
Accepted runtime baseline/hash
Current target
Current hypothesis
What is already proven
What is still unproven
Last probe/build used
Last device result
Known rejected approaches
Exact next recommended test
Any required files/logs
```

If there is an uncommitted experiment, state that explicitly.

The next contributor should read, in order:

1. topic `README.md`;
2. `HYPOTHESES.md`;
3. `HANDOFF.md`;
4. this workflow;
5. `PROBE_WORKFLOW.md`;
6. current `findings/`;
7. only then relevant `archive/` material.

---

## 14. Operator workload design

Interactive tests should be easy to execute correctly.

Prefer:

- short capture windows;
- obvious visual states;
- one Enter-to-arm step;
- clear stop messages;
- automatic cleanup;
- no requirement to hold an approximate state for long periods.

Avoid requiring the Operator to manually decode registers, estimate frame timing, maintain an exact health percentage for long periods, decide which debugger hits look relevant, or modify binary files manually.

If a test is hard to operate reliably, improve the probe rather than accepting noisy evidence.

---

## 15. Failure handling

When an experiment behaves unexpectedly:

1. record the exact device result;
2. do not immediately broaden the patch;
3. determine whether the failure is transport, probe, ABI, owner, transform, or layout related;
4. return to the smallest measurement that can distinguish those causes.

Examples:

```text
WebSocket timeout
-> transport issue, not renderer evidence

Target moves but animation stops
-> likely wrong layer/state mutation

Game crashes when HUD appears
-> likely runtime hook/ABI/addressing issue

Custom textures fail
-> treat module/layout compatibility as suspect

First state works, later state fails
-> ownership predicate incomplete
```

---

## 16. Acceptance and documentation flow

Once a target passes:

```text
raw evidence
    ↓
accepted experiment
    ↓
research/transient-ui/findings/
    ↓
full regression validation
    ↓
exact artifact hash frozen
    ↓
future merge/release preparation
```

Rejected or superseded work goes to `research/transient-ui/archive/`.

Reusable probes/builders belong under `tools/research/`.

Canonical project-wide rules should only be promoted into `docs/` after they are stable beyond this one research topic.

---

## 17. Guiding principle

> Measure narrowly, interpret explicitly, patch minimally, validate on device, and preserve the evidence.

The Operator should receive precise, reproducible tasks.

The Analyst/Engineer should receive raw, trustworthy observations.

Neither role should fill gaps in the other role's evidence with assumptions.
