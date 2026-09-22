# Winner-glow revalidation plan — 2026-09-21

## Why this revalidation exists

The earlier claim that OPT-EXP2S3/EXP3A fixed the rotating winner halo was withdrawn after deliberate retesting.

The halo is still on the wrong orb in both builds.

The previous EXP3B attribution is therefore invalid: EXP3B did not establish a new halo regression because the baseline was already wrong.

## New binary finding

Historical RoundWin v7 and released v1.2.0 do not use identical winner-glow code.

### RoundWin v7

The dedicated v7 build uses hard-coded 20:9 math:

```text
scale = 0.8
shift = 48
x' = 0.8*x + 48
```

The original v7 package explicitly described this as device-proven.

### Released v1.2.0 / optimization descendants

Later AutoHUD compaction rewrote the glow transform to use shared runtime parameters:

```text
scale  <- [0x08802304]
span   <- [0x08802328]
shift  <- span * 0.5
x'     <- scale*x + shift
```

At exact 20:9 these should mathematically equal v7, but the implementation was not byte-identical and must be re-proven.

## Diagnostic sequence

### Test A — historical RoundWin v7

Test the untouched archived v7 artifact on the same device.

Question:

> Does the historical build actually place the spinning halo on the newly earned orb?

This revalidates the original historical claim itself.

### Test B — current EXP3A with exact v7 math

Use device-stable EXP3A but replace only the five dynamic glow-math instructions with the exact v7 constants:

```text
f4 = 0.8
f6 = 48
```

Everything else stays current:

- current callsite hook;
- current predicate;
- current converter;
- current source save/restore;
- HP/font/slot optimizations;
- 0x0EB0 resident layout.

Interpretation:

- v7 correct + V7Math correct => dynamic AutoHUD glow parameter path is causal;
- v7 correct + V7Math wrong => predicate/ownership/install path changed later;
- v7 wrong too => original historical validation was itself incorrect/incomplete;
- V7Math visibly changes the halo but does not align => hook owns the effect but the assumed CENTER target is wrong.

## Important observation from archived frame dumps

The winner-glow texture appears as eight same-center submissions per burst frame.

Therefore the visible spin is a layered effect.

The investigation must prove that the production CPU hook affects the complete visible layered result, not merely one related converter submission.

No GitHub Actions are used.
