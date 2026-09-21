# OPT-EXP3B halo observation — corrected interpretation — 2026-09-21

## Corrected interpretation

OPT-EXP3B displayed the spinning winner/earned-round halo on the wrong orb.

Initially this was attributed to EXP3B compaction because EXP3A had been believed to have correct halo behavior.

That premise was later disproven.

The user retested:

- OPT-EXP2S3;
- OPT-EXP3A;

and confirmed that both already show the same wrong-orb halo.

Therefore there is **no evidence that EXP3B introduced the halo defect**.

The earlier R1 causal split between:

1. helper relocation;
2. zeroing 0x0D40..0x0D57;

is invalid as a diagnosis of the halo bug because the baseline was already failing.

## What remains useful from the EXP3B investigation

The direct-xref audit is still useful for space analysis, but winner-glow correctness must not be inferred from it.

The glow subsystem is now treated as an independent unresolved renderer issue.

The current investigation compares:

- historical RoundWin v7, whose dedicated test note claimed a device-proven fixed-20:9 glow;
- released v1.2.0 / OPT descendants, which use a rewritten dynamic glow transform;
- an exaggerated current-hook diagnostic to prove whether the visible residual spin is actually owned by the current converter hook.

## Optimization rule

Do not perform additional winner-glow code reclamation or compaction until the renderer owner is re-proven dynamically.

No GitHub Actions are used.
