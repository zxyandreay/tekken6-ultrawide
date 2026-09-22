# OPT-EXP1 implementation — 2026-09-21

## Purpose

This is the first mutation test from the downstream HP A/B research.

It changes only the HP-fill architecture from released v1.2.0. It does not change the automatic 3D aspect path, slot/rectangle hooks, timer, winner effects, Practice/Gold text logic, or the existing rank/side-strip transforms.

## Base

Released v1.2.0 PRX:

```text
SHA-256 311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75
file size 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Change

The released plugin installed upstream HP gauge hooks at:

```text
0x0892C1F0
0x0892C26C
```

which redirected through the module-relative wrapper at `0x07E4`.

OPT-EXP1 no longer installs those two upstream hooks, so Tekken's gauge path remains stock.

The now-dead module-relative `0x07E4..0x084C` region is reused as a packet-local HP handler reached from the existing downstream shared sprite wrapper.

The existing hooks at:

```text
0x0892D56C
0x0892D5B0
```

remain installed.

The shared wrapper first recognizes `Y=21.0f`, then the new handler verifies:

```text
Z = 1000.0f
descriptor side IDs = 6..9, 16-byte aligned
resource = 0x0D for IDs 6/7
resource = 0x0E for IDs 8/9
```

Invalid `Y=21` packets fall through unchanged to the stock submitter.

For valid HP packets it applies the exact released transform proved by the A/B captures:

```text
x'     = x - orientation * hp_shift
width' = width * hp_scale
```

using the same runtime `hp_shift` and `hp_scale` values already produced by the v1.2.0 initializer.

## Relocation handling

The old upstream wrapper used module-relative HI16/LO16 relocations at:

```text
0x07F4
0x07F8
```

Those two relocation entries are changed to `R_MIPS_NONE` in OPT-EXP1 because the replacement instructions are absolute/game-state operations. All other PRX relocation entries remain unchanged.

## Static build result

The generated test PRX is:

```text
SHA-256 91f84acad1047b80b474fe1b2f6df12888c9312fb0b9be34cfae45ff095495fa
file size 5626 bytes
one PT_LOAD
p_filesz = 0x0EB0
p_memsz  = 0x0EB0
```

The builder is:

```text
research/tools/build_opt_exp1.py
```

It refuses to build unless the authoritative released v1.2.0 PRX hash, expected patch-site words, relocation entries, and resident-layout invariant all match.

## Required device test

Cold-boot PPSSPP before testing. Do not hot-swap over a running released v1.2.0 session because the previous game-memory hooks may remain until restart.

Test in this order:

1. full HP for both players;
2. partial HP for P1 and P2 independently;
3. very low HP for both sides;
4. both HP resource layers remain visible/aligned;
5. rank badges;
6. translucent/lightning side strips;
7. timer and round markers;
8. winner orb/glow;
9. character-name placement;
10. Practice infinity and DAMAGE/HIT COMBO text;
11. Gold Rush REWARD and ATTACK VARIATION;
12. Arcade, Story, and Ghost Battle;
13. replacement textures/custom fonts;
14. main menu/pause/character select for regressions;
15. fast-forward/input behavior.

## Interpretation

If HP behavior matches released v1.2.0 and the regression sweep passes, the upstream gauge-owner hook is no longer architecturally necessary.

That would make the downstream shared dispatcher the new HP ownership boundary for the next optimization step.

If the build fails only in one HP state, preserve this binary and trace the first packet difference rather than changing multiple subsystems at once.
