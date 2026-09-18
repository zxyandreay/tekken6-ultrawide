> Historical later-phase checkpoint recovered from the original HUD research history (snapshot d5e6c73). This copy is preserved on main for v1.2.0 provenance.

# HUD research checkpoint: EXP6 dual-stage mode-font build

Date: 2026-09-17
Branch: `research/hud-correction`
Game: Tekken 6 USA (`ULUS10466`)
Target presentation: fixed 20:9 HUD correction on PPSSPP

## Checkpoint decision

EXP6 is the current accepted research checkpoint.

It combines the established v9.2 fight-HUD corrections with the mode-specific fixes that were split across EXP2, EXP3, and EXP4:

- Practice `∞` timer centered correctly;
- Practice `DAMAGE / HIT COMBO / DAMAGE` visibly de-stretched;
- Gold Rush target labels visibly de-stretched;
- Gold Rush target labels retain the correct EXP4-style placement;
- previously validated normal battle-HUD corrections remain intact.

The accepted device-tested artifact is:

```text
Tekken6-HUD-v9.3-ModeCompact-EXP6
PRX SHA-256: 38c9b2ebc86201263300d9a0503b7bd0b382e287c9a7010eef53d6834f400f9f
ZIP SHA-256: f2f0b3a75559adc9c68bb8a70dde6fa7891573145fd5d2b4a4ac40ab784b5efd
```

EXP6 was built directly from the device-proven EXP4 PRX:

```text
EXP4 PRX SHA-256:
5994089dfa90df4a11587be1d1168631434ec340841f9864361de4c9bd7846cd
```

The resident footprint remains unchanged:

```text
one PT_LOAD segment
p_filesz = 0x0EB0
p_memsz  = 0x0EB0
file size = 5626 bytes
```

No second LOAD segment is introduced.

The `0x0EB0` resident-memory ceiling remains mandatory because the earlier controlled A/B that changed only `PT_LOAD.p_memsz` from `0x0EB0` to `0x12D0` reproduced the custom Tekken font/text replacement-texture regression.

## Device validation result

EXP6 was tested on the official PPSSPP release after the earlier dev/debug-build crash issue had been isolated.

User device result:

```text
EXP6 worked.
All intended HUD fixes were applied.
```

The important visual result is that EXP6 successfully combines behavior that had previously been separated across EXP3 and EXP4:

```text
Practice infinity placement              correct
Practice DAMAGE / HIT COMBO text         visibly de-stretched
Gold Rush intended labels                visibly de-stretched
Gold Rush label placement                correct
normal battle HUD corrections            retained
```

This resolves the final known visual tradeoff between EXP3 and EXP4.

## Why EXP6 was needed

### EXP2

EXP2 moved the mode-font correction upstream to Tekken's horizontal-scale path and visibly de-stretched the Practice/Gold target text.

However, its Practice infinity integration still used the wrong placement/stage assumption.

Practical result:

```text
mode-text de-stretch     good
Practice infinity        wrong
```

### EXP3

EXP3 retained the early scale behavior and corrected the Practice infinity placement.

It therefore gave the strongest evidence that applying the 80% horizontal scale early was required for a true visible glyph de-stretch.

However, the Gold Rush heading/label placement was wrong.

Practical result:

```text
mode-text de-stretch     good
Practice infinity        good
Gold placement           wrong
```

### EXP4

EXP4 moved the mode-font intervention later in Tekken's scale path to synchronize packed/live scale state and produced the best overall placement and stability.

On official PPSSPP, EXP4 was stable and its Practice infinity and Gold placement were correct.

However, direct visual comparison against EXP2/EXP3 showed that the Practice/Gold target text still looked horizontally stretched. The later intervention did not reproduce all geometry/spacing calculations that Tekken had already derived from the original 100% scale.

Practical result:

```text
Practice infinity        good
Gold placement           good
stability                good
visible de-stretch       incomplete / absent
```

### EXP5

EXP5 deliberately removed mode-font correction and retained only the Practice infinity fix.

It remains an important simplified fallback because it proved a stable minimal mode-specific configuration within the `0x0EB0` footprint.

It is no longer the primary checkpoint because EXP6 has now restored the intended font corrections without sacrificing the successful EXP4 placement.

## EXP6 architecture

EXP6 is based on EXP4 and uses a dual-stage mode-font correction.

### Stage 1: early horizontal scale

Hook point:

```text
0x08970A90
```

This is the earlier horizontal-scale load path used successfully by EXP2/EXP3.

For the already researched battle-text owner only, EXP6 changes the horizontal scale from:

```text
100 -> 80
```

before Tekken performs the downstream glyph geometry calculations.

This is the key difference that restores the visible de-stretch.

The compact ownership gate remains narrow:

```text
saved caller return = 0x08973C84
saved a1            = 1
original X scale    = 100
```

Practice target:

```text
x < 200
104 <= y < 140
```

Gold target glyph rows used by the compact implementation:

```text
REWARD family:
  y = 25
  270 <= x < 380

ATTACK VARIATION family:
  y = 73
  x >= 128
```

Gold X is deliberately not shifted at this early stage.

### Stage 2: late packed-scale synchronization

Hook point:

```text
0x08970B24
```

The same target glyphs later pass through a compact synchronization helper.

For those target glyphs only:

```text
packed horizontal scale: 100 -> 80
Practice authored X:      unchanged
Gold authored X:          +120
```

For Gold, applying the +120 source-X offset before the 80% renderer scale gives the intended RIGHT-anchor transform:

```text
0.8 * (x + 120)
= 0.8x + 96
```

This preserves the good Gold placement seen in EXP4 while retaining the early de-stretch behavior seen in EXP3.

