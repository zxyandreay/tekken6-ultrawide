# Fight-HUD reverse-engineering notes

## Scope

Target: Tekken 6 USA (`ULUS10466`) running under PPSSPP.

The released v1.1.0 plugin already corrects the 3D projection automatically. This research adds a fixed-20:9 2D fight-HUD composition layer without globally scaling the entire UI.

The working semantic model is:

```text
P1 side information        -> LEFT
center timer/round family  -> CENTER
P2 side information        -> RIGHT
long health bars           -> SIDE_TO_CENTER span
```

For PSP logical width 480, center 240, and display aspect `A`:

```text
s = (16/9) / A
LEFT:   x' = s*x
CENTER: x' = 240 + s*(x - 240)
RIGHT:  x' = 480 - s*(480 - x)
```

At 20:9, `s = 0.8`:

```text
LEFT:   x' = 0.8*x
CENTER: x' = 0.8*x + 48
RIGHT:  x' = 0.8*x + 96
```

The rectangle path uses an integer center variant (`trunc(x*4/5)+49`) to compensate for integer truncation around the protected center family.

## Released 3D aspect path

The v1.1.0 automatic-aspect patch writes the projection constant at four instruction pairs:

```text
0x08945F10 / 0x08945F14
0x08946794 / 0x08946798
0x08946BC8 / 0x08946BCC
0x08947D90 / 0x08947D94
```

Stock words:

```text
LUI 0x3C013FE3
ORI 0x34218E39
```

The HUD research does not replace this mechanism.

## Fixed hook sites

Every fixed site is checked against its original instruction before the HUD hook set is installed.

### Slot-builder routes to `0x0892D9F8`

JAL sites, stock `0x0E24B67E`:

```text
0x08929854
0x08929958
0x089299E8
0x08929DF0
0x08929F3C
0x0892A10C
0x0892A170
0x0892A1B4
0x0892A1F0
0x0892A268
```

Tail-J sites, stock `0x0A24B67E`:

```text
0x08929228
0x089292F4
0x08929D4C
```

### Rectangle-builder calls to `0x08AB9380`

Stock `0x0E2AE4E0`:

```text
0x08AB9798
0x08AB98AC
```

### Gauge-layer submissions to `0x08928FF4`

```text
0x0892C1F0  stock 0x0E24A3FD  (JAL)
0x0892C26C  stock 0x0A24A3FD  (tail J)
```

### Shared sprite submissions to `0x08825EAC`

Stock `0x0E2097AB`:

```text
0x0892D56C
0x0892D5B0
```

These sites are narrowly filtered by packet shape before side-strip/rank correction is applied.

### Winner-glow converter call

```text
0x08AC9C38  stock 0x0E2BA529
original target: 0x08AE94A4
```

This site is handled separately from the ordinary rectangle path because the winner glow is a rotated THROUGH quad.

## HP shell geometry

A PPSSPP frame-dump differential isolated seven health-bar compositor draws: three shell/trough rectangles and four fill layers.

Through-mode shell geometry in stock screen space:

```text
center shell: 208..272, y=6..38, 64x32 UV
left shell:   -21..235, y=5..37, 256x32 UV
right shell:  245..501, y=5..37, mirrored 256x32 UV
```

Because these are `GE_VTYPE_THROUGH` screen-space vertices, an orthographic projection change cannot reposition them reliably. They must be corrected at the builder/vertex path.

`CMainTcb_t::Draw` is at `0x0892BDAC`. Slot `0xEF` is fetched around `0x0892BDE4` and submitted around `0x0892BE00`. Suppressing only this slot removed the visible HP frames while leaving colored fills, establishing the frame ownership boundary used by `tekken6_hud_slot_builder_wrapper`.

A clean slot-`0xEF` rectangle census produced:

```text
#0 a2=-8,  a3=10, t0=128, t1=64, t2=128, t3=64
#1 a2=360, a3=10, t0=128, t1=64, t2=128, t3=64
#2 a2=82,  a3=27, t0=128, t1=16, t2=128, t3=16
#3 a2=397, a3=27, t0=128, t1=16, t2=128, t3=16
#4 a2=-21, a3=5,  t0=256, t1=32, t2=256, t3=32
#5 a2=501, a3=5,   t0=256, t1=32, t2=256, t3=32
```

Only the last two are the long side shells. The stable long-shell predicate is therefore:

```text
a3=5
t0=256
t1=32
t2=256
t3=32
```

The device-validated fixed-20:9 shell endpoints are:

```text
P1: a2 -21 -> -17, width 256 -> 253  => -17..236
P2: a2 501 -> 497, width 256 -> 253 => 244..497
```

