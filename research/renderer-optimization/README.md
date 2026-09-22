# Renderer Optimization Research

**Status:** COMPLETE / ACCEPTED THROUGH v1.2.1

This topic records the post-v1.2.0 renderer consolidation and maintenance work that produced the official v1.2.1 / OPT-EXP4A baseline.

Authoritative runtime:

```text
PRX SHA-256:
6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8

one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Accepted findings

- [Final EXP4A architecture](findings/final-architecture.md)
- [Accepted internal-space audit](findings/space-audit.md)
- [Winner-glow final resolution](findings/winner-glow.md)
- [Stock renderer census](findings/renderer-census.md)
- [HP downstream A/B evidence](findings/hp-downstream.md)

## Archive

[`archive/`](archive/) contains the EXP1–EXP4 development trail, rejected candidates, corrected assumptions, winner-glow diagnostics, and release-readiness notes.

The archive is intentionally retained because several failures established important ABI, layout, and ownership constraints.

## Tools

Current research utilities are indexed under [`tools/research/`](../../tools/research/).
