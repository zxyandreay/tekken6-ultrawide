# OPT-EXP2S3 optimization checkpoint — 2026-09-21

## Corrected status

Accepted for the startup/table-compression and general HUD behavior, but **NOT accepted as a winner-glow fix**.

Build:

```text
Tekken6Ultrawide-OPT-EXP2S3-GlowSlots.prx

SHA-256:
7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Device-result correction

An earlier test report stated that the transient rotating winner glow/halo followed the correct newly earned orb.

That report was later rechecked and withdrawn.

Current verified result:

- Tekken 6 starts normally;
- battle HUD appears normally;
- earned-round/orb rectangle placement is substantially aligned;
- the transient rotating winner glow/halo is still on the wrong orb.

Therefore the EXP2S3 X-gate generalization did **not** solve the winner-glow problem.

Do not cite EXP2S3 as a halo-correct checkpoint.

## What remains accepted

### OPT-EXP1 — downstream HP consolidation

Validated:

- two upstream gauge-owner hooks are no longer installed;
- stock gauge rendering remains intact;
- HP transform is handled at the existing downstream shared-sprite path;
- fixed one-LOAD 0x0EB0 image remains unchanged in size.

### OPT-EXP2S2 — slot installer compression

Validated after correcting all three table walkers to +8-byte stride.

The battle-time slot topology remains unchanged from the known-good release architecture.

### OPT-EXP2S3 — glow classifier experiment

EXP2S3 removed the historical first-slot-only X gate while preserving:

- 4-vertex requirement;
- exact 64x64 UV pattern;
- winner-row Y gate;
- dynamic CENTER transform;
- source-X save/restore;
- original converter call.

The experiment did not visibly solve the residual spinning-halo placement.

It remains useful as evidence that the first-slot X gate was not the sole cause.

## Important historical correction

RoundWin v7 and released v1.2.0 do **not** contain the same winner-glow implementation.

RoundWin v7 used a direct fixed-20:9 transform:

```text
x' = 0.8*x + 48
```

Later AutoHUD work rewrote that path to load dynamic scale/center values from the shared parameter block.

Therefore previous wording that the v7 winner-glow fix simply carried forward unchanged into v1.2.0 was inaccurate.

## Baseline rule

Use OPT-EXP2S3 only as a stable optimization baseline for startup/table and general HUD behavior.

Winner glow must be revalidated independently.

No GitHub Actions are used.
