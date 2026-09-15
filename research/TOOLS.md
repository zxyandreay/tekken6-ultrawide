# Research tools

Only tools that remain useful after the validated HUD findings are retained here. Raw captures and one-off experiments belong in `.local-research/`, not in Git.

## `ppdmp_hud_diff.py`

Generic PPSSPP frame-dump parser/differ used to enumerate draw calls, decode vertices, compare draw groups, and correlate GPU geometry.

It is the common parser used by the round-win analyzer.

## `ppsspp_round_win_capture.mjs`

Read-only three-phase round-win capture utility for PPSSPP's remote debugger.

It records, for a controlled P1 or P2 win:

```text
2 pre-KO frames
18 immediate win/burst frames
3 stable next-round frames
```

No breakpoints are installed and no game memory is written.

Usage:

```text
node research/tools/ppsspp_round_win_capture.mjs <host:port> <p1|p2>
```

Captures are written under:

```text
.local-research/round-win/<side>/
```

The debugger endpoint is a runtime argument/environment value and is not serialized into reports.

## `ppdmp_round_win_analysis.py`

Phase analyzer for the capture set above. It intentionally inventories a broad top-HUD THROUGH window rather than filtering by the already-known winner-orb texture hashes.

Usage:

```text
python research/tools/ppdmp_round_win_analysis.py .local-research/round-win/p1 --side p1
python research/tools/ppdmp_round_win_analysis.py .local-research/round-win/p2 --side p2
```

It writes `analysis.json` alongside the captures and groups identities across pre-KO, burst, and next-round phases.

## `verify_hud_hook_sites.py`

Checks every fixed hook address against the expected stock ULUS10466 instruction in a local EBOOT.

Usage:

```text
python research/tools/verify_hud_hook_sites.py <ULUS10466_EBOOT.BIN>
```

A mismatch means the fixed-address research build should not be trusted for that executable.
