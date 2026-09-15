# Side-owned battle text labels

## Status

Character-name anchoring is solved and device-validated on ULUS10466 at fixed 20:9.

The remaining open work in this subsystem is the shared top-row text batch containing the left `STAGE/BATTLE + elapsed time` text and the right `ARCADE/STORY/GHOST BATTLE` mode label.

Validated side ownership is:

```text
P1 character-name art -> LEFT
P2 character-name art -> RIGHT
battle-mode label      -> RIGHT   (not yet implemented)
```

At 20:9:

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

Helper `0x08974578` indexes the table by character ID (`id * 4`) for IDs below `0x2B`. Examples observed in the executable include:

```text
KAZUYA -> 0x08BB0B6C
ASUKA  -> 0x08BB0BBC
LARS   -> 0x08BB0C48
```

A separate mode-text table is present around `0x08BE5918`; the `GHOST BATTLE` entry at `0x08BE5930` points to `0x08BB9D60`. The static tables establish string identity but are not themselves the rendering owner.

## Stable frame-capture findings

A read-only two-frame capture was taken in Arcade, Story, and Ghost Battle with the integrated timer build. The persistent top HUD separated into two useful families.

### Character-name rectangles

Character-name art already flows through the slot-`0xEF` rectangle compositor. Before the final fix it was already horizontally de-stretched by the existing 0.8 rectangle transform, but the y=28 family incorrectly fell through to CENTER anchoring.

Observed post-hook geometry before the side-anchor fix:

```text
Story P1 KAZUYA: x=57..108,  y=28..44, 51x16
Story P2 LARS:   x=381..432, y=28..44, 51x16
Arcade P2 ASUKA: x=343..445, y=28..44, 102x16
```

The 51/102-pixel widths are the 0.8-scaled forms of authored 64/128-pixel rectangles. Inverting the previous CENTER transform recovers approximate authored geometry:

```text
KAZUYA: x~10,  width 64
LARS:   x~415, width 64
ASUKA:  x~368, width 128
```

This proved that no new text renderer hook was required for character names. Only semantic side classification was missing.

The permanent rectangle predicate is deliberately narrow:

```text
y=28
height=16
authored width=64 or 128
```

Matching rectangles retain the existing 0.8 width correction and use authored X to select the anchor:

```text
X < 240 -> LEFT
X > 240 -> RIGHT
```

Expected fixed-20:9 positions from the recovered authored geometry are approximately:

```text
KAZUYA -> 8..59
LARS   -> 428..479
ASUKA  -> 390..492
```

On-device testing confirmed the names move outward to the intended sides while the center timer, HP bars, rank badges, side effects, round markers, winner orb, and winner glow remain correct.

The character-name rectangle family is therefore frozen unless a regression is demonstrated.

## Test-artifact failure and cleanup

The first name-anchor test artifacts (`v9` / `v9.1`) were structurally invalid for continued testing even though one of them visually corrected the names.

The failed experiment extended the PRX LOAD segment from:

```text
v8.1: 0x0EB0
v9.1: 0x1054
```

That extra `0x1A4` mapped bytes were residue from a temporary installer/trampoline experiment, not part of the name-anchor logic. The malformed artifact produced unrelated regressions, including PPSSPP replacement textures no longer being selected for some top-HUD assets and the user's fast-forward input no longer working normally.

A clean `v9.2` test was rebuilt directly from the known-good v8.1 PRX with identical ELF headers, LOAD segment size, section layout, module footprint, timer code, and all other hooks. Only two existing classifier instructions were changed in place. With that clean binary:

- character-name anchoring remained correct;
- custom replacement textures worked normally again;
- fast-forward input worked normally again;
- no regression was observed in the solved fight HUD.

This establishes the v9/v9.1 regressions as test-artifact contamination rather than a consequence of the semantic name-anchor correction. Future binary experiments must preserve the known-good PRX layout unless a deliberate module-layout change is independently required and validated.

## Top-row stage/time and battle-mode text

Arcade, Story, and Ghost captures all contain a stable top-row `0x80011E` glyph batch using the same texture/CLUT at y≈1..14. The batch spans nearly the full logical width:

```text
Arcade: x=12..467, count=52
Story:  x=12..467, count=50
Ghost:  x=11..467, count=52
```

This is consistent with a single combined font batch containing the left `STAGE/BATTLE + elapsed time` text and the right `ARCADE/STORY/GHOST BATTLE` label. Moving the complete batch would be incorrect. The next fix must identify and transform the side-owned glyphs within that batch:

```text
left stage/time glyphs -> LEFT
right mode glyphs      -> RIGHT
```

Ghost also contains a second `0x80011E` batch around y=32..46, consistent with additional player/opponent text. It should be investigated separately after the shared top-row owner is established.

## Next research target

Do not reopen the solved HP, rank/strip, timer, round-marker, winner-orb, or character-name rectangle subsystems.

The next target is the shared top-row `0x80011E` font renderer. Avoid a global font transform because result screens, pause UI, and front-end menus have different composition rules.
