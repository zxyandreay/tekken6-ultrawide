# v1.2.0 -> OPT-EXP2S3 internal space audit — 2026-09-21

## Purpose

Measure reusable capacity in the accepted optimization line relative to official v1.2.0 without overstating what is actually free.

This audit deliberately excludes all capacity estimates from rejected runtime-consolidation experiments.

Artifacts:

```text
official v1.2.0
SHA-256 311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75

accepted OPT-EXP2S3
SHA-256 7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805
```

Both remain:

```text
file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

The resident allocation has not shrunk.

## Confidence classes

Do not use one number for all "free" bytes.

The accepted image currently has three different classes:

1. hard-free detached bytes;
2. statically unreachable code that can be reclaimed only by an explicit repack;
3. inline startup instruction slots that are not a generic code cave.

Only class 1 should be described without qualification as free space.

## Category A — proven hard-free contiguous capacity

### Compressed slot-table tail

OPT-EXP2S2/S3 stores thirteen slot records at 8 bytes each.

The active table is:

```text
0x0A5C .. 0x0AC3
13 * 8 = 104 bytes
```

All three table walkers use the same end pointer and stride:

```text
end = 0x0A5C + 0x68 = 0x0AC4
validation stride     = +8
installation stride   = +8
cache-flush stride    = +8
```

The former tail is:

```text
0x0AC4 .. 0x0AF7
```

and is all zero in the accepted binary.

Capacity:

```text
0x34 = 52 bytes
```

Proof:

- the active table end is exactly 0x0AC4;
- every table walker terminates at that same end;
- no walker can advance into the tail;
- the bytes are zero-filled;
- the region is inside the existing executable PT_LOAD.

This is the only region currently classified as unquestioned general-purpose hard-free capacity.

## Category B — verified unreachable code, not yet physically reclaimed

### Old winner-glow first-slot X classifier

OPT-EXP2S3 changed:

```text
0x0D3C -> unconditional branch to 0x0D58
```

The skipped range is:

```text
0x0D40 .. 0x0D57
= 24 bytes
```

Before calling this block reusable, the accepted binary was checked for alternate entry paths.

Checks performed:

- scan of all PC-relative branch targets in the full 0x0EB0 load;
- scan of all direct J/JAL targets under the module's 0x08800000 execution region;
- scan for embedded absolute/module-relative pointers into 0x0D40..0x0D57;
- inspection of the winner-glow hook control flow;
- inspection of the PRX relocation records.

Result:

```text
no alternate branch target
no direct J/JAL target
no embedded pointer target
no relocation entry that creates an alternate entry
```

The only normal flow reaches 0x0D3C and jumps over the block to 0x0D58.

The accepted device test also validates that this bypass is the active winner-glow path.

Therefore the 24-byte block is statically unreachable in OPT-EXP2S3.

However:

- most of the bytes still contain old instructions;
- they have not yet been zeroed or repacked in an accepted build.

Classification:

```text
24 bytes verified unreachable / reclaimable by repack
NOT counted as hard-free until a build actually reclaims them
```

This distinction is intentional.

## Category C — startup-only inline instruction slots

OPT-EXP1 removed installation of the two upstream HP gauge hooks.

The initializer contains:

```text
0x03F0 = NOP
0x03F4 = NOP
```

Capacity:

```text
8 bytes
```

These words are still inside straight-line startup execution.

They are not a detached code cave.

They may only be reused by a startup repack that preserves surrounding control flow.

Classification:

```text
8 bytes startup-only inline opportunity
NOT general free space
```

## What is NOT free

### Former upstream HP wrapper

The old upstream HP wrapper was reused as the accepted downstream HP handler.

Net hard-free bytes from that region:

```text
0
```

The improvement is architectural, not a space reduction.

### Rejected slot-consolidation estimates

The 216-byte and 236-byte estimates belonged to OPT-EXP2 / EXP2R / EXP2R2.

Those architectures failed device testing.

Accepted capacity from those estimates:

```text
0
```

Do not cite those numbers as reclaimed space.

## Authoritative current budget

### Unquestioned hard-free capacity

```text
compressed table tail   52 bytes
```

### Additional verified reclaim candidates

```text
unreachable glow block  24 bytes
startup-only NOP slots   8 bytes
```

Therefore:

```text
52 bytes = already hard-free general capacity

24 bytes = statically proven unreachable, available only after explicit repack
 8 bytes = startup-only inline opportunity
```

A future compact build could potentially expose more, but it must be measured after device validation.

Do not describe the current accepted build as having "84 bytes of free space."

## OPT-EXP3A policy

OPT-EXP3A deliberately does not consume any of these three audited regions.

It leaves unchanged:

```text
0x0AC4 .. 0x0AF7   52-byte hard-free table tail
0x0D40 .. 0x0D57   24-byte unreachable glow block
0x03F0 .. 0x03F7   startup-only NOP slots
```

The first EXP3 experiment changes only the existing Practice/Gold font implementation and repurposes the already-dedicated late helper region.

This keeps the space audit independent from the behavioral proof of the one-hook font architecture.
