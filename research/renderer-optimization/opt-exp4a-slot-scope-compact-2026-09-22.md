# OPT-EXP4A plan — compact slot-scope wrapper — 2026-09-22

## Base

Device-accepted:

```text
OPT-EXP3D-A — GlowFullSlotRange
SHA-256:
d8afe941dc3198107a460511d78fa2d8acde6f709020a7b351605e6a6fdfe17f
```

Winner-glow code is frozen and excluded from this experiment.

## Target

Current slot-scope wrapper:

```text
0x05A0 .. 0x0647
168 bytes
```

All 13 game callsites remain exactly as accepted.

The wrapper's purpose is:

1. if original a1 == 0xEF, increment module scope counter;
2. call stock 0x0892D9F8;
3. if original a1 == 0xEF, decrement scope counter;
4. return exactly as the original callsite expects.

## Redundancy in the accepted wrapper

The current wrapper saves and restores:

```text
a0 a1 a2 a3
t0 t1 t2 t3
f12
```

before the stock call.

But the wrapper itself modifies none of those values.

Before the stock call it uses only t4/t5 for the scope counter.

Therefore the save/restore block is unnecessary for preserving the original
0x0892D9F8 input state.

The only values that must survive across the stock call are:

- incoming ra;
- original a1, for the post-call scope decision;
- the scope-counter pointer on the matched path.

## Boundary-state equivalence

### Non-0xEF path

At stock 0x0892D9F8 entry:

```text
a0-a3 unchanged
t0-t3 unchanged
f12 unchanged
t4 = 0xEF
t5 unchanged
```

This matches the accepted wrapper.

At wrapper return after the stock call:

```text
t4 = original a1
t5 = 0xEF
v0 = stock return value
ra/sp restored
```

This also matches the accepted wrapper.

### 0xEF path

At stock entry:

```text
t4 = module+0x0C44
t5 = incremented scope value
```

matching the accepted wrapper.

At wrapper return:

```text
t4 = module+0x0C44
t5 = decremented scope value
v0 = stock return value
ra/sp restored
```

again matching the accepted wrapper.

## Relocation handling

The old wrapper has two module-local HI16/LO16 pairs:

```text
0x05D8 / 0x05DC
0x0628 / 0x062C
```

The compact wrapper derives the counter pointer once through a BAL-relative local
PC value and stores that pointer on its stack.

The four old relocation records are therefore changed to R_MIPS_NONE.

No new relocation is required.

## Candidate size

Compact wrapper:

```text
0x05A0 .. 0x0603
96 bytes
```

New detached zero tail:

```text
0x0604 .. 0x0647
72 bytes
```

Existing accepted hard-free block:

```text
0x0C00 .. 0x0C3F
64 bytes
```

If device validation passes:

```text
72 + 64 = 136 bytes
```

of general detached hard-free capacity.

This is a candidate count until device validation.

## What does NOT change

- 13 slot callsites;
- J versus JAL semantics at those callsites;
- stock slot builder 0x0892D9F8;
- scope counter location;
- rectangle compositor;
- HP path;
- timer;
- Practice/Gold helper;
- character names;
- round-marker rectangle path;
- frozen EXP3D-A winner-glow path;
- PT_LOAD size/layout.

## Test priority

1. cold boot / title / menus;
2. Arcade battle;
3. P1 and P2 first + later earned wins, including spinning halo;
4. HP full/partial/low;
5. ranks / side strips / names;
6. timer;
7. Practice;
8. Gold Rush;
9. Ghost / Story;
10. replacement textures/fonts;
11. fast-forward.

No GitHub Actions are used.
