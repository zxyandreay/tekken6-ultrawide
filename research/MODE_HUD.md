# Practice and Gold Rush HUD

## Status

Open mode-specific HUD research target after the persistent normal battle HUD, center timer, and character-name anchoring were validated.

The normal Arcade/Story/Ghost battle-HUD fixes should remain frozen unless a regression is demonstrated. Practice and Gold Rush introduce additional HUD families that require separate ownership/geometry work.

## Practice observations

Device screenshots with the current integrated HUD build show two distinct issues.

### Infinite-time indicator

The Practice infinite-time (`∞`) indicator is no longer centered after the normal round-timer correction. It is displaced left into/behind the P1 health-bar region.

The normal round countdown is rendered through two dedicated calls at:

```text
0x08929AF8
0x08929B44
```

The plugin currently wraps both calls unconditionally and temporarily enables the centered rectangle scope. Normal two-digit timers are device-validated with that rule, but Practice demonstrates that an alternate timer/status presentation shares part of this path and cannot be assumed to have identical geometry semantics.

A stable Practice capture isolates one mode-only `0x80011A` rectangle at:

```text
post-hook bbox: x=166..217, y=6..38
post-hook size: 51x32
texture: 0f87368a50b3...
```

Its 51-pixel width is exactly the fixed-20:9 0.8 scaling of an authored 64-pixel rectangle. Inverting the current CENTER mapping recovers authored X around `147`. Applying the RIGHT-style horizontal offset to that authored geometry would yield approximately `214..265`, centering the 51-pixel result around x=240. This is a strong candidate for the Practice infinite-time correction, but it should remain a test hypothesis until the surrounding mode-specific glyph geometry is expanded and checked.

Do not remove or weaken the validated normal timer correction globally. The final fix should recognize the Practice-only geometry narrowly.

### Practice statistics panel

The left-side Practice HITS / DAMAGE / combo/readout family appears to have correct LEFT ownership/placement but remains horizontally stretched.

Desired behavior:

```text
anchor: LEFT
horizontal scale: 0.8 at fixed 20:9
vertical placement/scale: preserve
```

The first-stage capture identifies a stable `0x80011E` batched font draw using texture `8b127e798779...`:

```text
Practice idle: count=38, bbox x=3..463, y=2..116
Practice hit:  count=78, bbox x=3..463, y=2..139
```

The hit state adds 40 vertices, i.e. 20 rectangle-glyph pairs, strongly indicating that the dynamic HITS / DAMAGE / combo text is appended into the same batched font submission as other Practice HUD text. The parent draw cannot be transformed as a whole because it spans both sides of the HUD. The per-glyph rectangles must be expanded and classified by authored side/region.

Static string resources in ULUS10466 include Practice formatting/text near the 0x08B9B2xx/0x08B9B3xx range, including `DAMAGE` and `HIT COMBO` format strings. String identity alone is not sufficient to patch the renderer; stable draw ownership must be established first.

## Gold Rush observations

The Gold Rush right-side score/gold HUD appears correctly RIGHT-owned but horizontally stretched.

Desired behavior:

```text
anchor: RIGHT
horizontal scale: 0.8 at fixed 20:9
vertical placement/scale: preserve
```

The first-stage capture shows several Gold-Rush-only THROUGH submissions. Two full-screen multi-rectangle parents (`0x80011A` and `0x80011C`, each with count 16 and 512x272 aggregate bounds) are especially important because their aggregate bounding boxes hide disconnected child rectangles. These are strong candidates for the right-side REWARD / gold / attack-variation family and require per-rectangle expansion before a safe predicate can be written.

The ordinary right HP shell and known character/rank rectangles are also present and should remain frozen; they are not the Gold Rush target.

Do not apply a global right-side text transform because ordinary battle labels and menu/result screens have separate composition rules.

## Capture results and second-stage analysis

Initial read-only capture completed successfully for:

```text
practice-idle
practice-hit
goldrush
```

Use the second-stage analyzer on the existing captures; no recapture is required:

```text
python research/tools/ppdmp_mode_hud_glyphs.py .local-research/mode-hud
```

It expands multi-rectangle THROUGH draws into individual rectangle/glyph pairs and writes:

```text
.local-research/mode-hud/glyph-analysis.json
```

This is required before patching the Practice stats or Gold Rush score family because their parent draw bounds combine multiple unrelated screen regions.

## Safety rules

- Do not reopen the validated normal countdown geometry to solve Practice.
- Do not globally transform font/sprite renderers.
- Prefer a mode/owner/shape predicate that affects only the target family.
- Preserve PPSSPP texture replacement behavior and emulator controls; test PRXs must retain the clean validated module layout.
