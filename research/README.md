# Research documentation

This directory preserves the technical work behind the released Tekken 6 PPSSPP ultrawide plugin.

The goal is to document **how each problem was reverse-engineered and solved**: ownership discovery, controlled experiments, failed hypotheses, implementation constraints, and the final validated design.

## v1.1.0 — automatic 3D aspect correction

[`v1.1.0-auto-aspect-abi.md`](v1.1.0-auto-aspect-abi.md)

Covers the PPSSPP runtime-aspect query, the six-argument `sceIoDevctl` ABI issue encountered during development, and the automatic 3D projection path that became the foundation for AutoHUD.

## v1.2.0 — HUD correction / AutoHUD

[`v1.2.0-autohud.md`](v1.2.0-autohud.md)

The end-to-end engineering narrative. It explains:

- why the 3D aspect fix could not correct screen-space HUD geometry;
- how LEFT/CENTER/RIGHT semantic anchoring was derived;
- how HP shell and fill ownership were separated;
- how side strips, rank badges, round markers, winner glow, timer, and character names were identified;
- how Practice and Gold Rush text required separate glyph-path work;
- why the compact `0x0EB0` module footprint became a functional requirement;
- how EXP6 became the fixed-20:9 visual reference;
- why the first AutoHUD builds lost HP fill;
- how downstream packet tracing found the stale rejection-branch bug;
- why EXP16 regressed text;
- and why EXP17 became the final v1.2.0 architecture.

### Detailed v1.2.0 archive

[`v1.2.0/README.md`](v1.2.0/README.md)

Use this when you need the deeper subsystem notes, test-build evidence, HP packet-tracing investigation, or probe methodology.

The archive preserves the useful engineering record rather than every temporary branch or raw debugger capture.

## Source versus release binaries

The exact device-validated release PRXs are authoritative for the published versions.

For v1.2.0, a future clean source-derived replacement should reproduce the documented hook semantics, dynamic aspect behavior, `0x0EB0` resident footprint, replacement-texture compatibility, mode-specific HUD behavior, and PPSSPP stability before being considered equivalent to the published artifact.

## Privacy

Research documentation intentionally omits local network addresses, debugger endpoints, device identifiers, and workstation paths.
