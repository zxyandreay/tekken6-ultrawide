# HUD / Native 2D Research

Last updated: 2026-09-03

## Clarified goal

The project is not trying to reposition individual Tekken 6 HUD or menu elements.

The desired output is two presentation layers:

```text
3D geometry -> target ultrawide aspect
flat graphics -> original PSP-authored coordinates and 480:272 proportions,
                 centered inside the ultrawide output
```

This means a health bar remains at the position Tekken authored, a menu item remains at its original PSP coordinate, and a button prompt keeps its original relationship to the 480x272 canvas. The correction should happen once at the flat presentation boundary.

## Exact PSP safe-area math

The PSP framebuffer is `480x272`, whose aspect is:

```text
480 / 272 = 30 / 17 = 1.764705882...
```

For a target display/game aspect `A` under PPSSPP Stretch:

```text
safeScale = (480/272) / A
```

At 20:9:

```text
safeScale = (30/17) / (20/9)
          = 27/34
          = 0.794117647...
```

A viewport implementation therefore uses:

```text
safeWidth = originalWidth * safeScale
safeX     = originalX + (originalWidth - safeWidth) / 2
```

No Y/height change is required.

## Rejected paths

### Generic orthographic A/B/C

The three direct 480x272 calls to `0x08ACA990` remain negative runtime results:

- A: `0x08863258`
- B: `0x088634E4`
- C: `0x088644B8`

Changing their 480-wide bounds produced no visible HUD/UI/menu change on the target device. They are not the primary live flat path for the tested screens.

### v0.5 descriptor-width hook

v0.5 redirected three calls to initializer `0x08A392F0` and changed descriptor field `+0x28` from 480 to an aspect-derived width.

User testing showed the battle HUD remained stretched. That experiment is removed in v0.6.

## Viewport research

The previously unexplained path around `0x08864B74` calls `0x08AC5BA8`.

New tracing established that:

```text
0x08AC5BA8 -> thin wrapper -> 0x08AC63AC
```

`0x08AC63AC` consumes six floating values and constructs the viewport transform. Its math contains the expected half-width/half-height/depth midpoint operations and stores the original six viewport values.

The shared viewport builder itself cannot be patched globally because it is also reached by broader render setup.

### Broad 480x272 viewport family

`0x08946390` selects full/left/right viewport modes and is called from both perspective-associated and orthographic-associated setup paths. It is therefore not a valid global 2D hook.

The call graph includes caller regions classified with perspective markers and separate regions classified with orthographic markers.

### Live flat/surface path

Runtime `0x08864B88` calls the viewport wrapper from the surface/render function around `0x08864ADC`.

Its immediate owner:

- obtains current render-surface width/height,
- sets a full viewport,
- directly calls the viewport wrapper,
- has no direct call to the perspective builder `0x08ACA6C4`,
- has no direct call to the generic orthographic builder `0x08ACA990`.

Earlier broad experiments in this area visibly affected flat overlays, unlike the A/B/C no-op tests. Under the clarified project requirement, that is positive evidence that this is a real flat presentation path rather than a reason to manipulate individual sprites.

## v0.6 implementation

Only the `jal` at `0x08864B88` is redirected.

The MIPS wrapper in `plugin/safe_area.S` receives Tekken's already prepared viewport registers:

```text
f12 = x
f13 = y
f14 = width
f15 = height
f16 = near
f17 = far
```

It changes only `f12` and `f14` using the centered safe-area formula, then calls the original `0x08AC5BA8` routine.

No HUD object positions, sizes, health-bar values, text coordinates, menu descriptors, texture coordinates, or orthographic projection constants are patched.

## Important validation condition

The static evidence is strong enough for a beta implementation, but only device testing can prove that this viewport owns all intended battle/menu flat elements without affecting a 3D pass.

If the 3D world itself is compressed when `EnableNative2DSafeArea = 1`, the path must be reclassified and disabled; do not compensate by widening individual UI objects.
