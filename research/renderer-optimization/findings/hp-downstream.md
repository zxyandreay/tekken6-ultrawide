# HP Downstream A/B Analysis — 2026-09-21

## Decision

The upstream v1.2.0 HP gauge hook can move to the existing shared sprite dispatcher at `0x0892D56C / 0x0892D5B0` without losing the state needed to reproduce the released result.

The exact packet-local transform is:

```text
x'     = x - orientation * hp_shift
width' = width * hp_scale
```

where:

```text
d        = 1 - s
hp_shift = 6.528055667877197 * d
hp_scale = 1.0 + 0.24672749638557434 * d
```

The downstream packet supplies `x`, `width`, `orientation`, resource, and descriptor identity. It therefore does not need the upstream gauge object.

The common LEFT/CENTER/RIGHT endpoint model does not reproduce the released HP endpoints. `OPT-EXP1` should move the existing affine HP result downstream, not replace it with the general anchor formulas.

No production plugin was changed during this research.

## Evidence set

The analysis uses these ignored captures:

```text
hp-downstream-stock-2026-09-20T14-03-58-234Z.json
hp-downstream-discovery-stock-battle-hud-2026-09-20T14-56-38-062Z.json
hp-downstream-discovery-v120-battle-hud-2026-09-20T15-10-38-502Z.json
hp-downstream-discovery-v120-battle-hud-2026-09-20T15-16-17-615Z.json
hp-downstream-discovery-v120-low-hp-2026-09-21T03-00-59-835Z.json
```

The `15-16-17` capture contains two complete HUD cycles, 12 matched gauge transformations, and 19 raw downstream hits. Its old probe version marked the file invalid only because the six-second timebox ended before the requested 24-hit ceiling. The probe now treats a timeboxed burst as valid after it has captured an HP control packet.

The supplied stock executable was also checked directly:

```text
file:   D:\ULUS10466_EBOOT.BIN
SHA256: E0ED418952C51032796EBC54584592A9F6075495229F6D12D5065F3186BCB55F
```

Its load mapping is:

```text
file offset: 0x001018
guest base:  0x08804018
```

The bytes at both downstream calls confirm the same MIPS boundary:

```text
0x0892D56C  jal   0x08825EAC
0x0892D570  swc1  f0,0x2C(sp)

0x0892D5B0  jal   0x08825EAC
0x0892D5B4  swc1  f0,0x2C(sp)
```

At the wrapper or callee entry, the delay-slot store has executed and `packet+0x1C` contains the height. Stock and v1.2.0 comparisons in this report use that post-delay boundary.

## Runtime validation

The stock probe verified `ULUS10466`, rejected a loaded `Tekken6Ultrawide` module, and checked the documented original instructions with `memory.read` and `replacements: false`.

The v1.2.0 probe verified all of the following before capture:

- one active `Tekken6Ultrawide` module;
- the four released hook destinations at `0x0892C1F0`, `0x0892C26C`, `0x0892D56C`, and `0x0892D5B0`;
- the released downstream wrapper byte signature;
- readable v1.2.0 aspect and HP parameters.

PPSSPP v1.20.4 reported a module span of `0x0F00`. This is its allocated module memory block, not the ELF program header. The release still has one `PT_LOAD` with `p_filesz = p_memsz = 0x0EB0`; the resident-layout constraint is unchanged.

The measured runtime parameters were:

```text
s         = 0.7998131513595581
aspect    = 2.2227413674754306
hp_shift  = 1.306830883026123
hp_scale  = 1.0493916273117065
```

## Proven packet identities

All packets below reached `D56C` in the sampled battle HUD. No sampled battle packet used `D5B0`.

| Family | Side | Resource | Side ID | X | Y | Z | Width | Height | Orientation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HP layer | P1 | `0x0E` | 8 | 205 | 21 | 1000 | live | 32 | -1 |
| HP layer | P1 | `0x0D` | 6 | 205 | 21 | 1000 | live | 32 | -1 |
| HP layer | P2 | `0x0E` | 9 | 275 | 21 | 1000 | live | 32 | +1 |
| HP layer | P2 | `0x0D` | 7 | 275 | 21 | 1000 | live | 32 | +1 |
| Rank | left | variable | 4 | 38 | 56 | 1000 | 64 | 32 | +1 |
| Rank | right | variable | 5 | 442 | 56 | 1000 | 64 | 32 | +1 |
| Side strip | left | `0x2A` | 30 | 4 | 22 | 1000 | 256 | 32 | +1 |
| Side strip | right | `0x2A` | 31 | 476 | 22 | 1000 | 256 | 32 | -1 |

