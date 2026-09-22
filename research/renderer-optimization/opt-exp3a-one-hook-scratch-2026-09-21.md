# OPT-EXP3A OneHookScratch — test candidate

## Purpose

Test whether the accepted two-stage Practice/Gold text correction can be reduced to one dynamic game hook without changing visible behavior.

No GitHub Actions are used.

Base:

```text
OPT-EXP2S3 accepted checkpoint
SHA-256:
7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805
```

Candidate:

```text
OPT-EXP3A-OneHookScratch
SHA-256:
46063c6097e3dfaa51aafd077e0e5c65f02487bdbe420f8884f2a292edf8cf1f
```

Layout remains:

```text
file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Stock-flow proof used by this experiment

Relevant stock sequence:

```text
0x08970A90  lhu t3,0x2C8(s6)
...
0x08970B1C  beq t1,t0,0x08971120
...
0x08970B24  lw  a0,0x2C8(s6)
...
0x08970B40  sw  zero,0x28(sp)
```

Fast path:

```text
0x08971120  lw a0,0x2C8(s6)
...
returns to the common path that reaches 0x08970B40
```

Static inspection confirms:

- `0x28(sp)` is not read between A90 and B24;
- the fast path does not read `0x28(sp)`;
- both paths reach B40, which clears `0x28(sp)`;
- `0x58(sp)` authored X is not consumed between A90 and the current late correction point.

Therefore `0x28(sp)` can be used as short-lived per-call scratch without mutating persistent `s6` renderer state.

## Candidate architecture

### Dynamic game hook

Only:

```text
0x08970A90
```

continues to redirect to plugin code.

### Static late-site patch

```text
0x08970B24
```

is patched to:

```text
lw a0,0x28(sp)
```

It no longer calls plugin code.

### Non-target slow path

The early hook stores:

```text
0x28(sp) = original packed value from s6+0x2C8
```

so B24 remains stock-equivalent.

### Target Practice/Gold

The early hook retains the accepted owner/row predicates.

For a target glyph it branches to the existing C00 helper region, now repurposed as an early-hook postprocessor.

It:

- loads the same dynamic corrected horizontal scale used by OPT-EXP2S3;
- preserves the fast-path behavior;
- on the slow path, writes the corrected scale to 0x28(sp);
- applies the Gold X shift only on the slow path, matching the accepted two-stage behavior;
- leaves Practice authored X unchanged;
- resumes at stock 0x08970A98.

## Why EXP3A does not claim new free bytes yet

The old late helper region is repurposed for the state-equivalence test.

It is not counted as reclaimed.

EXP3A also leaves untouched:

```text
0x0AC4..0x0AF7  hard-free table tail
0x0D40..0x0D57  unreachable glow block
0x03F0..0x03F7  startup-only NOP slots
```

Only after device validation should a later EXP3B compact/repack the helper and measure net savings.

## Required device tests

First test Practice and Gold Rush.

Practice:

- infinity indicator;
- DAMAGE;
- HIT COMBO;
- DAMAGE readouts;
- header unchanged;
- no missing glyphs.

Gold Rush:

- REWARD;
- ATTACK VARIATION;
- right-side placement;
- currency/value rows remain excluded;
- no missing or widely spaced glyphs.

Then regression:

- Arcade;
- Story;
- Ghost Battle;
- main menu;
- pause;
- character select;
- replacement textures/custom fonts;
- HP full/partial/low both sides;
- ranks/side strips;
- timer;
- earned round orbs;
- winner glow/halo;
- fast-forward and normal controls.

Acceptance requires behavior matching OPT-EXP2S3.
