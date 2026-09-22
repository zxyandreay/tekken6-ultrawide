# OPT-EXP3D-A accepted optimization checkpoint — 2026-09-22

## Status

Accepted on device.

Artifact:

```text
Tekken6Ultrawide-OPT-EXP3D-A-GlowFullSlotRange.prx
SHA-256:
d8afe941dc3198107a460511d78fa2d8acde6f709020a7b351605e6a6fdfe17f

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

This supersedes OPT-EXP3A/EXP3B/EXP3C as the working optimization baseline.

## Accepted optimization chain

### OPT-EXP1
Downstream HP consolidation.

### OPT-EXP2S2
13-entry startup slot table compressed from 12-byte records to 8-byte records, with all three walkers corrected to +8 stride.

### OPT-EXP3A
Practice/Gold dynamic text correction reduced from two dynamic game-hook entries to one, using bounded stack scratch rather than persistent s6 mutation.

### OPT-EXP3B
The validated 52-byte one-hook helper was relocated into the former 52-byte slot-table tail, leaving the old 64-byte helper allocation detached and zero.

### OPT-EXP3C
Corrected the compact winner-glow packed 64x64 UV identity so the hook once again owns the actual rotating quad.

### OPT-EXP3D-A
Generalized winner-glow X ownership from historical first-win-only center families to the full documented round-win slot family.

## Device result

Current accepted behavior includes:

- startup/loading;
- HP shell/fill;
- Practice text;
- Gold Rush text;
- character-name side anchoring;
- first and later P1/P2 round-win spinner placement;
- spinner animation;
- persistent round markers;
- replacement textures/fonts;
- fast-forward behavior observed in the current optimization line.

## Diagnostic-only artifacts

Do not promote as production baselines:

- EXP3C-B fixed-v7-math control;
- EXP3D-B UV/Y-only control.

EXP3D-B passed the tested round-win sequence, but its ownership predicate is broader than necessary.

## Frozen winner-glow rule

The EXP3D-A winner-glow path is frozen.

Do not reclaim, rewrite, or repack its interior instructions for unrelated optimization work.

## Current hard-free capacity

The accepted general-purpose detached zero region is:

```text
0x0C00 .. 0x0C3F
64 bytes
```

The former 52-byte table tail is no longer free; it contains the live one-hook font helper.

The winner-glow X classifier is no longer free; it contains the accepted full-slot ownership logic.

The startup NOP pair at 0x03F0..0x03F7 remains startup-inline opportunity only and is not a general code cave.

## Next optimization policy

Continue only with isolated changes that:

- do not touch the frozen winner-glow path;
- do not enlarge the one-PT_LOAD 0x0EB0 resident image;
- produce a measurable structural simplification or additional hard-free capacity;
- preserve a directly testable rollback to this exact SHA-256.

No GitHub Actions are used.