Rank resource values varied across captures (`0x0B`, `0x0C`, and `0x0D`). A future rank predicate must not depend on one fixed resource value.

The descriptor pointer encodes the side ID:

```text
side_id = (a3 - 0x08B9BB84) / 0x10
```

The four HP `(resource, side ID)` pairs are stable and identify both layer and owner without upstream gauge state.

## Released downstream-wrapper behavior

The v1.2.0 breakpoint stops at the verified wrapper entry, after the game call's delay slot. The paired stop at `0x08825EAC` records the packet after the wrapper.

| Family | Side | Wrapper-entry X | Submit X | Entry orientation | Submit orientation | Width change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| HP | P1 | 206.306824 | 206.306824 | -1 | -1 | none |
| HP | P2 | 273.693176 | 273.693176 | +1 | +1 | none |
| Rank | left | 38 | 30.392900 | +1 | 0.799813 | none |
| Rank | right | 442 | 449.607100 | +1 | 0.799813 | none |
| Side strip | left | 4 | 3.199253 | +1 | 0.799813 | none |
| Side strip | right | 476 | 476.800747 | -1 | -0.799813 | none |

This proves that HP arrives at the final v1.2.0 side/rank wrapper already transformed. The wrapper rejects HP from its family-specific branches and forwards it unchanged. Rank and side-strip packets enter with stock coordinates and receive their released transforms inside the wrapper.

The three predicates can therefore coexist in one dispatcher.

## HP X transformation

Stock X stayed constant at full, partial, and low health:

```text
P1: 205
P2: 275
```

Released v1.2.0 produced:

```text
P1: 206.30682373046875
P2: 273.69317626953125
```

The relationship is:

```text
P1: 205 + hp_shift
P2: 275 - hp_shift
```

Equivalently, because HP orientation is `-1` for P1 and `+1` for P2:

```text
x' = x - orientation * hp_shift
```

The largest difference between the packet result and this expression was about `7.2e-6`, consistent with single-precision arithmetic.

## HP width transformation

The enhanced v1.2.0 probe traps the gauge wrapper before its multiply, traps `0x08928FF4` after the multiply, and attaches that pair to the matching downstream packet.

Representative results:

| State | Side | Resource | Input width | Output/downstream width | Ratio |
| --- | --- | ---: | ---: | ---: | ---: |
| partial/high | P1 | `0x0E` | 176.145 | 184.845 | 1.049391651 |
| partial/high | P1 | `0x0D` | 176.144 | 184.844 | 1.049391613 |
| partial/high | P2 | `0x0E` | 166.595 | 174.823 | 1.049391651 |
| partial/high | P2 | `0x0D` | 166.594 | 174.823 | 1.049391669 |
| low | P1 | `0x0E` | 21.222 | 22.270 | 1.049391673 |
| low | P1 | `0x0D` | 21.222 | 22.270 | 1.049391668 |
| low | P2 | `0x0E` | 18.039 | 18.930 | 1.049391582 |
| low | P2 | `0x0D` | 18.039 | 18.930 | 1.049391623 |

The partial/high run produced 12 matched pairs. Its maximum absolute ratio error against `hp_scale` was `4.151e-8`. The low run produced seven attached pairs; its maximum error was `4.569e-8`.

The stock full-health capture recorded width `191` for all four HP packets. At the measured aspect, the same formula gives:

```text
191 * 1.0493916273117065 = 200.433800816536
```

The earlier validated fixed-20:9 full-health capture recorded approximately `200.425`, matching `191 * 1.0493455`. Full, partial, and low widths therefore follow the same linear transform:

```text
width' = width * hp_scale
```

Both resource layers behave identically. Small differences between adjacent layer widths come from sampling separate live draw calls, not different coefficients.

## Consolidated A/B table

