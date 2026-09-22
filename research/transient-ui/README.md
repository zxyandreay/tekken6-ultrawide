# Transient UI / Safe-Area Research

**Status:** ACTIVE RESEARCH / PREPARATION

This topic is reserved for extending AutoHUD beyond the solved gameplay HUD while preserving the official v1.2.1 / OPT-EXP4A baseline.

The branch is based on the reorganized documentation architecture from:

```text
main commit:
d50cd5f19053a2f0aeda7f2970619b984aebad8f
```

## Authoritative runtime baseline

```text
Tekken6Ultrawide.prx
v1.2.1 / OPT-EXP4A

SHA-256:
6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8

file size: 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

Accepted detached module headroom:

```text
0x0604..0x0647   72 bytes
0x0C00..0x0C3F   64 bytes
-------------------------
total            136 bytes
```

## Intended targets

### CENTER safe-area

- `PERFECT`
- `YOU WIN`
- `YOU LOSE`
- `CONTINUE?` and countdown
- post-win/result composition: bonus rows, EXIT controls, directional prompt, and cards

### LEFT-owned

- `Promotion Chance`

The top-row `ARCADE/STORY/GHOST BATTLE` label remains a separate glyph-ownership problem unless future evidence proves a shared owner.

## Reading order

1. [Canonical AutoHUD architecture](../../docs/architecture/autohud.md)
2. [Renderer model](../../docs/architecture/renderer-model.md)
3. [PRX constraints](../../docs/architecture/prx-layout.md)
4. [Research methodology](../../docs/development/research-methodology.md)
5. [Renderer / ownership hypotheses](HYPOTHESES.md)
6. [Handoff](HANDOFF.md)
7. [Operator / Analyst workflow](OPERATOR_ANALYST_WORKFLOW.md)
8. [Probe workflow](PROBE_WORKFLOW.md)
9. [Current findings](findings/)
10. [Experiment archive](archive/)

Relevant accepted evidence:

- [AutoHUD findings](../autohud/)
- [Renderer optimization findings](../renderer-optimization/findings/)
- [Winner-glow resolution](../renderer-optimization/findings/winner-glow.md)
- [Renderer census](../renderer-optimization/findings/renderer-census.md)
- [Accepted EXP4A architecture](../renderer-optimization/findings/final-architecture.md)
- [Accepted space audit](../renderer-optimization/findings/space-audit.md)

## Branch policy

- Keep discovery/read-only probes separate from implementation.
- One renderer hypothesis per experiment.
- One user-visible correction family per candidate whenever possible.
- Keep exact rollback to official v1.2.1.
- Preserve the one-PT_LOAD `0x0EB0` footprint.
- Do not reopen solved HUD families during unrelated transient-UI work.
- Promote a conclusion to `findings/` only after device validation.
- Move rejected/superseded experiment notes into `archive/`; do not delete useful evidence.
