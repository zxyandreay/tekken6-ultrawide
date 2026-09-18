# Research documentation

This directory preserves the technical investigations behind the public releases.

## v1.1.0

[`v1.1.0-auto-aspect-abi.md`](v1.1.0-auto-aspect-abi.md)

Documents the PPSSPP automatic-aspect query work, including the six-argument `sceIoDevctl` ABI issue found during temporary non-PSPDEV testing and the path that produced the validated automatic 3D correction.

## v1.2.0 AutoHUD

[`v1.2.0-autohud.md`](v1.2.0-autohud.md)

**Detailed archive:** [`v1.2.0/README.md`](v1.2.0/README.md)

The detailed reverse-engineering and implementation record for the v1.2.0 battle-HUD work. It covers:

- semantic LEFT/CENTER/RIGHT HUD composition;
- HP shell and HP fill ownership;
- side strips and rank badges;
- round markers and winner glow;
- center-timer ABI;
- character-name anchoring;
- Practice and Gold Rush font/glyph research;
- the `0x0EB0` memory-footprint constraint;
- EXP6 as the fixed-20:9 reference;
- EXP11–EXP14 AutoHUD regressions;
- the EXP14 stale-branch HP-fill root cause;
- EXP15 repair;
- rejected EXP16 self-patching design;
- final EXP17 dynamic HP architecture;
- release validation and source/artifact limitations.

[`v1.2.0-autohud-timeline.md`](v1.2.0-autohud-timeline.md)

Chronological milestone list with the important recovered research commit SHAs.

## Provenance note

The temporary HUD research branches were deleted after v1.2.0 release cleanup. Their commits were still addressable by SHA, allowing the detailed v1.2.0 documentation to be reconstructed from the original notes and commit history.

The current documentation intentionally omits local network addresses, debugger endpoints, device identifiers, and workstation paths.

## Source versus release binaries

The exact device-validated release PRXs are authoritative for the published versions. The readable source tree is not automatically assumed to be byte-identical to every compact hand-integrated research binary.

For v1.2.0 specifically, a future source-derived replacement should reproduce the documented hook semantics, dynamic aspect behavior, `0x0EB0` resident footprint, replacement-texture compatibility, mode-specific HUD behavior, and official-PPSSPP stability before being considered equivalent to the published artifact.


### Recovered detailed v1.2.0 archive

The first post-release summary was intentionally compact and did not preserve enough of the experiment-by-experiment process. The detailed archive under [`v1.2.0/`](v1.2.0/) restores the original subsystem notes plus retained test-build evidence, including the RoundWin, Timer, SideNames, ModeHUD, compact EXP1–EXP6, and AutoHUD EXP11–EXP17 progression.
