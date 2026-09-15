# Tekken 6 ultrawide HUD research

This directory documents reverse engineering of the Tekken 6 USA (`ULUS10466`) fight HUD on PPSSPP. The branch is based on the published v1.1.0 automatic-aspect plugin and keeps that 3D projection path intact while experimentally recomposing selected 2D battle-HUD elements for a fixed 20:9 target.

## Current validated state

The following behavior has been validated on-device:

- automatic 3D ultrawide projection from v1.1.0 remains intact;
- long P1/P2 HP shells span outward while preserving the protected center region;
- both HP fill layers align with the remapped shells at full and partial health;
- rank badges and under-bar/lightning strips use side-aware horizontal anchoring;
- persistent round markers and newly earned round orbs use the center transform;
- the transient winner-orb glow is corrected independently of the ordinary orb rectangle;
- P1 and P2 first-win orb placement and winner glow are both correct in the integrated plugin.

The winner-orb subsystem is considered solved. Timer/front-end/character-select work is not part of that conclusion.

## Documentation

- [`HUD_RESEARCH.md`](HUD_RESEARCH.md) — consolidated renderer ownership, geometry, hook sites, validated transforms, and rejected approaches.
- [`WINNER_ORB.md`](WINNER_ORB.md) — focused record of the round-win orb/glow investigation and final fix.
- [`TOOLS.md`](TOOLS.md) — retained analysis/capture utilities and their intended use.
- [`v1.1.0-auto-aspect-abi.md`](v1.1.0-auto-aspect-abi.md) — earlier automatic-aspect ABI investigation retained from v1.1.0 development.

## Research rules

- Target `ULUS10466` only unless another executable is separately mapped.
- Validate fixed hook instructions before patching them.
- Prefer narrow owner/shape predicates over global sprite, projection, or THROUGH-mode transforms.
- Do not hard-code session-local heap, vertex-buffer, GE-list, debugger, or network addresses.
- Keep EBOOTs, frame dumps, memory snapshots, logs, test PRXs, debugger endpoints, and other local material under `.local-research/`; that directory is intentionally ignored.
- Preserve Y coordinates, UVs, colors, alpha, animation lifetime, and rotation unless a specific finding proves they require correction.

## Build and static verification

The research plugin requires PSPDEV:

```text
make -C plugin clean
make -C plugin
```

Before trusting a fixed-address build, verify the hook sites against the local ULUS10466 EBOOT:

```text
python research/tools/verify_hud_hook_sites.py <ULUS10466_EBOOT.BIN>
```

The current HUD correction is deliberately limited to the fixed 20:9 proof range (`~2.20..2.24`). Dynamic HUD coefficients should only be introduced after the remaining battle-HUD ownership is stable.
