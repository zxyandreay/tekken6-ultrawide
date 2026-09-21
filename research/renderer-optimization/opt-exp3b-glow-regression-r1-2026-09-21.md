# OPT-EXP3B winner-glow regression and R1 isolate — 2026-09-21

## Device result

OPT-EXP3B is rejected as an accepted checkpoint.

Observed:

- font optimization/compaction otherwise works;
- HP and other HUD behavior appear correct;
- winner/earned-round spinning glow is again on the wrong orb.

This narrows the regression to the two compaction actions that did not exist in accepted EXP3A:

1. relocating the OneHookScratch helper into 0x0AC4..0x0AF7;
2. physically zeroing 0x0D40..0x0D57 in the winner-glow hook tail.

## Important correction to the audit methodology

The static audit previously proved there were no *direct* entries into
0x0D40..0x0D57 through:

- PC-relative branches;
- direct J/JAL instructions;
- raw embedded pointers;
- relocation records.

That is insufficient to prove a MIPS block is dynamically unreachable.

It does not rule out:

- indirect JR/JALR control flow;
- computed return-address entry;
- runtime/self-patched entry;
- other execution paths not represented as a direct static xref.

Because device behavior regressed only after this block was physically cleared,
the region must no longer be considered safely reclaimable without a dynamic
execution proof.

## EXP3B-R1 design

EXP3B-R1 is a strict A/B isolate.

It keeps the EXP3B helper relocation and 64-byte compaction intact.

It restores only:

```text
0x0D40 .. 0x0D57
```

byte-for-byte from device-accepted EXP3A.

Therefore:

- if R1 fixes the halo, the restored winner-glow sub-block is causal;
- if R1 still fails, the helper relocation/table-tail execution placement is causal.

No other renderer logic changes.

## Space accounting during R1

Do not count the restored glow block as free.

The only candidate hard-free region carried forward is:

```text
0x0C00 .. 0x0C3F = 64 bytes
```

This is still unaccepted until R1 passes device testing.

## Permanent rule proposed if R1 passes

Do not reclaim any interior block of a live hand-integrated render hook based
only on direct-xref analysis.

For future optimization, require either:

- dynamic execution tracing proving the candidate block is never entered across
  the relevant runtime states; or
- relocation of an entire independently callable helper whose callers are fully
  enumerated and device-tested.

This rule is specifically intended to prevent another winner-glow regression.

No GitHub Actions are used.
