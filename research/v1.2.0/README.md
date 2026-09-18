# v1.2.0 HUD / AutoHUD research archive

This directory contains the detailed evidence behind the v1.2.0 HUD correction.

## Recommended reading

1. origin-and-early-research.md — actual preserved starting point: known-good 3D-only CWCheat, projection hypotheses, failed orthographic tests, Warriors-style candidate research, plugin/JIT verification, descriptor/native-2D work, and the transition to direct battle-HUD ownership mapping.

2. ../v1.2.0-autohud.md — end-to-end narrative from that starting point through the final AutoHUD implementation.

3. hud-research.md — consolidated battle-HUD ownership notes.

4. test-builds.md — retained experiment artifacts and their checksums, purposes, and recoverable outcomes.

5. winner-orb.md — immediate round marker and winner-glow reverse engineering.

6. center-timer.md — timer ownership and stack-argument ABI failure.

7. side-labels.md — character-name anchoring and separation from other battle text.

8. mode-hud.md — Practice infinity, Practice stats and Gold Rush text research.

9. hp-fill-auto-aspect.md — automatic-aspect HP regression, packet tracing, stale rejection-branch root cause, and final dynamic HP integration.

10. tools-and-probes.md — diagnostic methodology used to isolate ownership and compare working/broken paths.

## Evidence boundary

Some raw local debugger captures were never committed and cannot be reconstructed.

Where only a test package survives, the archive records the experiment purpose without inventing a result.

Where old commits or later notes explicitly preserve a result, that result is documented.

## Release artifact

v1.2.0 PRX SHA-256: 311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75

file size: 5626 bytes
PT_LOAD p_filesz = 0x0EB0
PT_LOAD p_memsz  = 0x0EB0
