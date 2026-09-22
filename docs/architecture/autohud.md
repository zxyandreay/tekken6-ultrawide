# AutoHUD Architecture

**Status:** CURRENT / ACCEPTED  
**Runtime baseline:** official v1.2.1 / OPT-EXP4A

Tekken 6 uses a 16:9 logical presentation. The plugin asks PPSSPP for the current landscape display aspect ratio and derives horizontal correction at runtime rather than selecting a fixed phone/monitor profile.

For display aspect `A`, with baseline `B = 16/9`:

```text
s = B / A
```

Semantic horizontal transforms use the 480-wide PSP logical frame:

```text
LEFT:
x' = s*x

CENTER:
x' = 240 + s*(x - 240)

RIGHT:
x' = 480 - s*(480 - x)
```

Ordinary horizontal extent generally follows:

```text
w' = s*w
```

Vertical geometry is preserved unless a renderer-specific finding proves otherwise.

## Why semantic ownership matters

The plugin does **not** globally scale every 2D draw. Different HUD elements belong to different semantic owners:

- P1/left-side information -> LEFT
- timer, round markers, and center effects -> CENTER
- P2/right-side information -> RIGHT
- HP bars -> specialized side-to-center behavior
- mode-specific text -> narrow owner/state predicates

This avoids moving menus, unrelated fonts, or transient UI merely because they share a renderer.

## Current accepted coverage

The accepted gameplay architecture includes:

- automatic 3D aspect correction;
- HP shell and colored fill;
- side strips and rank badges;
- character-name anchoring;
- round timer;
- persistent and immediate round markers;
- animated winner/earned-round glow;
- Practice HUD text/infinity behavior;
- Gold Rush target labels;
- custom replacement-texture/font compatibility;
- PPSSPP fast-forward compatibility.

The implementation is aspect-derived. Development validation has primarily used an approximately 20:9 device, so other ratios still benefit from independent real-device testing.

## Research evidence

See:

- [AutoHUD research](../../research/autohud/)
- [Renderer optimization findings](../../research/renderer-optimization/)
