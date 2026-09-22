# Research

This directory contains the **engineering evidence and experiment history** behind the plugin.

For the current accepted architecture, start with [`docs/`](../docs/). Use `research/` when you need to understand how a conclusion was established, inspect rejected approaches, or continue unresolved work.

## Topics

### [Auto aspect](auto-aspect/)

**Status:** COMPLETE / HISTORICAL FOUNDATION

Runtime PPSSPP aspect-query work that replaced fixed manual aspect-ratio selection.

### [AutoHUD](autohud/)

**Status:** ACCEPTED

Fight-HUD ownership, HP, timer, round markers, side labels, mode text, and the development path that produced the dynamic HUD architecture.

### [Renderer optimization](renderer-optimization/)

**Status:** COMPLETE / ACCEPTED THROUGH v1.2.1

Post-v1.2.0 renderer consolidation, winner-glow correction, slot/font optimization, and the accepted EXP4A layout.

## Folder convention

Each topic uses:

```text
README.md       -> current status / reading order
findings/       -> accepted technical conclusions
archive/        -> superseded, rejected, chronological, or historical evidence
```

Historical files are preserved even when their conclusions were later disproved.

## Research tools

Executable probes, builders, and audits live under:

[`tools/research/`](../tools/research/)

This keeps the research tree primarily readable Markdown rather than mixing documentation and utilities.
