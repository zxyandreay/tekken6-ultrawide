# OPT-EXP2R remaining round-win regression and EXP2R2 — 2026-09-21

## Device result

OPT-EXP2R improved the rejected EXP2 result:

- the very red/orange compositing regression was fixed;
- the round-win halo/after-glow still targeted the wrong-looking orb;
- P1 earned-orb placement remained slightly misaligned.

Therefore OPT-EXP2R is not accepted. OPT-EXP1 remains the last fully validated checkpoint.

## What remained unchanged

Binary comparison confirms that the dedicated winner-glow converter and the late-orb rectangle implementation were not edited by EXP2/EXP2R.

The dedicated glow still uses:

```text
0x08AC9C38 -> 0x08AE94A4
```

and the late earned-orb rectangle rule still includes the validated P2 lower bound:

```text
P2 authored x >= 273
```

The remaining defect is therefore caused by slot-scope ownership, not by reopening the winner-glow transform itself.

## Historical scope rule

The v1.2.0 documentation explicitly records:

> the newly earned orb is submitted after the slot-0xEF scope closes.

That distinction is important. When scope depth is nonzero, the rectangle hook applies the broad scoped battle-HUD transform. When scope depth is zero, the immediate earned orb is selected by a much narrower y=27 / 16x16 / side-specific X predicate.

OPT-EXP2/EXP2R moved the scope interception inside the common D9F8 renderer. That can scope calls which were not members of the original thirteen caller patches, including indirect/dynamic calls that do not appear as direct static references.

The result is that win-burst overlay rectangles which were intentionally outside the broad scope can be transformed together with the orb. The separate rotated winner glow remains on its own correct converter path, so the two visual layers no longer line up as they did in v1.2.0.

## EXP2R2 design

EXP2R2 restores the original scope membership rather than adding an orb-specific workaround.

- The ten original direct JAL routes are restored to stock.
- The three original tail-J routes remain externally wrapped.
- One internal hook is kept at 0x0892DA04.
- At that internal hook, the broad 0xEF scope is opened only when D9F8's saved caller really came from a stock direct `JAL 0x0892D9F8`.
- The tail-J wrapper uses a tiny trampoline so it cannot be mistaken for one of those direct callers.
- Indirect/dynamic D9F8 submissions remain scope-depth zero and therefore fall back to the already validated late-orb predicate.
- Winner-glow converter code is unchanged.
- Late-orb rectangle code is unchanged.

This reduces the original thirteen caller patches to four installed game hooks while preserving the historical split between persistent round-marker scope and the late earned-orb phase.

## Binary invariant

```text
file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

EXP2R2 SHA-256:

```text
b6570ddc1127ce12cef02643b5f16703af01badd8728aa42624c177e42760b8c
```

## Test priority

Test only the rejected subsystem first:

1. P1 first win;
2. P2 first win;
3. immediate earned orb position;
4. halo/spin follows that same orb during the burst;
5. normal orange-light appearance;
6. persistent next-round orb stays in the same slot.

Only if those pass should the broader v1.2.0 regression sweep continue.
