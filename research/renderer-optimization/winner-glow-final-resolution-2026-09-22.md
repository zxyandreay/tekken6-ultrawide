# Winner-glow final resolution — 2026-09-22

## Status

Solved and device-validated for the complete tested round-win sequence.

Authoritative optimized baseline:

```text
OPT-EXP3D-A — GlowFullSlotRange
SHA-256:
d8afe941dc3198107a460511d78fa2d8acde6f709020a7b351605e6a6fdfe17f

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Device validation

Confirmed on device:

- P1 first earned win: spinner rotates on the newly lit orb;
- P1 later earned wins: spinner follows the newly lit orb;
- P2 first earned win: spinner rotates on the newly lit orb;
- P2 later earned wins: spinner follows the newly lit orb;
- persistent next-round round markers remain aligned;
- the rest of the tested HUD remains correct.

OPT-EXP3D-B (UV/Y-only) also passed first and later wins, but remains diagnostic-only because it is broader than necessary.

## Final root cause

The long-lived winner-glow problem had two independent causes.

### 1. AutoHUD compact UV predicate bug

Historical RoundWin v7 identified the rotating winner-glow quad with exact 64x64 UV corners:

```text
(0,0)
(0,64)
(64,0)
(64,64)
```

The compact AutoHUD implementation accidentally destroyed the high half of the packed fourth-corner comparison.

It effectively compared:

```text
0x00000040
```

instead of:

```text
0x00400040
```

so the later hook did not reliably identify the same rotating quad as v7.

EXP3C repaired that packed UV predicate without adding code.

### 2. Historical v7 validation was first-slot-only

The recovered RoundWin-v7 documentation described the subsystem as solved for P1/P2, but its actual capture protocol tested only controlled first wins.

Its X ownership predicate admitted only:

```text
P1 x0+x3 approximately 394..398
P2 x0+x3 approximately 559..563
```

Those are first-win center families.

The repository already documented a wider ordinary late earned-orb family:

```text
P1 authored X 150..206
P2 authored X 273..310
```

EXP3D-A generalized the winner-glow X ownership gate to that full round family while retaining the corrected rotating-quad identity.

That fixed later wins without removing the ownership check entirely.

## Final production predicate

The accepted winner-glow path requires:

- vertex count a3 == 4;
- exact corrected packed 64x64 UV sequence;
- winner-row Y family;
- X ownership inside the full known P1/P2 round-win family.

When matched:

- only source X coordinates are temporarily transformed;
- current AutoHUD dynamic CENTER math is used;
- Tekken's original converter is called;
- original source X values are restored.

Preserved stock behavior includes:

- Y;
- UV;
- color/alpha;
- Z;
- rotation/skew;
- animation size;
- animation lifetime.

## Frozen subsystem rule

Do not modify the winner-glow hook as part of unrelated optimization work.

The following are now frozen:

```text
callsite      0x08AC9C38
converter     0x08AE94A4
UV predicate  corrected 64x64 packed identity
Y ownership   winner-row gate
X ownership   EXP3D-A full round-family gate
transform     AutoHUD dynamic CENTER
source X      save -> transform -> converter -> restore
```

Any future change requires a dedicated round-win regression test.

## Permanent acceptance matrix

A winner-glow change is not accepted unless all of these are explicitly checked:

```text
P1 first win
P1 later win
P2 first win
P2 later win
spinner visibly rotates
spinner follows newly lit orb
persistent next-round marker remains aligned
no unrelated top-HUD effect moves
```

A first-win-only pass is insufficient.

A static glow is insufficient.

## Historical correction

The old RoundWin-v7 result remains valuable: it correctly identified the rotating quad and fixed first-win placement at 20:9.

However, it did not prove later-slot coverage.

The phrase "round-win subsystem complete" in the recovered historical document should therefore be read as a first-win-era conclusion, not full slot-sequence validation.

No GitHub Actions are used.