A later same-shape shell overlay is submitted after the slot-depth scope closes; the same exact long-shell tuple is intentionally recognized outside that scope.

## HP fill path

The four fill draws share a normalized local quad. Baseline visible extents were:

```text
P1 layers: 13.248..205.752
P2 layers: 274.248..466.752
```

Baseline world translation/scale:

```text
P1 translation 109.5, scale -191.0
P2 translation 370.5, scale +191.0
```

Live debugging re-established the active path:

```text
0x0892C124 -> 0x08928FF4 -> 0x0892D3E0 -> 0x0892D56C
```

The two narrow gauge submissions are:

```text
0x0892C1F0: resource 0x0E, side IDs 8/9
0x0892C26C: resource 0x0D, side IDs 6/7
```

Both pass `gauge + 0x84` in `t1`. Stable owner fields:

```text
gauge + 0x5C: 0=P1, 1=P2
gauge + 0x84: +98.0=P1 X, -98.0=P2 X
```

At full health `f12=191.0`; depletion scales it proportionally. The validated implementation copies X/Y into plugin scratch storage and applies:

```text
P1 scratch X = original X + 1.3056111
P2 scratch X = original X - 1.3056111
f12          = original width * 1.0493455
```

Using scratch storage avoids cumulative mutation of the live gauge object. Full and partially depleted HP were validated on-device with correct alignment and depletion direction.

## Side strips and rank badges

At the shared sprite path, packet families were separated by shape:

```text
y=22, 256x32 -> translucent under-bar/lightning strip family
y=56, 64x32  -> rank badge family
```

The y=22 family uses sprite orientation to retain P1/P2 ownership. Rank badges cannot use the same sign because both sides may share positive orientation; authored packet X relative to center 240 is used instead:

```text
X < 240 -> P1 / LEFT
X > 240 -> P2 / RIGHT
```

Only horizontal X and scale are corrected; Y/height are preserved. Device testing confirmed P1/P2 rank placement and outward side-effect alignment without regressing the HP span.

## Round markers

Round rails and ordinary round-orb rectangles belong to the centered family. Persistent markers are handled through the scoped rectangle path.

A newly earned orb is also submitted after the slot-`0xEF` scope closes. The late rectangle predicate is deliberately narrow:

```text
y=27
16x16 authored rectangle
P1 authored X: 150..206
P2 authored X: 273..310
```

The P2 lower bound is `273`; a previous `274` lower bound skipped the first P2 late-orb slot by exactly one pixel. The late orb receives the same CENTER transform as the persistent marker family.

The transient winner glow is not an axis-aligned rectangle and is handled by a separate converter hook. See [`WINNER_ORB.md`](WINNER_ORB.md).

## Center shell and timer

The frame dump conclusively identifies the 64x32 center shell at `208..272`, but the six-hit slot census did not identify a unique live builder tuple for that center cap. Do not apply asymmetric side-span logic to it without re-establishing ownership.

Timer and center text should remain proportion-correct and centered rather than horizontally stretched. Their final composition is still separate future work; the solved round-marker result does not imply the whole timer/front-end HUD is complete.

## Rejected or misleading approaches

The following paths produced collateral, stale correlations, or insufficient ownership evidence:

- global/common sprite hooks: moved unrelated menus;
- global/group orthographic projection changes: damaged pause/menu presentation and cannot directly move THROUGH-mode vertices;
- CMain child MAP 1-6 suppression: did not own the long HP shell;
- static descriptor writes: plausible descriptors were copied/relocated before the write mattered;
- long-lived hot breakpoints at the shared fill path: caused severe render stalls/black flashing;
- inferring semantic ownership from raw hit counts: disproven by later captures;
- treating packet `+0x20` as pixel width: observed values behave as scale coefficients;
- deriving P1/P2 solely from packet-local X on mirrored/world-matrix paths;
- hard-coding heap, vertex-buffer, texture-wrapper, or cached GE-list addresses: all were session dependent;
- CPU read watchpoints on cached GE data: PPSSPP CPU watchpoints do not observe GE DMA consumption.

The stable strategy is to identify an owner or exact geometry/resource family, patch one narrow path, and verify the resulting GPU geometry and device presentation.

## Current status

Device-validated:

- 3D automatic ultrawide projection;
- long HP shell span;
- both HP fill layers at full/partial health;
- rank badges and side strips/lightning;
- persistent and immediate winner-orb placement;
- P1/P2 winner-orb glow.

The winner-orb subsystem is frozen unless a regression is demonstrated. Remaining work should move to other battle-HUD families such as timer/labels before considering front-end screens.