| Scene | Side | Resource | Path | Stock X | v1.2.0 X | Stock-space width | v1.2.0 width | Orientation | Side ID |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| full | P1 | `0x0E` | D56C | 205 | 206.306824 | 191 | 200.433801* | -1 | 8 |
| full | P1 | `0x0D` | D56C | 205 | 206.306824 | 191 | 200.433801* | -1 | 6 |
| full | P2 | `0x0E` | D56C | 275 | 273.693176 | 191 | 200.433801* | +1 | 9 |
| full | P2 | `0x0D` | D56C | 275 | 273.693176 | 191 | 200.433801* | +1 | 7 |
| partial/high | P1 | `0x0E` | D56C | 205 | 206.306824 | 176.145 | 184.845 | -1 | 8 |
| partial/high | P1 | `0x0D` | D56C | 205 | 206.306824 | 176.144 | 184.844 | -1 | 6 |
| partial/high | P2 | `0x0E` | D56C | 275 | 273.693176 | 166.595 | 174.823 | +1 | 9 |
| partial/high | P2 | `0x0D` | D56C | 275 | 273.693176 | 166.594 | 174.823 | +1 | 7 |
| low | P1 | `0x0E` | D56C | 205 | 206.306824 | 21.222 | 22.270 | -1 | 8 |
| low | P1 | `0x0D` | D56C | 205 | 206.306824 | 21.222 | 22.270 | -1 | 6 |
| low | P2 | `0x0E` | D56C | 275 | 273.693176 | 18.039 | 18.930 | +1 | 9 |
| low | P2 | `0x0D` | D56C | 275 | 273.693176 | 18.039 | 18.930 | +1 | 7 |

`*` The full v1.2.0 value is the exact result of the measured current-aspect coefficient applied to the direct stock width. The earlier fixed-20:9 runtime capture directly measured approximately `200.425` with that build's `1.0493455` coefficient.

## Endpoint-model test

Treating P1 as `[x-width, x]` and P2 as `[x, x+width]`, the current-aspect full-health transform predicts:

```text
P1 stock:   outer=14       inner=205
P1 v1.2.0: outer=5.873030 inner=206.306831

P2 stock:   inner=275      outer=466
P2 v1.2.0: inner=273.693169 outer=474.126970
```

Applying the general semantic anchors to those stock endpoints instead would produce:

```text
P1 LEFT outer:    11.197384
P1 CENTER inner: 212.006540
P2 CENTER inner: 267.993460
P2 RIGHT outer:  468.802616
```

Those values do not match v1.2.0. The released HP transform expands the live span and shifts its inner endpoint by a small side-dependent constant. It is not the general LEFT-to-CENTER or CENTER-to-RIGHT endpoint transform.

The smallest proven exact downstream formulation is therefore the affine packet transform using `hp_shift` and `hp_scale`. Substituting their definitions makes it depend only on `s`, packet X, packet width, and orientation, but it does not eliminate the two HP coefficients mathematically.

## Proposed HP predicate

For the stock packet that `OPT-EXP1` would receive, use all stable identity fields:

```text
path in { D56C, D5B0 }
Y      == 21.0f    (0x41A80000)
Z      == 1000.0f  (0x447A0000)
height == 32.0f    (0x42000000)

and one exact owner/layer tuple:

(resource=0x0E, sideId=8, X=205.0f, orientation=-1.0f)  // P1 layer E
(resource=0x0D, sideId=6, X=205.0f, orientation=-1.0f)  // P1 layer D
(resource=0x0E, sideId=9, X=275.0f, orientation=+1.0f)  // P2 layer E
(resource=0x0D, sideId=7, X=275.0f, orientation=+1.0f)  // P2 layer D
```

Relevant exact float words are:

```text
205.0f = 0x434D0000
275.0f = 0x43898000
-1.0f  = 0xBF800000
+1.0f  = 0x3F800000
```

Width should remain a payload, not an identity. It changes continuously with health.

This predicate is mutually exclusive with the observed controls:

- rank uses side IDs `4/5`, `Y=56`, width `64`, and X `38/442`;
- side strip uses side IDs `30/31`, `Y=22`, resource `0x2A`, width `256`, and X `4/476`.

Resource alone is insufficient because HP resource `0x0D` can overlap a rank resource. The full tuple prevents that collision.

