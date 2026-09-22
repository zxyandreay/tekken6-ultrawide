# Winner-glow later-slot investigation — 2026-09-22

## Device symptom

EXP3C-A and EXP3C-B both:

- correctly identify and animate the spinning halo;
- correctly position the first earned-win halo;
- fail to position the halo on the correct orb for subsequent wins.

The behavior is identical with dynamic AutoHUD math and fixed v7 20:9 math.

Therefore transform math is not the cause of the later-win failure.

## Archived-documentation finding

The repository's historical winner-glow conclusion was broader than its test coverage.

The recovered RoundWin-v7 research used two controlled captures:

```text
P1 first win:
2 pre-KO
18 immediate first-win/burst frames
3 next-round frames

P2 first win:
same protocol
```

There is no second- or third-win capture in that validation.

The historical final X predicate was:

```text
P1 x0+x3 approximately 394..398
P2 x0+x3 approximately 559..563
```

Those are first-slot center families, not a general round-slot family.

The old test then stated the subsystem was solved for P1/P2, but it had only
demonstrated first-win correctness.

## Why this matches the current result

The ordinary late earned-orb rectangle path was already documented with a wider
authored family:

```text
y=27
16x16

P1 authored X 150..206
P2 authored X 273..310
```

The repository explicitly records the lesson:

> visually identical earned-orb states can use slightly different authored
> coordinates or draw phases.

That lesson was applied to the P2 first-orb lower-bound bug, but not to later
winner-glow slots.

After EXP3C repaired the compact UV identity, the glow hook now reaches the
actual rotating 64x64 quad. The remaining narrow first-slot X gate explains:

```text
first win -> matches -> transformed correctly
later win -> different stock X center -> rejected -> remains at stock position
```

## EXP3D-A — full round-family X gate

Keep all EXP3C protections:

- a3 == 4;
- exact 64x64 UV corners;
- winner-row Y;
- source-X-only temporary transform;
- source restore;
- original converter;
- dynamic AutoHUD CENTER math.

Broaden only X ownership.

The known late rectangle family gives a conservative source-center envelope.

P1:

```text
authored rectangle X 150..206
approx center X      158..214
approx x0+x3         316..428
with small float/rotation margin:
high16 0x439c..0x43d7
```

P2:

```text
authored rectangle X 273..310
approx center X      281..318
approx x0+x3         562..636
observed first glow ~559
with margin:
high16 0x440b..0x441f
```

This is intentionally wider than the three inferred standard slots so the fix
does not depend on a single round-count configuration.

## EXP3D-B — UV/Y-only fallback diagnostic

If A still misses a later spinner, remove only the X gate.

Still require:

```text
4 vertices
exact 64x64 UV
winner-row Y
```

Interpretation:

- A fixes all slots -> historical first-slot X gate was the remaining bug;
- A misses but B fixes -> later geometry lies outside the inferred round-family envelope;
- both miss -> later wins use another source/callsite/path and require runtime capture.

## Acceptance rule

A pass requires all of:

- first P1 win spinner rotates and is centered on the newly lit orb;
- later P1 win spinner rotates and follows the newly lit orb;
- first P2 win correct;
- later P2 win correct;
- persistent next-round marker remains aligned;
- no unrelated top-HUD effect is shifted.

A first-win-only pass is explicitly insufficient.

No GitHub Actions are used.
