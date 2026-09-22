# OPT-EXP2S startup hang and OPT-EXP2S2 fix — 2026-09-21

## Device result

OPT-EXP2S is rejected.

Observed behavior:

- PPSSPP/Tekken 6 becomes very laggy at startup;
- black screen persists;
- game appears not to finish loading;
- device resource use rises.

This is consistent with an infinite startup loop.

## Exact root cause

OPT-EXP2S compressed the slot patch table from 12-byte records to 8-byte records.

The initializer walks that table three separate times:

1. validate each target instruction;
2. install each replacement hook;
3. invalidate/flush each patched instruction address.

The first two loops were changed to +8-byte stride.

The third loop, beginning around module-relative 0x0408, was accidentally left at the original +12-byte stride:

```text
0x0408  lw    a0,0(s0)
0x040C  li    a1,4
0x0410  jal   cache/invalidate helper
0x0414  addiu s0,s0,0x0C   ; BUG: old 12-byte stride
0x0418  bnel  s0,s1,0x040C
```

The compressed table end is:

```text
start + 0x68
```

and:

```text
0x68 = 104
```

Since 104 is not divisible by 12, the pointer sequence can never equal the new end pointer. The cache-flush loop therefore never terminates.

That exactly explains the black screen and high resource usage.

## OPT-EXP2S2 correction

Only one runtime word differs from rejected OPT-EXP2S:

```text
module+0x0414
0x2610000C  addiu s0,s0,12
    ->
0x26100008  addiu s0,s0,8
```

After this correction all three table walks use the same 8-byte stride:

```text
validation:     +8
installation:   +8
cache flushing: +8
```

For 13 records:

```text
13 * 8 = 104 = 0x68
```

so every loop terminates exactly at the compressed table end.

## Safety properties

OPT-EXP2S2 still preserves the conservative EXP2S architecture:

- all 13 original battle-time slot hooks remain;
- original v1.2.0/OPT-EXP1 slot wrapper remains unchanged;
- late earned-orb predicate unchanged;
- winner-glow converter unchanged;
- OPT-EXP1 downstream HP optimization unchanged;
- timer/text/rank/strip/name paths unchanged.

The optimization remains startup-only.

## Reclaimed capacity

```text
old slot table: 13 * 12 = 156 bytes
new slot table: 13 *  8 = 104 bytes
reclaimed:                  52 bytes
```

The same 52-byte contiguous tail remains available inside the fixed PT_LOAD.

## Binary

```text
OPT-EXP2S2 SHA-256:
1a23770194fe66f753554a1981d55d64e266f398f4f44b156ffa9385529a4409

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Test order

First verify the specific rejected boundary:

1. cold-boot PPSSPP;
2. confirm Tekken 6 reaches the title/menu normally;
3. enter a fight and confirm the HUD appears without crash/hang;
4. verify P1/P2 round-win orb/halo against OPT-EXP1;
5. then continue the normal HUD/texture/fast-forward regression sweep.
