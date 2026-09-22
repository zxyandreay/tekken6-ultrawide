# OPT-EXP2S3 — winner-glow slot generalization

## Device finding that triggered this test

OPT-EXP2S2 fixed the startup hang and restored the earned-round alignment close to the validated layout, but the transient rotating earned-win halo still appeared on the wrong orb.

That visual symptom matches the historical "residual winner glow" subsystem rather than the ordinary round-marker rectangle path.

## What the old research actually proved

The original bilateral round-win capture proved the glow at only the first-win stock centers:

```text
P1 center ~198
P2 center ~280.5
```

The winner-glow hook then used those two narrow X-sum families as part of its predicate.

However, the ordinary late earned-orb classifier was already broader:

```text
P1 authored X: 150..206
P2 authored X: 273..310
```

That broader range exists because different win slots use different authored positions.

The winner-glow classifier never received an equivalent multi-slot generalization.

## Capture re-analysis

The archived P1/P2 round-win analysis files were rechecked.

Within the burst phase, every draw satisfying:

```text
vertex type = 0x80019E
primitive   = 4
count       = 4
center Y    = approximately 35
```

used the same winner-glow texture identity:

```text
texture SHA-256:
53f085d3224d25b4987fd6f31da53d2513297ef9192c77d5863eaefec97614bb

CLUT SHA-256:
a8413108ef6dc9eeaa5450943216de9e90728b9d004957c05ec1f609ef8706e4
```

No alternate top-row 0x80019E 4-vertex particle texture appeared in that row in either P1 or P2 capture.

That means the existing exact UV + vertex-count + Y-row checks already identify the winner-glow family strongly enough for a controlled test.

## EXP2S3 change

The existing hook remains unchanged except for removing the narrow first-slot-only X test.

Before:

```text
count == 4
exact 64x64 UV corners
X-sum matches first P1 or first P2 center
Y-sum matches winner row
→ transform
```

EXP2S3:

```text
count == 4
exact 64x64 UV corners
Y-sum matches winner row
→ transform
```

The transform itself remains the validated dynamic CENTER transform:

```text
x' = s*x + centerShift
```

All four source X values are still saved, transformed temporarily, passed through the original converter at `0x08AE94A4`, then restored.

## What is NOT changed

- ordinary earned-orb rectangle path;
- P2 x=273 late-orb boundary;
- persistent round-marker scope;
- slot installer compression from EXP2S2;
- downstream HP optimization;
- timer;
- rank/strip;
- character names;
- Practice/Gold text;
- winner-glow UV/Y/count checks;
- PRX allocation.

## Binary

```text
SHA-256:
7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Test priority

Test the halo across more than one earned round if possible.

For P1 and P2:

1. first earned round;
2. second earned round;
3. if the mode allows it, another later win slot;
4. verify the rotating halo follows the newly lit orb each time;
5. verify the next-round persistent marker stays aligned;
6. confirm no unrelated top-row particle is moved.

If this works, it confirms that the historical glow fix was first-slot-specific rather than truly round-slot-generic.
