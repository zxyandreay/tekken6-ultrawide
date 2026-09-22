# Renderer Model

**Status:** CURRENT / ACCEPTED

The plugin is built around **owner-specific correction**, not a global 2D transform.

## Established renderer landmarks

These are important known addresses in Tekken 6 USA (`ULUS10466`). They are landmarks, not permission to patch globally.

```text
shared slot builder        0x0892D9F8
rectangle builder          0x08AB9380
shared stock sprite submit 0x08825EAC
shared sprite callsites    0x0892D56C / 0x0892D5B0
timer renderer             0x0892D72C
text early stage           0x08970A90
text packed/late stage     0x08970B24
winner-glow callsite       0x08AC9C38
winner-glow converter      0x08AE94A4
```

## Ownership rule

A safe hook needs both:

1. a transform point where authored/source geometry is still recoverable;
2. enough surviving semantic state to distinguish the intended family from unrelated draws.

Useful discriminators include:

- caller/return address;
- resource/family ID;
- descriptor/source pointer;
- texture/CLUT identity;
- primitive/vertex type;
- authored X/Y and size;
- side/orientation;
- mode/state.

Use the smallest combination that uniquely includes the target and rejects neighbors.

## Frozen accepted subsystems

Do not reopen these during unrelated work without a demonstrated regression:

- HP;
- rank/side-strip path;
- character names;
- timer;
- round-marker family;
- winner orb/glow;
- Practice/Gold mode-font path;
- EXP4A slot-scope wrapper.

The winner-glow path is especially sensitive: visually related layers can use different geometry/UV ownership.

## Separate UI domains

The stock census showed that pause/front-end/transient UI does not necessarily traverse the solved battle-HUD owners. When a target does not appear at a known choke point, start a new owner-discovery pass rather than broadening the battle predicate.

For detailed evidence, see [research](../../research/).
