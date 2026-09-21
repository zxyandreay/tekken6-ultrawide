# OPT-EXP2S3 accepted optimization checkpoint — 2026-09-21

## Status

Accepted on device.

Build:

```text
Tekken6Ultrawide-OPT-EXP2S3-GlowSlots.prx

SHA-256:
7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

The fixed resident-allocation rule remains unchanged.

## Device result

The OPT-EXP2S3 winner-glow generalization was tested on device after the corrected OPT-EXP2S2 startup-table compression.

Confirmed:

- Tekken 6 starts normally;
- battle HUD appears normally;
- earned round/orb placement is substantially aligned again;
- the transient rotating winner glow/halo now follows the correct newly earned orb;
- the previous residual spin on the wrong orb is gone.

This validates the generalized winner-glow classifier.

## What OPT-EXP2S3 contains

The accepted line consists of three successful optimization/correction steps relative to official v1.2.0.

### 1. OPT-EXP1 — downstream HP consolidation

Validated result:

- the two upstream gauge-owner hooks at `0x0892C1F0` and `0x0892C26C` are no longer installed;
- stock gauge rendering remains intact;
- HP shell/fill ownership is classified at the existing downstream shared-sprite dispatcher;
- the exact v1.2.0 HP shift/scale behavior is reproduced there;
- the fixed one-LOAD `0x0EB0` image remains unchanged in size.

Important accounting rule:

The old upstream wrapper region was reused for the downstream HP handler. It is architectural simplification, not free capacity.

### 2. OPT-EXP2S2 — safe slot installer compression

The original slot patch table contained thirteen 12-byte records:

```text
address       4
expected word 4
kind          4
              --
              12 bytes
```

The `kind` value is redundant because the expected instruction opcode already identifies J versus JAL.

The accepted table is therefore:

```text
address       4
expected word 4
              --
               8 bytes
```

All three startup table walkers use an 8-byte stride:

- validation;
- installation;
- cache invalidation.

The earlier EXP2S startup hang was caused by leaving the cache-invalidation loop at +12. OPT-EXP2S2 corrected that to +8.

The battle-time slot topology remains identical to v1.2.0/OPT-EXP1:

- thirteen original slot hooks;
- original slot wrapper;
- original scope lifetime.

### 3. OPT-EXP2S3 — winner-glow slot generalization

The historical winner-glow hook was validated only against the original first-win P1/P2 X-center families.

The ordinary earned-orb rectangle code already covered a broader set of authored round slots.

Re-analysis of the archived bilateral round-win captures showed that the combination of:

```text
4 vertices
exact 64x64 UV corner pattern
winner-orb Y row
```

was sufficient to isolate the same rotating winner-glow family in the captures.

OPT-EXP2S3 therefore removed only the obsolete first-slot X-family gate.

Preserved:

- vertex-count gate;
- exact UV identity;
- Y-row gate;
- dynamic CENTER transform;
- temporary source-X transform;
- original converter call;
- source-X restoration.

Device validation confirms the halo now follows the correct earned orb.

## Rejected optimization line

Do not reuse these results as available-space evidence:

- OPT-EXP2;
- OPT-EXP2R;
- OPT-EXP2R2.

Those builds attempted runtime slot-route consolidation.

Observed failures included:

- wrong round-win compositing;
- wrong residual halo relationship;
- renderer ABI corruption;
- an unsafe PRX-local trampoline;
- PPSSPP force-close at battle-HUD startup.

The previously quoted 216/236-byte capacity belonged to that rejected architecture and is not part of the accepted byte budget.

## Current accepted baseline

For further optimization work, use OPT-EXP2S3 as the checkpoint.

Do not restart from rejected EXP2/EXP2R/EXP2R2 binaries.

The next proposed target is the two-stage Practice/Gold mode-font implementation, but only after the current internal-space audit is treated as the authoritative capacity record.
