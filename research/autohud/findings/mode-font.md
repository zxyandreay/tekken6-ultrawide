# Practice and Gold Rush HUD

## Current checkpoint status

Mode-specific HUD research started after the normal Arcade/Story/Ghost battle HUD, center timer, winner effects, and character-name anchoring were already validated.

EXP6 is now the accepted mode-HUD checkpoint.

```text
Practice infinity indicator        ACCEPTED / DEVICE VALIDATED
Practice damage/combo readout      ACCEPTED / DEVICE VALIDATED
Gold Rush static target labels     ACCEPTED / DEVICE VALIDATED
Gold Rush money strings            STOCK / NOT TARGETED
EXP6 integrated PRX                ACCEPTED / DEVICE VALIDATED
PT_LOAD p_memsz                     0x0EB0
```

Checkpoint hashes, architecture, and regression policy: [`checkpoint-exp6.md`](../archive/exp6-checkpoint.md).

The simplified EXP5 fallback is recorded in [`test-builds.md`](../archive/test-builds.md).

The normal Arcade/Story/Ghost battle-HUD fixes remain frozen unless a regression is demonstrated.

## Practice infinity

The Practice infinite-time (`∞`) indicator is not rendered by the ordinary decimal countdown path.

The ordinary timer digits are owned by:

```text
0x08929AF8
0x08929B44
```

A direct A/B against those calls did not restore the Practice indicator, proving that Practice infinity is a separate sprite/rectangle path.

The stable capture isolated the post-transform packet as:

```text
x = 166
y = 6
width = 51
height = 32
```

The device-proven correction changes only X:

```text
166 -> 214
```

Width and height remain unchanged.

This keeps the Practice infinity visual center near logical screen center `x ~= 240` while leaving the normal decimal timer untouched.

EXP3 first demonstrated the corrected placement; EXP4 and EXP6 retain it.

## Practice statistics panel

The left Practice `DAMAGE / HIT COMBO / DAMAGE` readout belongs to the shared `0x80011E` font family.

Second-stage glyph analysis separated the relevant rows:

```text
mode header:  y=2..14, far right
stats rows:   y=104..116
              y=116..128
              y=127..139
```

The correction is:

```text
x < 200
104 <= y < 140
horizontal scale = 80%
LEFT anchored
```

EXP2/EXP3 visibly proved that changing Tekken's horizontal scale early produces the correct de-stretch.

The important renderer-stage finding is that changing only the later packed/live scale state is not equivalent to changing the earlier source scale. EXP4 demonstrated this: overall placement was good, but direct device comparison showed that the Practice target text still looked horizontally stretched.

EXP6 therefore restores the early scale change before Tekken derives downstream glyph geometry.

## Gold Rush targets

Gold Rush uses the same broad font family but contains multiple independent text groups with different semantics.

Captured families included:

```text
mode header:            y=2..14, far right
REWARD:                 around y=16..28
reward amount / G:      separate right-side string
ATTACK VARIATION:       around y=64..76
floating +gold rows:    around y=136..160
```

The accepted target scope remains narrow:

```text
REWARD:
  de-stretch / RIGHT anchor

ATTACK VARIATION:
  de-stretch / RIGHT anchor

reward amount / G:
  stock / no transform

floating +gold rows:
  stock / no transform
```

The RIGHT transform is:

```text
x' = trunc(4*x/5) + 96
```

which is equivalent to:

```text
0.8 * (x + 120)
```

## EXP2 -> EXP6 progression

### EXP2

EXP2 moved the target font correction to the earlier horizontal-scale path around:

```text
0x08970A90
```

For target glyphs, it changed horizontal scale:

```text
100 -> 80
```

This visibly de-stretched the Practice/Gold target text.

However, Practice infinity placement was still wrong.

### EXP3

EXP3 kept the early 80% scale and corrected the Practice infinity placement.

Device result:

```text
Practice target text     de-stretched correctly
Practice infinity        correct
Gold target text         de-stretched
Gold placement           wrong
```

The Gold positioning issue showed that applying both scale and source-X adjustment too early did not preserve the desired final anchor behavior.

### EXP4

EXP4 moved the correction later, around:

```text
0x08970B24
```

The goal was to keep Tekken's packed/live scale state internally synchronized and preserve Gold placement.

On official PPSSPP, EXP4 was stable and produced good Practice-infinity and Gold placement behavior.

However, visual A/B comparison against EXP2/EXP3 showed that the Practice/Gold target text still looked stretched. The later correction occurred after some glyph geometry/spacing had already been derived from the original 100% scale.

