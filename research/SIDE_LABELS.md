# Side-owned battle text labels

## Status

Open research target after the center round timer was solved.

Screenshots from Arcade Battle and Story Battle show that several player-facing text labels remain at their original 16:9 horizontal positions even though the HP shells/fills, rank badges, side strips/lightning, round markers, winner glow, and center countdown are already corrected.

Visible unresolved examples:

```text
ARCADE BATTLE
STORY BATTLE
character names such as KAZUYA, ASUKA, LARS
```

These should not be treated as center-safe-area menu text. They are persistent fight-HUD labels with semantic side ownership:

```text
P1 character/name text -> LEFT
P2 character/name text -> RIGHT
battle-mode label       -> RIGHT
```

For the fixed 20:9 research target the intended horizontal transforms are:

```text
LEFT:  x' = 0.8*x
RIGHT: x' = 0.8*x + 96
```

Any glyph/sprite horizontal scale must also be reduced by `0.8` if the renderer is currently stretched by the widened PPSSPP viewport. Y placement and vertical scale should remain unchanged unless later evidence proves otherwise.

## Static string evidence

ULUS10466 contains a character-name pointer table beginning at:

```text
0x08BE52C0
```

Helper `0x08974578` indexes this table by character ID (`id * 4`) for IDs below `0x2B` and returns the corresponding string pointer. Examples observed in the executable include:

```text
KAZUYA -> 0x08BB0B6C
ASUKA  -> 0x08BB0BBC
LARS   -> 0x08BB0C48
```

This establishes string identity but does not yet establish the draw owner.

A separate mode-text table is present around `0x08BE5918`; `GHOST BATTLE` is referenced from the entry at `0x08BE5930` and points to `0x08BB9D60`. This supports treating battle-mode labels as a separate text subsystem rather than part of the rank/strip sprite path.

## Research direction

Do not reopen the solved rank/strip or y=10 panel geometry hooks. The next task is to identify the renderer/callsite that consumes these strings during active battle and then gate a side-aware horizontal transform at the narrowest stable owner.

Preferred proof order:

1. capture one stable Arcade/Story fight frame with the current integrated plugin;
2. identify the character-name and mode-label draw records in the top HUD;
3. correlate those records with CPU-side text submissions;
4. test a narrow LEFT/RIGHT correction without changing other text or menus;
5. validate both P1 and P2 names plus Arcade/Story/Ghost mode labels.

Avoid a global font/text transform because result screens, pause UI, and front-end menus require different composition rules.
