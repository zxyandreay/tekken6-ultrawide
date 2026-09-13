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

## Path-map diagnostic v1 result

`ULUS10466_HUD_PATH_MAP_v1.ini` used a small wrapper that added `+32.0f` to packet X without changing width. On-device testing produced a decisive result:

- MAP 0 (`0x0892D56C`, `0x0892D5B0`) moved the visible HP fill.
- MAP 1 through MAP 5 did nothing to the visible fight HUD.

The old MAP 1-5 candidates are therefore discarded for the current milestone.

## EBOOT RTTI breakthrough

The ULUS10466 EBOOT retains C++ RTTI for the battle HUD. Relevant class names include:

```text
tk::sprite::battle::CMainTcb_t
tk::sprite::battle::CGaugeTcb_t
tk::sprite::battle::CGaugeRageTcb_t
```

This lets the research target the actual battle-gauge class hierarchy instead of generic 2D rendering paths.

### CGaugeTcb_t

The `CGaugeTcb_t` vtable points to its render method at:

```text
0x0892C124
```

Static disassembly shows that this method draws two gauge layers through `0x08928FF4`, using resource IDs `0x0E` and `0x0D`. That helper eventually reaches `0x0892D3E0`, whose final packet submission uses the already-proven MAP 0 calls:

```text
0x0892D56C -> jal 0x08825EAC
0x0892D5B0 -> jal 0x08825EAC
```

This explains the v1 result: MAP 0 is inside the real `CGaugeTcb_t` HP-fill render path.

`CMainTcb_t` also constructs two `CGaugeTcb_t` instances, one with player index 0 and one with player index 1. The constructor path writes the `CGaugeTcb_t` vtable and stores the side index at object offset `+0x5C`.

### CGaugeRageTcb_t

The rage-gauge class has a separate render method at:

```text
0x0892C290
```

It is not part of the first HP-frame milestone unless later evidence shows that it owns an overlapping shell element.

### CMainTcb_t

The parent battle-HUD class has its render method at:

```text
0x0892BDAC
```

Its main render branch invokes these component renderers in sequence:

```text
0x08929A10
0x0892A30C
0x08929B60
0x0892A5A4
0x0892A7D0
0x0892AE74  ; tail renderer
```

Because this is the class render method rather than update/gameplay logic, selectively suppressing one component call at a time is a much safer ownership diagnostic than hooking a global sprite primitive.

## CMain path-map diagnostic v2

`ULUS10466_HUD_CMAIN_MAP_v2.ini` maps the six `CMainTcb_t::Draw` component renderers above. Each test restores the other render calls and then suppresses exactly one component. MAP 6 replaces the final tail-call with `jr $ra`; its existing stack-restoration delay slot is preserved.

The purpose is to identify which component owns the static HP-bar shell/background around the already-confirmed `CGaugeTcb_t` fill. Once the shell owner is identified, its internal packet submissions can be traced and corrected without touching the rest of the battle HUD.

## Paths deliberately excluded for now

Do not reuse the old global orthographic/projection edits around:

```text
0x08863228
0x0886345C
0x08864490
0x08864B74..0x08864C18
```

Those paths were too broad and previously caused pause-overlay loss, rectangular artifacts, and unrelated UI corruption.

## Final correction strategy

Once both ownership paths are proven:

1. Apply the centered-safe-area packet transform only to the two `CGaugeTcb_t` HP-fill instances.
2. Apply the same transform only to the proven static HP-frame/background component.
3. Leave the 3D projection, menus, pause UI, and unrelated fight HUD untouched.
4. After a fixed 20:9 implementation is stable, derive `scale` and `offset` from the same PPSSPP display-aspect query already used by the v1.1.0 plugin.
