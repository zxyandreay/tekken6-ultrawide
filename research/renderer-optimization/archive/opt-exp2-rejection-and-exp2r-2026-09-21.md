# OPT-EXP2 rejection and OPT-EXP2R repair — 2026-09-21

## Device result

OPT-EXP2 is rejected.

Observed on-device regression:

- round/win orb behavior regressed;
- the post-win visual appeared to light the wrong-looking slot again;
- the earned orb looked much redder than the normal orange-lit v1.2.0/OPT-EXP1 result.

OPT-EXP1 remains the last validated optimization checkpoint.

## What did not break

The dedicated winner-glow converter hook was not changed by OPT-EXP2.

The v1.2.0/OPT-EXP1 winner-glow code remains at module-relative roughly `0x0D80..0x0DFC`, including its stock converter call:

```text
0x08AC9C38 -> 0x08AE94A4
```

A binary diff between OPT-EXP1 and rejected OPT-EXP2 changes only:

- the slot installer loop bound;
- module-relative `0x05A0..0x0647` slot wrapper;
- the slot patch table at `0x0A5C..`;
- the corresponding relocation metadata.

The winner-glow implementation itself is byte-identical.

## Root cause

The original released slot wrapper explicitly preserved these live renderer inputs before calling `0x0892D9F8`:

```text
a0-a3
t0-t3
f12
```

The saved/restored block is visible in the authoritative OPT-EXP1/release binary at module `0x05A0..`.

The stock renderer census had already established the semantic reason:

```text
t0/t1 = live renderer flags
t2/t3 = optional translation/scale pointers
f12   = live renderer value
```

Rejected OPT-EXP2 moved the interception to the internal call `0x0892DA04`, but used `t0/t1` as temporary registers for the rectangle-depth counter before calling `0x0892D72C`.

That means the consolidated wrapper passed corrupted renderer state into `0x0892D72C`.

This is an ABI violation.

## Why the round-win orb exposed it

The round-marker subsystem is unusually sensitive because it combines several distinct paths:

1. persistent round rails/orbs through the protected rectangle scope;
2. a newly earned late orb with a separate narrow y=27 / x-range predicate;
3. a separate rotated THROUGH winner-glow converter.

The documentation explicitly records that the immediate earned orb and the transient winner glow are different draw paths.

The dedicated glow remained correct, while the scoped ordinary round-marker path received corrupted `t0/t1` state. That can change how the underlying round-marker/overlay submission is built. Visually, the unchanged glow then no longer composites/aligned with the same ordinary orb state, which is consistent with the reported wrong-slot/red-vs-orange appearance.

The correct response is therefore not to edit the winner-glow predicate or late-orb x=273 fix. Those remain frozen.

## Corrected OPT-EXP2R design

Keep the 13 -> 1 hook consolidation, but make the new internal wrapper transparent to the known renderer ABI.

At `0x0892DA04`, stock D9F8 has already executed:

```text
addiu sp,sp,-0x20
addiu v0,zero,1
sw    ra,0x10(sp)
```

and its call delay slot stores:

```text
sw v0,0(sp)
```

so the fifth argument is already correctly present for `0x0892D72C`.

OPT-EXP2R therefore:

- does not change `sp`;
- does not touch `a0-a3`;
- does not touch `t0-t3`;
- does not touch `f12`;
- uses only `t4/t5` for depth bookkeeping, matching the released wrapper's existing scratch behavior;
- for non-0xEF calls, tail-jumps directly to `0x0892D72C`;
- for 0xEF calls, increments depth, calls `0x0892D72C`, decrements depth, then jumps to the stock D9F8 epilogue at `0x0892DA0C`.

## Reclaimed capacity if OPT-EXP2R passes

The fixed PRX remains:

```text
file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

The compact ABI-safe wrapper ends at module `0x05E8`.

That leaves:

```text
unused old slot table records: 144 bytes
unused old wrapper tail:        92 bytes
----------------------------------------
reusable internal capacity:    236 bytes
```

Do not count those 236 bytes as validated free space until OPT-EXP2R passes the full device regression sweep.

## Test priority

The first acceptance check for OPT-EXP2R must be the exact regression that rejected EXP2:

1. P1 first win;
2. P2 first win;
3. immediate earned orb slot;
4. orange-lit appearance during winner burst;
5. stable next-round persistent orb;
6. winner glow alignment.

Only then continue to HP, names, timer, ranks/strips, Practice, Gold, replacement textures, menus, and fast-forward.
