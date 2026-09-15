# Center round timer

## Status

Solved and device-validated on ULUS10466 at fixed 20:9.

The large two-digit round countdown is a separate draw family from the round rails/orbs. The surrounding round-marker geometry was already corrected, but the countdown digits bypassed the slot-builder scope used by that family.

## Static ownership

The countdown owner renders two digit submissions through the original timer renderer at `0x0892D72C`.

Dedicated digit callsites:

```text
0x08929AF8
0x08929B44
```

Observed authored positions:

```text
digit 1: x=211, y=7
digit 2: x=236, y=7
```

Both calls eventually reach the ordinary rectangle builder already intercepted by the HUD plugin.

## Correction model

The timer is neutral/center-owned HUD, so it uses the same fixed-20:9 CENTER transform as the protected round-marker family:

```text
x' = 0.8*x + 48
width' = 0.8*width
```

Y and height are preserved.

The final implementation wraps only the two timer digit submissions, temporarily increments the existing centered HUD rectangle scope, calls the original timer renderer, then immediately restores the scope.

## ABI requirement

`0x0892D72C` consumes a fifth argument from the caller stack. The original timer callsites place that word at `0($sp)`. Any wrapper that creates its own stack frame must forward this argument into its outgoing argument area before calling the original renderer.

An early integrated wrapper omitted that forwarding and caused the timer to disappear. The corrected wrapper preserves the stack argument and reproduces the behavior of the successful scope diagnostic.

## Device validation

The corrected integrated plugin was tested in multiple battle modes and the countdown remained visible, horizontally de-stretched, and centered. No regression was observed in HP bars, ranks, side effects, round markers, or winner-orb behavior.

The center round timer is therefore frozen unless a regression is demonstrated.
