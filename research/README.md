# Research documentation

This directory preserves the technical investigations behind the Tekken 6 PPSSPP ultrawide plugin.

The documentation is organized around how the problems were investigated and solved, not around treating a later test build as the project baseline.

## v1.1.0 — automatic 3D aspect correction

See v1.1.0-auto-aspect-abi.md for the runtime aspect-query/plugin work that replaced the fixed 3D CWCheat with automatic PPSSPP aspect detection.

## v1.2.0 — HUD correction / AutoHUD

See v1.2.0-autohud.md for the main end-to-end research narrative.

It starts from the actual preserved baseline: a known-good 3D-only CWCheat with stretched HUD/UI and no known HUD transform.

### Detailed archive

See v1.2.0/README.md for:

- earliest projection/screen-space/native-2D research;
- battle-HUD ownership mapping;
- HP shell/fill research;
- winner-orb and glow work;
- timer ABI findings;
- character-name anchoring;
- Practice/Gold Rush glyph research;
- retained test-build evidence;
- HP AutoHUD packet tracing;
- probe methodology.

## Evidence policy

The research docs distinguish between verified/recovered results from old commits, retained artifacts, or runtime captures; experiment intent where a test package survives but the exact device result does not; and final validated behavior from the release test sweep.

Missing history is not filled with guesses.

## Source versus release binary

The exact device-validated v1.2.0 PRX remains authoritative for the release.

A future source-derived replacement should reproduce the documented hook semantics, dynamic aspect behavior, compact resident footprint, replacement-texture compatibility, mode-specific HUD behavior, and PPSSPP stability before being considered equivalent.

## Privacy

Local network addresses, debugger endpoints, device identifiers, and workstation paths are intentionally omitted.
