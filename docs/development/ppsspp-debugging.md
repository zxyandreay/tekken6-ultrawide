# PPSSPP Debugging Guide

**Status:** CURRENT

## Transport first

Before interpreting any probe failure:

- verify TCP/WebSocket reachability;
- verify PPSSPP version;
- verify game ID `ULUS10466`;
- verify CPU state;
- verify whether the plugin module should be present.

A timeout is not a rendering result.

## Stock control

For ownership discovery:

- disable the plugin;
- disable relevant cheats;
- restart the game;
- verify the plugin module is absent;
- verify expected stock instructions.

PPSSPP JIT/emuhack replacements can affect raw instruction reads. Use instruction-aware/JIT-aware reads or reads with replacements disabled when validating stock code.

## Capture methods

Use frame-dump A/B first when possible:

- target absent;
- target visible;
- diff primitive/texture/UV/geometry/draw order.

Then use narrow execution breakpoints to capture:

- PC/RA/SP/backtrace;
- GPR/FPU inputs;
- stack arguments;
- resource/descriptor pointers;
- authored geometry;
- neighboring non-target draws.

## Breakpoint hygiene

- cap samples on hot renderers;
- remove breakpoints on success/failure/timeout;
- resume the CPU after capture;
- record raw output before the next state;
- pair caller/renderer samples with RA/SP/thread context.

Reusable probes live under [`tools/research/probes/`](../../tools/research/probes/).