## Proposed `OPT-EXP1` architecture

Keep the two shared game hooks and extend their existing wrapper:

```text
0x0892D56C / 0x0892D5B0
              |
              v
     compact packet dispatcher
       |        |        |
      HP      side      rank
       |        |        |
  affine HP   existing  existing
  X + width   transform transform
       \        |        /
        \       |       /
           0x08825EAC
```

The HP branch should run at wrapper entry, after the original delay slot:

```text
if exact_hp_predicate(packet, a1, a3):
    packet.x     -= packet.orientation * hp_shift
    packet.width *= hp_scale
    forward_to_stock_submit()
```

The experiment can then remove:

```text
0x0892C1F0 patch
0x0892C26C patch
module+0x07E4 upstream gauge wrapper
upstream side selection and scratch-X adjustment
upstream HP width multiply
HP-specific call/tail-call ABI handling
```

For the first experiment, retain the proven startup computation and storage of `hp_shift` and `hp_scale`; load those values in the shared dispatcher. This changes one variable at a time. A later binary-size comparison can test whether computing them from `s` inside the dispatcher saves space after accounting for extra instructions.

Do not estimate byte savings until an actual `OPT-EXP1` binary exists.

## Risks and limits

1. Every sampled battle packet used `D56C`. `D5B0` remains a released hook and must preserve the same ABI, but this run did not exercise it.
2. The battle burst contained HP, rank, and side-strip families but no unrelated shared-path packet. The exact predicate has no collision in observed data; broader mode testing must still check false positives.
3. Rank resource values varied. Preserve the released rank classifier rather than replacing it with a fixed resource check.
4. Both original callsites use `swc1 f0,0x2C(sp)` in the delay slot. The replacement must keep that effect before reading packet height or forwarding.
5. P2 uses positive orientation and the opposite X shift. A sign error would move both bars in the same direction.
6. The two HP resources can differ slightly during animation because they are separate submissions. Transform each packet's own live width.
7. The first low-health attempt missed the gauge-wrapper breakpoint because PPSSPP retained a JIT block. Re-adding both verified wrapper breakpoints at the canary stop fixed the trace; seven later low pairs matched.
8. `OPT-EXP1` still needs a visual device test at full, partial, and low HP and a regression sweep for rank, side strip, replacement textures/fonts, menus, and all v1.2.0 modes.
9. Preserve the one-`PT_LOAD`, `0x0EB0/0x0EB0` resident layout. This optimization must recover code space, not enlarge the module.

## Completion answers

| Question | Answer |
| --- | --- |
| 1. Exact HP identity fields? | `Y=21`, `Z=1000`, height `32`, resources `0x0D/0x0E`, side IDs `6/7/8/9`, stock X `205/275`, orientation `-1/+1`, with the exact owner/layer tuple above. |
| 2. Exact X transform? | `x' = x - orientation * hp_shift`. |
| 3. Exact width transform? | `width' = width * hp_scale`. |
| 4. Valid at full, partial, and low HP? | Yes. Stock full/low controls, historical full v1.2.0 evidence, and new same-execution partial/low pairs agree. |
| 5. Do both resource layers behave identically? | Yes. Both layers use the same X shift and width coefficient on both sides. |
| 6. Can downstream state identify P1/P2? | Yes. Side ID, stock X, and orientation independently agree. |
| 7. Can HP avoid side/rank false positives? | Yes for all observed packets. The exact tuples are disjoint from rank and side-strip identities. |
| 8. Can the upstream machinery move downstream? | Yes. The gauge object is unnecessary. The exact affine coefficients remain required unless a later byte-level rewrite proves a smaller equivalent computation from `s`. |
| 9. Which upstream pieces become removable? | Both gauge-owner patches, the `module+0x07E4` wrapper, scratch-X/side preparation, width multiply, and special JAL/tail-J handling. |
| 10. Is `OPT-EXP1` justified? | Yes. The evidence supports the exact implementation above. Build and mutation testing remain separate work. |

## Final conclusion

The released upstream HP hook survives for historical reasons, not because downstream state is insufficient. The final side/rank dispatcher sees a complete, stable HP identity and the live width. Moving the exact released affine transform into that dispatcher is justified as the next experiment.
