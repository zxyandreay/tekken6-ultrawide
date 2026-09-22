# Winner-glow root cause: compact UV predicate mismatch — 2026-09-22

## Revalidation result

Device retest established:

- historical RoundWin v7 is correct;
- later EXP2S3 / EXP3A are not correct;
- EXP3A with only v7's fixed 0.8*x+48 math is still wrong;
- that math-only diagnostic also makes the visible orb glows appear static rather than restoring the spinning halo.

Therefore the failure is not simply the dynamic scale/center constants.

## Concrete binary bug

Historical RoundWin v7 identifies the spinning winner glow using exact UV corners:

```text
(0,0)
(0,64)
(64,0)
(64,64)
```

The later compact AutoHUD hook replaced the eight halfword checks with packed 32-bit checks.

Relevant compact sequence:

```text
0x0D04  lui   t1,0x0040     -> 0x00400000
...
0x0D10  li    t1,0x0040     -> 0x00000040   [destroys high half]
...
0x0D1C  ori   t1,t1,0x0040  -> still 0x00000040
0x0D20  bne   t0,t1,...
```

The intended fourth packed UV pair is:

```text
0x00400040
```

but the compact code compares against:

```text
0x00000040
```

Therefore the AutoHUD-era hook is not matching the same 64x64 rotating quad as RoundWin v7.

This explains why restoring only v7's transform constants does not fix the spinner: the transform is being applied to the wrong related layer.

## Zero-cost predicate repair

No extra instructions are required.

Instead of overwriting t1 at 0x0D10:

```text
li t1,64
```

use:

```text
addiu t0,t0,-64
```

and replace the following comparison with:

```text
bnez t0,fallback
```

This checks the third packed corner against 64 while preserving:

```text
t1 = 0x00400000
```

Then the existing:

```text
ori t1,t1,0x40
```

correctly forms:

```text
0x00400040
```

for the fourth (64,64) corner.

## Ownership gate

EXP2S3 had also bypassed the compact P1/P2 X-center gate.

That experiment is now known not to fix the halo.

The next candidate restores the pre-S3 X ownership gate so the repaired UV identity does not broaden the hook to unrelated top-row 64x64 quads.

## Candidates

### OPT-EXP3C-A — dynamic AutoHUD

- repaired exact packed UV identity;
- restored P1/P2 X ownership;
- keeps current AutoHUD dynamic CENTER math.

This is the preferred production direction because it retains auto aspect ratio.

### OPT-EXP3C-B — historical v7 math control

Same predicate/ownership repair, but:

```text
scale = 0.8
shift = 48
```

Use only if A still has a positioning problem.

## Permanent regression rule

The winner-glow acceptance test must explicitly verify the animated spinner, not only whether an orb has some glow.

Required states:

- P1 first earned win;
- P2 first earned win;
- later earned slot where practical;
- spinner remains visibly rotating;
- spinner center follows the newly lit orb;
- persistent next-round orb remains aligned.

A static glow at the expected row is not sufficient.

No GitHub Actions are used.
