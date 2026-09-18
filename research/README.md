# Research documentation

Technical notes for the Tekken 6 PPSSPP ultrawide plugin.

The files are organized around the engineering process: initial state, hypothesis, test, observation, conclusion, and implementation.

## v1.1.0 — automatic 3D aspect correction

See `v1.1.0-auto-aspect-abi.md` for the runtime aspect-query work that replaced the fixed 3D CWCheat with automatic PPSSPP aspect detection.

## v1.2.0 — HUD correction / AutoHUD

See `v1.2.0-autohud.md` for the end-to-end HUD-correction research.

The work starts from a known-good 3D-only 20:9 patch with stretched HUD/UI and no identified HUD transform, then follows the projection, screen-space, compositor, sprite, text, and packet paths that led to AutoHUD.

### Detailed notes

See `v1.2.0/README.md` for:

- projection, screen-space, and native-2D experiments;
- battle-HUD ownership mapping;
- HP shell/fill research;
- winner-orb and glow work;
- timer ABI findings;
- character-name anchoring;
- Practice/Gold Rush glyph research;
- test-build records;
- HP AutoHUD packet tracing;
- probe methodology.

## Documentation convention

Each experiment records only what was established by static analysis, a controlled test, a runtime capture, or a validated build. If a test result was not recorded, it is marked as such rather than inferred.

## Source versus release binary

The exact device-validated v1.2.0 PRX is authoritative for the release.

A future source-derived replacement should reproduce the documented hook semantics, dynamic aspect behavior, compact resident footprint, replacement-texture compatibility, mode-specific HUD behavior, and PPSSPP stability before being considered equivalent.
