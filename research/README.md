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

## v1.2.1 — renderer maintenance and optimization

See `renderer-optimization/README.md` for the maintenance line that followed v1.2.0.

That research records:

- downstream HP consolidation;
- slot-table and slot-scope wrapper compaction;
- Practice/Gold one-hook text architecture;
- winner-glow UV predicate root cause;
- the historical first-win-only validation gap;
- first and later winner-glow slot correction;
- accepted EXP4A checkpoint and 136-byte detached hard-free audit;
- deterministic builders and PPSSPP probes used during the work.

The exact device-validated EXP4A PRX is the authoritative v1.2.1 runtime binary.

## Research method

Record only what is established by static analysis, a controlled test, a runtime capture, or a validated build. Mark an unrecorded result as `Result: not recorded` rather than inferring it.

## Implementation status

The exact device-validated release PRX remains authoritative.

A future source-derived replacement should reproduce the documented hook semantics, dynamic aspect behavior, compact resident footprint, replacement-texture compatibility, mode-specific HUD behavior, winner-glow slot coverage, fast-forward behavior, and PPSSPP stability before being considered equivalent.
