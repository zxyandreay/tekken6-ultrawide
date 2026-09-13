# Fight HUD safe-area research

## Current milestone

Keep the released v1.1.0 automatic 3D aspect correction unchanged and isolate only the in-fight 2D HUD. The first target is the two player HP/status assemblies.

The intended final behavior is:

- 3D scene continues to use the detected ultrawide aspect ratio.
- Fight HUD remains visually authored for the original PSP 16:9 frame.
- No global menu/UI projection change is made during this milestone.

For a 20:9 output, the centered 16:9 safe-area transform in PSP logical coordinates is:

```text
scale = (16/9) / (20/9) = 0.8
x'    = 0.8 * x + 48
width'= 0.8 * width
```

For a later arbitrary detected aspect `A`:

```text
scale  = (16/9) / A
offset = 240 * (1 - scale)
x'     = scale * x + offset
width' = scale * width
```

## What the old experiments already proved

An earlier global draw hook correctly identified the relevant draw-packet fields:

- packet `+0x00`: X position
- packet `+0x20`: horizontal width/scale

It also implemented the correct 20:9 safe-area math (`x = 0.8*x + 48`, `width *= 0.8`). The failure was scope: hooking the shared draw primitive transformed unrelated menus/UI and caused collateral rendering regressions.

The new strategy therefore keeps the packet transform but applies it only to proven fight-HUD draw callers.

## Known draw primitive

The common 2D draw primitive is at runtime address:

```text
0x08825EAC
```

Original call instruction at the candidate sites:

```text
0x0E2097AB    jal 0x08825EAC
```

A previously tested narrow hook at `0x0892D56C` and `0x0892D5B0` affected the HP fill path, but not the complete bar assembly. Those two sites are retained as the diagnostic control.

## Strong direct-draw candidates

The repair history also identified eight additional direct calls to the same draw primitive that were touched during the old HUD investigation:

```text
0x0893EE90
0x0893EF04
0x0893EF58
0x0893EFBC
0x0893F010
0x0893F074
0x08941524
0x08944394
```

The six calls in `0x0893EDAC..0x0893F078` form three highly regular sprite pairs. The resource IDs passed immediately before those draw calls are:

```text
Pair A: 0x12 / 0x0F
Pair B: 0x13 / 0x10
Pair C: 0x14 / 0x11
```

This makes them strong candidates for paired P1/P2 HUD sub-elements, but ownership is not yet proven.

## Path-map diagnostic v1

`ULUS10466_HUD_PATH_MAP_v1.ini` intentionally does **not** apply the final safe-area correction. Instead it installs a tiny wrapper at `0x089EB858` that only adds `+32.0f` to packet X and then tail-calls the original draw primitive.

The tests are:

- MAP 0: known HP-fill path (`0x0892D56C`, `0x0892D5B0`)
- MAP 1: pair `0x12 / 0x0F`
- MAP 2: pair `0x13 / 0x10`
- MAP 3: pair `0x14 / 0x11`
- MAP 4: single draw at `0x08941524`
- MAP 5: single draw at `0x08944394`

Only one mapping entry should be enabled at a time. The purpose is to identify exactly which HP frame/background/icon pieces move before introducing any scaling.

## Paths deliberately excluded for now

Do not reuse the old global orthographic/projection edits around:

```text
0x08863228
0x0886345C
0x08864490
0x08864B74..0x08864C18
```

Those paths were too broad and previously caused pause-overlay loss, rectangular artifacts, and unrelated UI corruption.

## Next step after ownership is confirmed

Once the screenshots identify which direct calls own the full HP assemblies, replace the diagnostic `+32 X` wrapper only on those calls with the real centered safe-area packet transform. After the fixed 20:9 version is stable, derive `scale` and `offset` from the same PPSSPP display-aspect query already used by the v1.1.0 plugin.
