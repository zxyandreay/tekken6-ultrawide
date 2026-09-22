# OPT-EXP3B Compact — test candidate

## Base

Device-accepted:

```text
OPT-EXP3A-OneHookScratch
SHA-256:
46063c6097e3dfaa51aafd077e0e5c65f02487bdbe420f8884f2a292edf8cf1f
```

## Goal

Convert the validated one-hook font architecture into actual internal compaction without changing its behavior.

No GitHub Actions are used.

## Compaction

The EXP3A helper is exactly 52 bytes:

```text
0x0C00 .. 0x0C30
```

The proven compressed-table tail is exactly 52 bytes:

```text
0x0AC4 .. 0x0AF7
```

EXP3B relocates the helper into that table tail.

Only three early-font branches need retargeting:

```text
0x0E74
0x0E8C
0x0E9C
```

The helper's two internal branches are regenerated for its new address.

The helper's jump back to stock Tekken:

```text
0x08970A98
```

is unchanged.

## Newly zeroed regions

After relocation:

```text
0x0C00 .. 0x0C3F = 64 zero bytes
```

The previously verified-unreachable old winner-glow X classifier is also physically cleared:

```text
0x0D40 .. 0x0D57 = 24 zero bytes
```

Candidate physically hard-free total:

```text
64 + 24 = 88 bytes
```

The former 52-byte table cave is no longer free because it now stores the live helper.

Relative to the accepted EXP2S3/EXP3A hard-free count of 52 bytes, the candidate increases physically zero detached capacity by:

```text
88 - 52 = 36 bytes
```

Relative to the broader previous 76-byte hard-free-plus-unreachable opportunity, the net increase in total reclaimable capacity is:

```text
88 - 76 = 12 bytes
```

Do not call the 88-byte figure accepted until device validation passes.

## Safety audit

Before building:

- no alternate branch/J/JAL/pointer/relocation entry existed into 0x0D40..0x0D57;
- the only external entries into the old C00 helper were the three known early-font branches;
- those three branches are retargeted;
- no relocation entry exists in the old helper or destination cave;
- the destination cave lies after the active compressed-table end and is not visited by any table walker.

## Layout

```text
file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Device test

Because this should be semantic-equivalent compaction, repeat the highest-risk areas first:

1. Practice DAMAGE / HIT COMBO / infinity;
2. Gold REWARD / ATTACK VARIATION;
3. P1/P2 earned round + spinning winner halo;
4. full/partial/low HP;
5. replacement textures/custom fonts;
6. fast-forward;
7. main menu, pause, character select;
8. Arcade / Story / Ghost.

If all match EXP3A, the 88-byte hard-free candidate can be promoted to accepted capacity.
