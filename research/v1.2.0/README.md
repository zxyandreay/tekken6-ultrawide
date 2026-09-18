# v1.2.0 HUD / AutoHUD research archive

This directory preserves the detailed reverse-engineering record behind Tekken 6 Ultrawide v1.2.0.

The archive combines recovered subsystem notes, retained test-build evidence, exact artifact hashes, and the final validated implementation record.

The intent is to preserve **how the implementation was discovered**, including failed experiments and intermediate hypotheses, rather than documenting only the final AutoHUD equations.

No local network addresses, debugger endpoints, device identifiers, or workstation paths are retained.

## Recommended reading order

1. [`../v1.2.0-autohud.md`](../v1.2.0-autohud.md)  
   End-to-end narrative from 3D-only v1.1.0 through EXP17/v1.2.0.

2. [`hud-research.md`](hud-research.md)  
   Original consolidated fight-HUD reverse-engineering notes: fixed hook sites, HP shell/fill, side strips/ranks, round markers, timer, names, shared top-row text, rejected approaches.

3. [`test-builds.md`](test-builds.md)  
   Artifact-by-artifact experiment record: FrameDump diagnostics, RoundWin v6/v7, Timer v8/v8.1, SideNames v9/v9.1/v9.2, ModeHUD v10/v10.1/v10.2, MemSize A/B, ModeCompact EXP1–EXP6, AutoHUD EXP11–EXP17.

4. [`winner-orb.md`](winner-orb.md)  
   Immediate earned-orb and residual winner-glow investigation.

5. [`center-timer.md`](center-timer.md)  
   Timer ownership and fifth stack-argument ABI regression.

6. [`side-labels.md`](side-labels.md)  
   Character-name anchoring and separation from the batched top battle-mode text.

7. [`mode-hud.md`](mode-hud.md)  
   Practice infinity, Practice stats, Gold Rush labels, and EXP2→EXP6 dual-stage font solution.

8. [`checkpoint-exp6.md`](checkpoint-exp6.md)  
   The fixed-20:9 visual/behavioral reference frozen before AutoHUD generalization.

9. [`hp-fill-auto-aspect.md`](hp-fill-auto-aspect.md)  
   EXP11–EXP17 HP-fill investigation, MIPS call pairing, packet tracing, stale rejection-branch root cause, EXP15 repair, EXP16 failure, EXP17 solution.

10. [`tools-and-probes.md`](tools-and-probes.md)  
    Frame-dump, glyph, timer, side-label, HP-path, downstream renderer, hook verification, and candidate-generator methodology.


## Major phases

### Phase A — establish the 3D automatic-aspect foundation

v1.1.0 supplied the PPSSPP runtime aspect query and projection correction.

### Phase B — reverse-engineer battle HUD ownership at fixed 20:9

The research deliberately solved one visual family at a time:

```text
HP shell
HP fill
side strips
rank badges
round markers
winner glow
center timer
character names
Practice infinity
Practice stats
Gold Rush labels
```

This produced EXP6, the fixed-20:9 reference.

### Phase C — discover the compact-memory constraint

Larger PRX mappings caused custom replacement font/text regressions.

A controlled v9.2 A/B changed only `PT_LOAD.p_memsz` from `0x0EB0` to `0x12D0` and reproduced the regression.

From then on the compact one-LOAD `0x0EB0` footprint became a functional compatibility requirement.

### Phase D — generalize EXP6 into AutoHUD

The fixed transforms were converted into aspect-derived LEFT/CENTER/RIGHT equations.

Most dynamic paths worked, but HP fill disappeared.

### Phase E — follow missing HP downstream

EXP14 restored the entire working EXP6 gauge hook yet HP was still absent.

Runtime comparison showed the gauge and renderer inputs were correct.

Packet tracing found a stale rejection-branch target in a shortened side-strip hook. HP packets rejected through that path and never reached stock sprite submission.

EXP15 restored the common forwarding jump.

### Phase F — dynamic HP without regressions

EXP16 tried startup self-patching but reused initializer instructions still required by font/text paths.

EXP17 preserved the initializer and changed only HP coefficient transport.

The all-mode regression sweep passed and EXP17 became the v1.2.0 release PRX.

## Authoritative release artifact

```text
v1.2.0 PRX SHA-256:
311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75

file size:
5626 bytes

PT_LOAD:
p_filesz = 0x0EB0
p_memsz  = 0x0EB0
```

## Archive boundary

Some raw local debugger captures were never committed and are not preserved here. The measurements, addresses, control-flow findings, experiment purposes, artifact hashes, device outcomes, and architectural conclusions needed to understand the implementation are preserved.
