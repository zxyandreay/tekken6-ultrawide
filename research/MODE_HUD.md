# Practice and Gold Rush HUD

## Status

Mode-specific HUD research after the persistent normal battle HUD, center timer, and character-name anchoring were validated.

The normal Arcade/Story/Ghost battle-HUD fixes remain frozen unless a regression is demonstrated.

Current status:

```text
Practice infinity indicator        SOLVED / DEVICE VALIDATED
Practice damage/combo readout      SOLVED / DEVICE VALIDATED
Gold Rush static labels            CORRECTION PATH VALIDATED
Gold Rush money strings            OPEN / COMPOSITION RULE UNDER TEST
```

## Practice

### Infinite-time indicator

The Practice infinite-time (`∞`) indicator was displaced left into/behind the P1 health-bar area after the ordinary countdown work.

The ordinary decimal countdown is still owned by the two validated timer submissions:

```text
0x08929AF8
0x08929B44
```

A direct A/B against those two calls did not restore the Practice indicator, proving that the visible `∞` is not owned by the normal tens/ones timer submissions.

The stable Practice capture isolated one mode-only `0x80011A` rectangle:

```text
post-hook bbox: x=166..217, y=6..38
post-hook size: 51x32
texture: 0f87368a50b3...
```

An exact-shape rectangle diagnostic moved only this already-transformed `51x32` rectangle from x=166 to x=214. Device testing confirmed that this restores the Practice `∞` to the visual center while leaving the normal decimal countdown unchanged.

This family is therefore considered solved. The permanent implementation should preserve the narrow exact-shape / Practice-only ownership gate rather than weakening the normal timer correction.

### Practice statistics panel

The left Practice DAMAGE / HIT COMBO / DAMAGE readout is rendered inside a batched `0x80011E` font submission using texture `8b127e798779...`.

Second-stage glyph analysis separates the Practice battle HUD cleanly:

```text
mode header:  y=2..14, far right
stats rows:   y=104..116
              y=116..128
              y=127..139
```

The idle batch contains 38 vertices; the hit state grows to 78 vertices, adding 20 rectangle/glyph pairs for the dynamic Practice readout.

A battle-HUD-gated converter diagnostic applied only:

```text
x < 200
y = 104..139
LEFT transform: x' = trunc(4*x/5)
```

Device testing confirmed that the Practice damage/combo readout becomes proportion-correct and remains correctly left-owned.

An earlier diagnostic matched only by X/Y bands and also affected Practice menus that reused the same global font converter. The corrected diagnostic additionally requires the far-right Practice/Gold-Rush mode header in the same converter batch before any glyph transformation. Permanent code must retain an owner/batch gate; a global font-row transform is not acceptable.

Practice battle HUD is considered solved at the research level.

## Gold Rush

Gold Rush uses the same `0x80011E` batched font family, but its composition contains several independent strings in the same converter submission. The visible right-side labels and money values must not be treated as one undifferentiated screen-right block.

The captured Gold Rush font batch contains 96 vertices / 48 glyph rectangles. Per-glyph analysis recovers these stable groups:

### Mode header

```text
y=2..14
x≈377..466
```

`GOLD RUSH` is already acceptable and should remain untouched.

### Top reward row

The y=16 row contains two separate strings:

```text
REWARD:       x≈276..349   7 glyphs
reward value  x≈409..465   5 glyphs in the captured sample
```

The last reward-value glyph uses the distinct gold/currency color but remains part of the same `0x80011E` batch.

### Attack-variation row

```text
ATTACK VARIATION  x≈317..466, y=64..76
```

One low-alpha glyph/rectangle also appears around x≈477..490 in the captured batch and should not be used as the alignment anchor for the visible label.

### Gold-gain rows

Two dynamic six-glyph money rows were captured:

```text
y=136..148, x≈399..465
y=148..160, x≈399..465
```

Each contains a leading plus/value sequence and a differently colored final currency glyph.

## Device result from first Gold Rush correction

The first safe battle-batch-gated diagnostic applied the generic RIGHT rule:

```text
x' = trunc(4*x/5) + 96
```

to the Gold Rush y=16, y=64, y=136, and y=148 regions.

Device testing showed:

- `REWARD:` and `ATTACK VARIATION` visibly improved;
- the money/value strings became inconsistent in perceived scale/spacing;
- Practice remained corrected;
- the remaining Gold Rush problem is therefore specifically the money/string composition rule, not basic font ownership.

The generic screen-right origin is too coarse for a batch that contains both left-aligned and right-aligned strings.

## Current Gold Rush A/B

Two narrower composition models should be compared before permanent integration.

### Variant A — labels only

Keep the validated Practice correction. In Gold Rush:

```text
correct REWARD:
correct ATTACK VARIATION
leave top reward amount stock
leave +gold rows stock
```

This tests whether the money strings were already acceptable and were over-corrected by the first generic RIGHT transform.

### Variant B — local string anchors

De-stretch each Gold Rush string around its own composition anchor rather than framebuffer x=480:

```text
REWARD:            keep left edge around x=276
reward amount:     keep right edge around x=465
ATTACK VARIATION:  keep right edge around x=466
+gold rows:        keep right edge around x=465
```

The intended scale remains 0.8 horizontally; Y, vertical scale, UVs, color, and animation remain unchanged.

The device comparison between Variant A and Variant B will determine the permanent Gold Rush rule.

## Converter path

The relevant `0x80011E` dispatcher path reaches the converter through:

```text
0x08AC9CC4 -> 0x08AE9C14
```

The converter emits 16-byte THROUGH vertices. The diagnostic post-processes only X after Tekken's own conversion and only after the whole-batch ownership predicate passes.

This is intentionally separate from the slot-`0xEF` rectangle hook; Practice/Gold Rush font glyphs do not belong to the axis-aligned rectangle family used by the HP shell, round markers, timer digits, or character-name plates.

## Safety rules

- Keep the validated normal Arcade/Story/Ghost HUD frozen.
- Keep the ordinary decimal timer correction frozen.
- Practice `∞` must use a narrow exact-shape/mode rule.
- Never globally transform the `0x80011E` font converter by screen row alone.
- Require battle-HUD batch ownership before Practice/Gold Rush text correction.
- Preserve PPSSPP texture replacement behavior and emulator controls.
- Test PRXs must retain the clean validated module layout; do not repeat the malformed v9/v9.1 load-segment experiment.
