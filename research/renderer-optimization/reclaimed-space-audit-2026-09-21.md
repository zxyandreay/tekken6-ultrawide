# Accepted internal-space audit — OPT-EXP3D-A — 2026-09-22

## Authoritative baseline

```text
OPT-EXP3D-A — GlowFullSlotRange
SHA-256:
d8afe941dc3198107a460511d78fa2d8acde6f709020a7b351605e6a6fdfe17f

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

Resident allocation reduction remains:

```text
0 bytes
```

The fixed 0x0EB0 mapping remains part of correctness.

## Hard-free general-purpose capacity

### Old Practice/Gold helper allocation

EXP3A validated the one-hook stack-scratch architecture.

EXP3B relocated its 52-byte live helper into the previously proven 52-byte slot-table tail.

The old helper allocation was then detached and zeroed:

```text
0x0C00 .. 0x0C3F
64 bytes
```

This relocation remained intact through EXP3C and device-accepted EXP3D-A.

Therefore the accepted general-purpose hard-free capacity is:

```text
64 bytes
```

## Regions that are NOT free

### Former compressed-table tail

```text
0x0AC4 .. 0x0AF7
```

This was previously 52 bytes of hard-free space.

It now contains the live one-hook Practice/Gold helper.

Current free capacity:

```text
0 bytes
```

### Winner-glow classifier

The earlier audit treated part of:

```text
0x0D40 .. 0x0D57
```

as a possible reclaim candidate.

That classification is permanently withdrawn.

EXP3C/EXP3D established that this region participates in the accepted winner-glow ownership logic.

Current free capacity:

```text
0 bytes
```

Do not optimize this region independently.

### Startup HP installer NOPs

```text
0x03F0 .. 0x03F7
8 bytes
```

These remain inside straight-line startup execution.

Classification:

```text
startup-only inline opportunity
NOT general hard-free space
```

## Accepted budget

```text
general-purpose hard-free: 64 bytes
startup-inline opportunity:  8 bytes
resident allocation saved:   0 bytes
```

Do not combine 64+8 into one generic free-space number.

## Historical numbers that must not be reused

Do not cite as current accepted free space:

- 52-byte old table-tail cave — now occupied by live font helper;
- 24-byte old glow block — now live/frozen;
- 76/84-byte EXP2S3 accounting — obsolete after later accepted repacking;
- 216/236-byte EXP2/EXP2R estimates — rejected architecture.

## Rule for further optimization

Future work may use the 64-byte hard-free block if needed, but an optimization that merely consumes it without reclaiming more elsewhere is not a space optimization.

Prefer changes that simplify runtime topology or create a larger detached region while keeping:

```text
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

Winner-glow code is frozen and excluded from optimization targets.

No GitHub Actions are used.
