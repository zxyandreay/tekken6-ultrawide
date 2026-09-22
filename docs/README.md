# Documentation

This directory contains the **current, reader-facing technical documentation** for the plugin.

Use `docs/` when you want to understand how the accepted system works now. Use [`research/`](../research/) when you want the experiment history, evidence, rejected approaches, and unresolved questions.

## Read this first

### Architecture

- [AutoHUD architecture](architecture/autohud.md) — dynamic aspect correction and semantic HUD anchoring.
- [Renderer model](architecture/renderer-model.md) — known renderer families, ownership model, and frozen subsystems.
- [PRX layout and constraints](architecture/prx-layout.md) — authoritative runtime artifact, module footprint, and accepted internal headroom.

### Development

- [Research methodology](development/research-methodology.md) — how renderer hypotheses are tested and accepted.
- [PPSSPP debugging](development/ppsspp-debugging.md) — frame dumps, remote debugger controls, and capture discipline.
- [Binary patching rules](development/binary-patching-rules.md) — ABI, delay-slot, relocation, cache, and deterministic-builder rules.

### History

- [How the original CWCheat was made](history/how-the-cwcheat-was-made.md).

## Documentation policy

Canonical docs describe the **accepted current model**. They should not become chronological experiment logs.

When a new research line is accepted:

1. update the relevant canonical document;
2. keep the supporting experiment trail under `research/`;
3. keep old rejected/superseded experiments in `archive/` rather than deleting them.
