# Research Methodology

**Status:** CURRENT

The project uses small, falsifiable experiments rather than broad renderer rewrites.

## Standard sequence

1. Reproduce the visual problem.
2. Capture a stock/control state.
3. Identify the final draw family with frame-dump or runtime evidence.
4. Trace that draw back to a CPU owner.
5. Record ABI, delay slot, stack arguments, and surviving semantic state.
6. Design the narrowest possible predicate.
7. Change one architectural variable per experiment.
8. Build deterministically from an exact parent hash.
9. Test on device.
10. Record the result as accepted, rejected, superseded, or not recorded.

## Evidence classes

Prefer, in order:

- exact binary/static evidence;
- controlled runtime capture;
- frame-dump A/B;
- device behavior.

A visual movement alone is not proof that the correct renderer was hooked.

## Status vocabulary

Use:

```text
CURRENT / ACCEPTED
ACTIVE RESEARCH
SUPERSEDED
REJECTED
HISTORICAL
RESULT NOT RECORDED
```

Never let an old "fixed" claim silently outrank a later contradictory device test.

## Regression principle

A new fix is accepted only after both its target state and the existing baseline are checked.

The historical winner-glow first-win-only validation is the reference lesson: one successful state does not prove the entire family.