Therefore EXP4 solved placement/state consistency but not the complete visible de-stretch.

### EXP5

EXP5 removed the mode-font correction and kept only the Practice infinity correction.

It provided a minimal stable fallback for further font experiments.

### EXP6 — accepted solution

EXP6 starts from the successful EXP4 binary and combines two narrowly filtered stages.

#### Stage 1: early true de-stretch

Hook point:

```text
0x08970A90
```

For the researched battle-text owner and target rows only:

```text
horizontal scale: 100 -> 80
```

Compact ownership/state gate:

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

Gold target rows in the compact implementation:

```text
REWARD family:
  y = 25
  270 <= x < 380

ATTACK VARIATION family:
  y = 73
  x >= 128
```

Gold X is not shifted here. This lets Tekken derive glyph geometry using the correct 80% horizontal scale first.

#### Stage 2: late synchronization and Gold placement

Hook point:

```text
0x08970B24
```

The same target glyphs are synchronized later:

```text
packed horizontal scale: 100 -> 80
Practice authored X:      unchanged
Gold authored X:          +120
```

For Gold:

```text
0.8 * (x + 120) = 0.8x + 96
```

This retains the good EXP4-style Gold placement while preserving the real EXP3-style de-stretch.

No second 0.8 cached-factor multiplication is applied at the late stage. The early scale change already causes Tekken's stock path to derive the necessary horizontal factor; multiplying again would double-scale the glyphs.

## EXP6 device result

EXP6 was validated on the official PPSSPP release.

Test result:

```text
EXP6 worked.
All intended fixes were applied.
```

The visually important combination is now achieved:

```text
Practice infinity                   correct
Practice DAMAGE/HIT COMBO text      visibly de-stretched
Gold target labels                  visibly de-stretched
Gold target placement               correct
normal battle-HUD fixes             unchanged
```

This makes EXP6 the current accepted mode-HUD solution.

## PPSSPP dev-build finding

Earlier EXP2-EXP4 crash observations were confounded by the PPSSPP development/debug build used for remote-debugger work.

A dev build in the `v1.20.4-1783-g03bb3e20fe` range could crash when release camera CWCheats were enabled with otherwise known-good HUD builds.

Switching to the current official Google Play PPSSPP release restored stability.

Therefore:

- dev/debug builds may be used for probes;
- official PPSSPP releases are the acceptance environment;
- a dev-build-only crash must not automatically be classified as a plugin regression;
- emulator build/channel must be recorded with future device results.

## PRX footprint constraint

Accepted builds must preserve the custom-texture-safe module ceiling:

```text
one PT_LOAD segment
p_filesz = 0x0EB0
p_memsz  = 0x0EB0
```

A controlled A/B that changed only `PT_LOAD.p_memsz` from `0x0EB0` to `0x12D0` reproduced the custom Tekken font/text replacement-texture regression.

EXP6 remains within the known-safe footprint.

Do not add a second LOAD segment or enlarge the original segment merely to simplify source integration.

## Source status

The device-proven EXP6 binary is authoritative.

The readable source tree is not yet claimed to reproduce the exact EXP6 binary layout. A future source cleanup must reproduce both renderer stages and the Practice infinity rule while remaining within `0x0EB0`.

A source-linked candidate must not be called equivalent to EXP6 until it passes:

- early `0x08970A90` scale behavior;
- late `0x08970B24` packed-scale/Gold-X synchronization;
- Practice infinity centering;
- custom replacement texture validation;
- camera CWCheat compatibility;
- all frozen normal battle-HUD checks;
- official-PPSSPP stability;
- `PT_LOAD.p_memsz <= 0x0EB0`.

## Safety rules

- Keep the validated normal Arcade/Story/Ghost HUD frozen.
- Keep the ordinary decimal timer correction frozen.
- Keep the Practice `∞` correction frozen.
- Keep the EXP6 Practice stats de-stretch frozen.
- Keep the EXP6 Gold `REWARD:` / `ATTACK VARIATION` correction frozen.
- Leave Gold numeric/currency/floating rows stock unless separately researched.
- Never globally transform the shared font renderer by screen row alone.
- Preserve PPSSPP replacement-texture behavior and emulator controls.
- Treat `PT_LOAD.p_memsz = 0x0EB0` as a hard compatibility ceiling until disproven.
- Use official PPSSPP releases for acceptance testing.
- Test a non-default release camera preset before accepting a future checkpoint.