The cached horizontal factor is not multiplied by another 0.8 at the late stage. The early scale change already causes Tekken's stock path to derive the required horizontal factor; applying another multiplier would double-scale the target text.

## Practice infinity

The Practice infinity correction is unchanged from the successful EXP3/EXP4 behavior.

Device-proven post-transform signature:

```text
x = 166
y = 6
width = 51
height = 32
```

Correction:

```text
x = 214
```

Width and height remain unchanged.

This keeps the Practice `∞` centered around the logical screen center without affecting the ordinary decimal timer.

## Accepted HUD scope

The following behavior is now considered solved and frozen unless a regression is demonstrated:

- automatic 3D ultrawide projection;
- long P1/P2 HP shell span;
- both HP fill layers at full and partial health;
- side strips / lightning family;
- rank badges;
- persistent and immediate round-win orb placement;
- P1/P2 winner glow;
- large center decimal round timer;
- P1/P2 character-name rectangle anchoring;
- Practice-mode `∞` centering;
- Practice `DAMAGE / HIT COMBO / DAMAGE` horizontal de-stretch;
- Gold Rush `REWARD:` target label horizontal de-stretch and right anchoring;
- Gold Rush `ATTACK VARIATION` horizontal de-stretch and right anchoring.

Gold reward values, currency markers, and floating `+gold` rows remain outside the targeted correction unless a later device finding demonstrates that they need their own owner-specific rule.

## PPSSPP dev-build finding remains important

Several earlier crashes were observed under a PPSSPP development/debug build in the `v1.20.4-1783-g03bb3e20fe` range while release camera CWCheats were enabled.

Those crashes were initially misattributed to the compact HUD hooks.

Switching back to the current official Google Play PPSSPP release restored stability, including with EXP4/EXP5 and the normal release camera cheats.

Therefore:

- dev/debug builds are useful for remote-debugger probes;
- official PPSSPP releases are the acceptance environment;
- a dev-build-only crash is not sufficient evidence of a plugin regression;
- every future accepted checkpoint must record the PPSSPP build/channel used for validation.

## Camera-cheat compatibility

The release camera presets remain separate CWCheats and are part of the expected regression environment:

```text
Camera - Original (Default)  -> 0x3F80
Camera - Slightly Wider      -> 0x3F81
Camera - Wider               -> 0x3F82
Camera - Widest              -> 0x3F83
```

At least one non-default camera preset should remain enabled during future checkpoint regression testing.

## EXP5 fallback checkpoint

`CHECKPOINT_INFINITY_ONLY.md` remains useful as the last simplified fallback checkpoint.

If later mode-font work regresses stability, layout, custom textures, or camera compatibility, EXP5 provides a known minimal recovery target:

```text
EXP5 PRX SHA-256:
44c80a417e3602d4e9b8553cdcf89be9348e208582c28c0e3b7a9dcfd8ee3ea2
```

However, EXP5 is superseded as the primary research checkpoint by EXP6 because EXP6 now reproduces the full intended mode-specific visual correction.

## Source versus binary status

The authoritative checkpoint is the device-tested EXP6 binary artifact.

The readable source tree is not yet claimed to be byte-equivalent to EXP6. The final EXP6 layout is a compact/hand-integrated binary architecture that combines two renderer stages while preserving the `0x0EB0` resident footprint.

Before calling a source-linked PRX equivalent to EXP6, it must reproduce:

1. the early `0x08970A90` target-scale behavior;
2. the late `0x08970B24` packed-scale/Gold-X synchronization;
3. the Practice infinity correction;
4. the exact `0x0EB0` memory ceiling;
5. custom replacement texture behavior;
6. release camera-cheat compatibility;
7. all established battle-HUD fixes;
8. official-PPSSPP stability.

Do not increase `p_memsz` merely to make a readable source implementation fit.

## Required regression protocol

Any future checkpoint candidate should be tested from a cold official PPSSPP start.

Minimum sequence:

1. Fully close PPSSPP before replacing the PRX.
2. Use an official PPSSPP release for acceptance testing.
3. Confirm custom replacement font/text/button textures still load.
4. Confirm Arcade/Story/Ghost battle HUD remains correct.
5. Confirm HP shells/fills, ranks, side strips, round orbs, winner glow, timer, and character names.
6. Practice: confirm centered `∞`.
7. Practice: confirm `DAMAGE / HIT COMBO / DAMAGE` is visibly de-stretched and remains correctly positioned during repeated hits.
8. Gold Rush: confirm `REWARD:` and `ATTACK VARIATION` are visibly de-stretched and correctly positioned.
9. Confirm intentionally untargeted Gold numeric/currency rows remain acceptable.
10. Enable at least one non-default release camera preset and repeat a normal battle plus Practice.
11. Confirm custom textures remain correct with camera cheats enabled.
12. Test fast-forward and normal emulator controls.
13. Verify one LOAD segment and `PT_LOAD.p_memsz <= 0x0EB0`.

## Checkpoint policy

From this point forward:

- treat this fixed-ratio behavior as the frozen comparison checkpoint for subsequent experiments;
- keep the preceding simplified build as a fallback checkpoint;
- do not modify `main` or published `v1.1.0` while this remains research;
- keep HUD work on `research/hud-correction`;
- do not use GitHub Actions for this research session;
- preserve the `0x0EB0` resident-memory ceiling;
- prefer narrow owner/state predicates over global text-renderer changes;
- validate future changes against official PPSSPP before changing checkpoint status.

## Checkpoint versus final release

EXP6 is suitable as the **final research checkpoint from this point forward** based on current device testing.

It should not yet be labeled a final public release solely from this binary result. Before promoting the work out of the research branch, the remaining release-engineering task is to reconcile the readable source/build process with the device-proven EXP6 binary without increasing the PRX footprint or changing behavior.
