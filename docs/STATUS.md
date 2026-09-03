# Status

Last updated: 2026-09-03

## Current phase

Phase 8: v0.5 beta — keep the validated 3D/camera baseline, reduce repeated PPSSPP JIT invalidation, and device-test a narrowly scoped UI logical-canvas hook.

## Verified baseline

- Supported game: Tekken 6 USA `ULUS10466`.
- The known-good 20:9 CWCheat visually fixes the 3D view on the development device when PPSSPP Display Layout is set to Stretch.
- Four exact 3D runtime sites remain unchanged:
  - `0x08945F10`
  - `0x08946794`
  - `0x08946BC8`
  - `0x08947D90`
- Original aspect pair at each site:
  - `0x3C013FE3`
  - `0x34218E39`
- Camera site remains `0x0895350C` with presets `0x3F80` through `0x3F83`.
- v0.3's invalidate-before-write method was visually validated and is the known-good PRX/JIT foundation.

## v0.5 runtime maintenance

v0.3/v0.4 invalidated and rewrote the target guest-code ranges on every poll. v0.5 keeps invalidate-before-write for initial installation or real restoration, but does not disturb a healthy target instruction or the expected PPSSPP `0x68xxxxxx` emuhack state on every subsequent 77 ms poll.

This preserves the proven JIT-safe installation method while reducing unnecessary code-cache churn. It does not alter texture bytes or replacement-texture identities.

## HUD/UI research result

The project still rejects a broad global 480x272 projection patch. Three earlier generic orthographic candidates were disproven by runtime testing.

Focused tracing of candidate #2 established:

- coordinate/set helper: `0x08A39158`
- initializer B: `0x08A392F0`
- follow-up float/property helper: `0x08A39808`
- initializer B creates a 2D descriptor with `+0x28 = 480.0` and `+0x2C = 272.0`.
- `+0x30` and `+0x34` initialize to `1.0`, but a whole-executable scan did not identify a safe candidate-#2-specific setter that could be promoted as a HUD X/Y scale hook.
- `+0x4C` is broadly referenced (117 generic COP1 hits in the earlier scan) and is now treated as unsafe; the surrounding 1.0 fields make color/alpha state a more plausible interpretation than a dedicated HUD scale.

## v0.5 experimental HUD hook

Only three external calls to initializer B are redirected:

- `0x089A92D8`
- `0x089AB3A4`
- `0x089AD87C`

Their traces show the target descriptor pointer is already supplied in `$a0`. The plugin hook:

1. calls the original `0x08A392F0` initializer,
2. preserves its integer return value,
3. changes only descriptor field `+0x28`,
4. leaves `+0x2C` and all other descriptor fields untouched.

The logical width is calculated as:

```text
480 * targetAspect / (16/9)
```

At 20:9 this is 600, yielding a targeted `600x272` logical canvas for only those three caller paths.

This is an **experimental device-test path**, not a completed HUD fix. It can be disabled with:

```ini
EnableHUDExperimental = 0
```

## Immediate test matrix

1. Confirm 3D proportions and camera still match v0.4 with the experimental HUD option both on and off.
2. Check fight HUD, character select, pause/menu screens, result screens, prompts, and full-screen overlays.
3. Test any replacement texture pack on the same screens with `EnableHUDExperimental = 1` and `0`.
4. If only one UI family regresses, document that screen rather than broadening the patch globally.
5. Keep `+0x4C` and the disproven generic orthographic paths out of runtime code unless new evidence overturns the current trace.
