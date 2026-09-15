# Side-owned battle text labels

## Status

Open research target after the center round timer was solved.

Screenshots from Arcade Battle and Story Battle show that several player-facing text labels remain at their original 16:9 horizontal positions even though the HP shells/fills, rank badges, side strips/lightning, round markers, winner glow, and center countdown are already corrected.

Visible unresolved examples:

```text
ARCADE BATTLE
STORY BATTLE
GHOST BATTLE
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

Y placement and vertical scale remain unchanged.

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

This establishes string identity but does not by itself establish the draw owner.

A separate mode-text table is present around `0x08BE5918`; `GHOST BATTLE` is referenced from the entry at `0x08BE5930` and points to `0x08BB9D60`. This supports treating battle-mode labels as a separate text subsystem rather than part of the rank/strip sprite path.

## Stable frame-capture findings

A read-only two-frame capture was taken in Arcade, Story, and Ghost Battle with the integrated timer build. The persistent top-HUD draws separate into two useful families.

### Character-name rectangles

Character-name art is already flowing through the slot-`0xEF` rectangle compositor. The current hook uniformly de-stretches these rectangles, but because only y=10 is classified as side-owned, the y=28 name family falls through to the CENTER transform.

Observed post-hook geometry:

```text
Story P1 KAZUYA: x=57..108,  y=28..44, 51x16
Story P2 LARS:   x=381..432, y=28..44, 51x16
Arcade P2 ASUKA: x=343..445, y=28..44, 102x16
```

The widths are exactly the current 0.8-scaled forms of authored 64/128-pixel rectangles. Inverting the current integer CENTER transform recovers approximate authored positions:

```text
KAZUYA: x~10,  width 64
LARS:   x~415, width 64
ASUKA:  x~368, width 128
```

This proves the name art does not need a new font/text renderer hook. It only needs a narrower classification inside the rectangle path:

```text
y=28
height=16
authored width=64 or 128
P1 / authored X < 240  -> LEFT
P2 / authored X > 240  -> RIGHT
```

Expected fixed-20:9 examples:

```text
KAZUYA -> about 8..59
LARS   -> about 428..479
ASUKA  -> about 390..492
```

The existing 0.8 width correction is retained; only the anchor offset changes.

### Top-row stage/time and battle-mode text

Arcade, Story, and Ghost all contain a stable top-row `0x80011E` glyph batch using the same texture/CLUT and y≈1..14. The batch spans almost the entire logical width:

```text
Arcade: x=12..467, count=52
Story:  x=12..467, count=50
Ghost:  x=11..467, count=52
```

This is consistent with one combined font batch containing the left `STAGE/BATTLE + elapsed time` text and the right `ARCADE/STORY/GHOST BATTLE` label. Moving the whole draw would be incorrect. The eventual fix must classify glyphs/vertices inside that batch by authored side so left text receives LEFT and the mode header receives RIGHT.

Ghost also has a second `0x80011E` batch around y=32..46, consistent with additional player/opponent text. That path should be investigated after the rectangle-based character-name correction is validated.

## Research direction

Do not reopen the solved rank/strip, HP, timer, round-marker, or winner-orb subsystems.

Preferred proof order now:

1. validate the narrow y=28 character-name LEFT/RIGHT rectangle correction in Story and Arcade;
2. regression-check timer, HP, ranks, side effects, and round markers;
3. isolate the shared top-row `0x80011E` font builder;
4. apply per-glyph LEFT/RIGHT anchoring to the top-row batch without moving center or menu text;
5. validate Arcade/Story/Ghost mode labels and any Ghost-specific player/opponent text.

Avoid a global font/text transform because result screens, pause UI, and front-end menus require different composition rules.
