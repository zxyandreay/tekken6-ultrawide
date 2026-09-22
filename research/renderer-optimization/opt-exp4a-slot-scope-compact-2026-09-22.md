# OPT-EXP4A — compact slot-scope wrapper — accepted checkpoint — 2026-09-22

## Status

Accepted on device.

Artifact:

```text
Tekken6Ultrawide-OPT-EXP4A-SlotScopeCompact.prx

SHA-256:
6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

This supersedes OPT-EXP3D-A as the working optimization baseline while preserving the exact accepted winner-glow implementation from EXP3D-A.

## Device validation

The complete regression sweep passed with no observed breakage.

Confirmed working:

- cold boot/startup;
- gameplay HUD corrections;
- HP shell and colored fill;
- ranks and side strips;
- character-name anchoring;
- round timer;
- persistent round markers;
- P1 first-win spinning winner glow;
- P1 later-win spinning winner glow;
- P2 first-win spinning winner glow;
- P2 later-win spinning winner glow;
- Practice HUD/font correction;
- Gold Rush HUD/font correction;
- custom replacement textures/fonts;
- fast-forward.

No winner-glow code was modified by EXP4A.

## Optimization performed

Accepted pre-EXP4A slot-scope wrapper:

```text
0x05A0 .. 0x0647
168 bytes
```

The original wrapper preserved a0-a3, t0-t3 and f12 even though it did not modify those values before calling stock `0x0892D9F8`.

The compact wrapper preserves only state that actually needs to survive across the stock call:

- incoming ra;
- original a1 for scope close-out;
- scope-counter pointer on the 0xEF path.

It preserves the accepted wrapper's stock-call and wrapper-return boundary behavior, including t4/t5 values.

## Relocation cleanup

The removed wrapper contained two module-local HI16/LO16 address-materialization pairs.

The compact wrapper derives the scope-counter pointer through a local BAL-relative value.

The four obsolete relocation records are disabled as R_MIPS_NONE.

## Accepted hard-free result

New detached zero tail:

```text
0x0604 .. 0x0647
72 bytes
```

Existing accepted detached zero block:

```text
0x0C00 .. 0x0C3F
64 bytes
```

Accepted general-purpose hard-free capacity:

```text
72 + 64 = 136 bytes
```

This is now device-validated capacity.

## Frozen subsystems

Winner-glow remains frozen exactly as accepted in EXP3D-A.

Do not alter for unrelated optimization:

```text
0x08AC9C38 winner-glow callsite
0x08AE94A4 original converter
corrected packed 64x64 UV identity
winner-row Y gate
full P1/P2 round-family X gate
dynamic AutoHUD CENTER transform
source-X save/transform/restore sequence
```

## Recommendation after acceptance

EXP4A is a suitable release baseline.

Further optimization is no longer required for the next maintenance release.

Any additional optimizer experiment should branch from this exact hash and should not delay a release unless it fixes a demonstrated user-visible problem.

No GitHub Actions are used.
