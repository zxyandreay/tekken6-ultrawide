# Winner-orb and round-win glow investigation

## Final status

Solved and validated on-device for both P1 and P2.

The ordinary newly earned orb and the transient winner glow are two separate draw paths. Both now use the same 20:9 CENTER composition, but they require different hooks.

## Initial symptoms

Two distinct defects exposed the split:

1. P1: the earned orb could be correctly positioned while a residual glow remained at the stock orb position.
2. P2: on the first win, the immediate earned orb appeared at the wrong/second-looking slot; when the next round began, the persistent first orb appeared correctly without another win.

The second symptom proved that immediate and persistent round-marker submissions were not identical.

## Neutral bilateral capture

A read-only PPSSPP capture was run independently for controlled P1 and P2 first wins. Each run recorded:

```text
2 pre-KO frames
18 immediate win/burst frames
3 stable next-round frames
```

No texture identity was preselected by the analyzer.

### Earned orb

Earned-orb texture:

```text
SHA-256: 9cef219613e142077222ded7d79fd43f65044d360b36f331ec80a62b46a160aa
CLUT:    3b52e8483492c86a22f0d42a4217054c9e0c9a538ba42e9b29dacbb6e0ed0b9d
```

P1 immediate and next-round geometry:

```text
bbox   201..213 x 27..43
center 207,35
size   12x16
```

P1 was already passing through the intended center correction.

P2 immediate first-win geometry before the fix:

```text
bbox   273..289 x 27..43
center 281,35
size   16x16
```

P2 next-round persistent geometry:

```text
bbox   267..279 x 27..43
center 273,35
size   12x16
```

The persistent geometry exactly matches the integer center transform of stock `x=273`, `w=16`:

```text
x' = trunc(273*4/5)+49 = 267
w' = trunc(16*4/5)     = 12
```

The late-orb predicate had started the P2 authored range at `274`, so the first P2 orb at `273` missed the hook by one pixel. Changing the lower bound to `273` fixed the immediate first-win orb. Device testing confirmed that the first P2 orb now lights immediately and remains the same first orb into the next round.

## Winner glow GPU identity

The neutral capture independently isolated a transient rotated THROUGH draw with the timing and position of the visible residual glow:

```text
primitive:       4-vertex triangle strip
vertex type:     0x80019E (THROUGH)
output stride:   20 bytes
texture:         64x64, format 5
texture SHA-256: 53f085d3224d25b4987fd6f31da53d2513297ef9192c77d5863eaefec97614bb
CLUT SHA-256:    a8413108ef6dc9eeaa5450943216de9e90728b9d004957c05ec1f609ef8706e4
UV corners:      (0,0), (0,64), (64,0), (64,64)
```

Behavior across phases:

- absent before KO;
- appears with the newly earned orb during the win burst;
- size/alpha animate during the burst;
- disappears before the stable next-round HUD;
- remains centered on the stock/original orb coordinate until corrected.

Observed centers from clean captures:

```text
P1 glow: ~198,35
P1 corrected orb: 207,35

P2 glow: ~280.5,35
P2 corrected orb: 273,35
```

Applying the float center transform gives:

```text
P1: 0.8*198.0 + 48 = 206.4
P2: 0.8*280.5 + 48 = 272.4
```

which aligns with the corrected orb positions within expected float/integer differences.

## Static EBOOT correlation

The ULUS10466 EBOOT is a directly usable little-endian MIPS ELF mapped into the same address region used by runtime debugging.

Static analysis identified the CPU converter at:

```text
0x08AE94A4
```

This routine writes the exact `0x80019E` output layout:

```text
+0x00 UV U (16-bit)
+0x02 UV V (16-bit)
+0x04 packed color
+0x08 float X
+0x0C float Y
+0x10 float Z
stride 0x14 / 20 bytes
```

The relevant converter call is:

```text
0x08AC9C38: 0x0E2BA529  -> JAL 0x08AE94A4
```

The plugin validates this stock instruction before redirecting the call.

The source records consumed by the converter have stride `0x30`. For the four glow vertices, X is read at:

```text
0x00, 0x30, 0x60, 0x90
```

and the 64x64 UV corner pairs are at source offsets `+0x20/+0x22` for each record.

## Final hook predicate

`tekken6_hud_winner_glow_hook` is deliberately narrow. It requires:

- vertex count `a3 == 4`;
- exact UV sequence `(0,0), (0,64), (64,0), (64,64)`;
- P1 stock center family selected by `x0+x3` approximately `394..398` (center ~198);
- or P2 stock center family selected by `x0+x3` approximately `559..563` (center ~280.5);
- `y0+y3` approximately `68..72` (winner-orb row center ~35).

When the predicate matches, only the four source X coordinates are temporarily transformed:

```text
x' = 0.8*x + 48
```

Tekken's original converter at `0x08AE94A4` is then called, and the four original source X values are restored immediately.

This preserves:

- Y positions;
- UVs;
- color and alpha;
- Z;
- rotation/skew;
- animation size/lifetime behavior;
- the source object for any later consumers.

All nonmatching converter traffic passes through unchanged.

## Validation

Before integration, the predicate was checked against both bilateral round-win capture inventories. Every matching top-HUD draw used the same winner-glow texture identity; no alternate texture matched in those captures.

A reversible runtime diagnostic using the same converter/predicate was then tested on-device:

```text
P1 winner glow -> corrected
P2 winner glow -> corrected
```

The same logic was integrated into the PRX while retaining the one-pixel P2 late-orb fix. A subsequent integrated-plugin test again passed for both P1 and P2.

Therefore:

- immediate P1/P2 earned-orb placement is solved;
- persistent next-round P1/P2 marker placement is solved;
- transient P1/P2 winner glow is solved;
- the round-win orb subsystem is considered complete.

## Rejected paths and lessons

Several earlier approaches were useful only to eliminate possibilities:

- transient output VADDRs and cached GE-list positions move between frames/loads and are not stable hook identities;
- CPU read watchpoints do not observe GE DMA reads of cached command data;
- a suspected builder at `0x08ACABE8` was disproven; it is effectively a return site, not the `0x80019E` builder;
- a resource/cache value `0x40000401` was observed during one resource correlation but was never required by the final fix and should not be treated as a production identity;
- global THROUGH/particle transforms are unnecessary and carry unacceptable collateral risk.

The decisive path was GPU phase correlation followed by static identification of the exact CPU vertex converter and a geometry-specific hook.
