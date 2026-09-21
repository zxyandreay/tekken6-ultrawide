# v1.2.0 -> OPT-EXP2S3 internal space audit — 2026-09-21

## Purpose

Measure actual reusable capacity in the accepted optimization line relative to official v1.2.0.

This audit deliberately excludes capacity estimates from rejected runtime-consolidation experiments.

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

Therefore resident allocation has not shrunk.

The optimization target is reusable capacity *inside* the fixed image.

## Category A — hard-free contiguous capacity

### Compressed slot-table tail

Accepted OPT-EXP2S2/S3 stores thirteen slot records at 8 bytes each.

The table now ends at:

```text
module+0x0AC4
```

The previous table allocation continued through:

```text
module+0x0AF7
```

Current bytes:

```text
0x0AC4 .. 0x0AF7 = all zero
```

Capacity:

```text
0x34 = 52 bytes
```

This is the strongest available region:

- contiguous;
- zero-filled;
- no longer visited by the table loops;
- inside the executable PT_LOAD;
- available for code or constants without increasing p_memsz.

## Category B — validated dead code, reusable after repack

### Winner-glow first-slot X classifier

OPT-EXP2S3 now branches directly:

```text
0x0D3C -> 0x0D58
```

after the exact UV/count checks.

The old narrow first-slot X classifier at:

```text
0x0D40 .. 0x0D57
```

is no longer reachable.

Capacity:

```text
0x18 = 24 bytes
```

Only `0x0D40` is currently zero; the rest still contains the old instructions.

Because the new unconditional branch skips the whole range and the accepted device test validates the generalized glow path, this 24-byte block can be overwritten by a future builder.

It should be treated as logically reclaimed, but not yet as zero-filled capacity.

## Category C — startup-only instruction slots

### Removed upstream HP hook installs

OPT-EXP1 stopped installing the two upstream gauge hooks.

The initializer now contains:

```text
module+0x03F0 = NOP
module+0x03F4 = NOP
```

Capacity:

```text
8 bytes
```

These two words lie in straight-line startup execution, so they are not a generic detached code cave.

They may be reused for startup calculations/install operations only, or only with an explicit branch/repack that preserves control flow.

Do not add them to the generic code-cave budget.

## What is NOT free

### Old upstream HP wrapper

The former HP wrapper at roughly:

```text
0x07E4 .. 0x084C
```

was repurposed as the accepted downstream HP handler.

Net reusable capacity from that region:

```text
0 bytes
```

The architectural win is two fewer game hooks and reduced dependence on gauge-owner internals, not resident-space reduction.

### Rejected slot-consolidation estimates

The 216-byte and 236-byte estimates from OPT-EXP2/EXP2R were based on removing the original thirteen runtime slot wrappers/table entries.

Those architectures failed device testing.

Accepted reusable capacity from those estimates:

```text
0 bytes
```

## Authoritative accepted byte budget

General reusable capacity:

```text
hard-free table tail              52 bytes
dead winner-glow X block          24 bytes
------------------------------------------
general reusable capacity         76 bytes
```

Additional startup-only instruction capacity:

```text
removed HP-install stores          8 bytes
```

Total available when execution-context restrictions are respected:

```text
76 bytes general
+8 bytes startup-only
=84 bytes of accepted reclaimed instruction/storage opportunity
```

This is not equivalent to reducing `p_memsz` by 84 bytes.

The module must remain at the validated:

```text
p_filesz = p_memsz = 0x0EB0
```

unless a separate controlled memory-layout experiment proves otherwise.

## Next target implication

A safe OPT-EXP3 should aim to free substantially more than it consumes.

The two-stage Practice/Gold mode-font implementation currently uses:

- an early hook at `0x08970A90`;
- a late hook at `0x08970B24`;
- early target classification in the compact tail;
- a separate late helper around module `0x0C00..0x0C3F`.

If the late helper can be replaced by one stock instruction reading a short-lived stack scratch prepared by the early hook, the entire ~64-byte late helper becomes a candidate for reclamation.

That direction is preferable to mutating persistent `s6` text state.
