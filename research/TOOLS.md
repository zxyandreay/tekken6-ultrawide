# Research tools

Only tools that remain useful after the validated HUD findings are retained here. Raw captures and one-off experiments belong in `.local-research/`, not in Git.

## `ppdmp_hud_diff.py`

Generic PPSSPP frame-dump parser/differ used to enumerate draw calls, decode vertices, compare draw groups, and correlate GPU geometry.

It is the common parser used by the focused HUD analyzers.

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

## `ppsspp_side_labels_capture.mjs`

Read-only capture for the unresolved side-owned battle text. It records two stable active-fight frames each from Arcade, Story, and Ghost Battle without breakpoints or memory writes.

Usage:

```text
node research/tools/ppsspp_side_labels_capture.mjs <host:port>
```

Captures are written under:

```text
.local-research/side-labels/
```

## `ppdmp_side_labels_analysis.py`

Filters the side-label captures to stable top-HUD THROUGH draws and groups them into left, center, and right regions. The goal is to isolate character-name and battle-mode glyph batches without globally transforming text.

It is run automatically by `ppsspp_side_labels_capture.mjs`, or manually with:

```text
python research/tools/ppdmp_side_labels_analysis.py .local-research/side-labels
```

The report is written to `.local-research/side-labels/analysis.json`.

## `verify_hud_hook_sites.py`

Checks every fixed hook address against the expected stock ULUS10466 instruction in a local EBOOT.

Usage:

```text
python research/tools/verify_hud_hook_sites.py <ULUS10466_EBOOT.BIN>
```

A mismatch means the fixed-address research build should not be trusted for that executable.
