# Status

Last updated: 2026-09-03

## Current phase

Phase 9: v0.6 beta — restore normal Tekken/PPSSPP memory behavior, retire the failed v0.5 HUD descriptor experiment, and test a single native-PSP flat-layer viewport transform while preserving the validated ultrawide 3D/camera baseline.

## Validated baseline retained

- Game: Tekken 6 USA `ULUS10466`.
- 3D aspect sites:
  - `0x08945F10`
  - `0x08946794`
  - `0x08946BC8`
  - `0x08947D90`
- Camera site: `0x0895350C`.
- User-validated baseline: 20:9 3D correction + Wider camera (`0x3F82`) with PPSSPP Display Layout = Stretch.
- Low-churn PPSSPP JIT maintenance remains in place.

## Texture/memory correction

The previous manifest had `memory = 93`. PPSSPP uses the plugin memory field to increase emulated game RAM, so the plugin was changing Tekken's memory environment even though the PRX does not require extended RAM.

v0.6 removes the `memory` key entirely. This is the primary plugin-side correction for the selective replacement-texture fallback reported in UI/menu screens.

Runtime confirmation is still required; CI can only confirm package contents and build behavior.

## Re-established 2D requirement

The target is not individual HUD repositioning.

Desired architecture:

```text
3D scene -> ultrawide
flat UI/HUD/menu layer -> original Tekken PSP coordinates and 480:272 proportions,
                          centered inside the ultrawide output
```

The exact PSP frame aspect is `480/272`, not exact 16:9.

For target aspect `A`:

```text
safeScale = (480/272) / A
```

At 20:9:

```text
safeScale = 27/34 = 0.794117647...
```

## Retired v0.5 experiment

The v0.5 hook at initializer `0x08A392F0`, which changed descriptor `+0x28`, is removed. User testing proved it did not correct the battle HUD.

The three generic orthographic 480x272 paths A/B/C remain rejected because isolated runtime tests produced no visible HUD/UI/menu change.

## v0.6 native 2D viewport path

New static tracing followed the previously unexplained `0x08AC5BA8` route and established:

- `0x08AC5BA8` is a thin wrapper forwarding to `0x08AC63AC`.
- `0x08AC63AC` constructs a viewport transform from six floating-point bounds.
- The live call at `0x08864B88` occurs in a surface/flat render owner around `0x08864ADC`.
- That surrounding path directly uses the viewport routine but has no direct perspective or generic-orthographic builder marker.
- Separate calls to the broad viewport family were classified around known perspective and orthographic setup functions; therefore the shared viewport builder itself is not patched globally.

v0.6 redirects only `0x08864B88` through `plugin/safe_area.S`.

The wrapper receives the original viewport, reduces only its width by `safeScale`, and adds half the removed width to X. Y, height, near/far, and every game-authored HUD/menu coordinate remain unchanged.

Status: **strong static candidate / new device-test implementation**, not yet visually validated.

## Immediate validation

1. Cold boot v0.6 with the same HD texture pack used in v0.4/v0.5.
2. Confirm previously missing custom pause/menu/prompt textures load again.
3. Confirm 3D proportions and Wider camera match v0.4.
4. Confirm battle HUD, prompts, menus, pause UI, character/stage select, and results are no longer horizontally stretched.
5. Compare `EnableNative2DSafeArea = 1` vs `0` if any flat screen behaves unexpectedly.
