# OPT-EXP3 plan — collapse Practice/Gold mode font to one hook

## Goal

Replace the accepted two-stage Practice/Gold text implementation with one dynamic hook while preserving the exact visible behavior of v1.2.0 / OPT-EXP2S3.

Current game hook sites:

```text
early: 0x08970A90
late:  0x08970B24
```

Current plugin behavior:

```text
early hook:
- classify the narrow Practice/Gold owner;
- target horizontal scale 100 -> dynamic corrected scale (80 at 20:9);
- allow Tekken to derive the correct glyph width/geometry.

late hook:
- synchronize the packed scale value used by the slow path;
- leave Practice authored X unchanged;
- shift Gold authored X by the dynamic right-anchor amount.
```

The accepted two-stage behavior must remain the reference.

## Why a late-only one-hook design is rejected

ModeCompact EXP4 already showed that fixing only the later stage is too late.

By `0x08970B24`, important horizontal geometry has already been derived from the earlier percentage load.

Therefore OPT-EXP3 must keep the early interception at:

```text
0x08970A90
```

and eliminate the late dynamic hook, not the other way around.

## New static observation

The stock ULUS10466 flow around the two stages is:

```text
0x08970A90  lhu t3,0x2C8(s6)
...
0x08970B1C  beq t1,t0,0x08971120
...
0x08970B24  lw  a0,0x2C8(s6)
...
0x08970B38  sw  zero,0x2C(sp)
0x08970B40  sw  zero,0x28(sp)
0x08970B44  lw  a1,0x58(sp)
```

The fast path at `0x08970B1C` bypasses `0x08970B24`.

For the slow path that does reach `0x08970B24`:

- `0x28(sp)` is not read between the early hook and B24;
- B40 clears it immediately after B24;
- the authored X/Y values already used by the current late helper are at `0x58(sp)` and `0x5C(sp)`;
- those X/Y stack slots are not consumed by stock code between A90 and B24.

This provides a bounded scratch lifetime inside the same function frame.

## Proposed one-hook architecture

### Game patch 1 — retain the early dynamic hook

Keep:

```text
0x08970A90 -> module early mode-font hook
```

The early hook will continue to perform the same narrow owner and row checks.

### Game patch 2 — replace the late hook with one ordinary instruction

Instead of redirecting `0x08970B24` to plugin code, patch it to:

```text
lw a0,0x28(sp)
```

This is a static instruction substitution, not a second dynamic hook.

The early hook prepares `0x28(sp)` only for the slow-path state that can reach B24.

### Slow-path non-target behavior

For a non-target slow-path invocation:

```text
scratch[0x28] = original packed word from s6+0x2C8
```

Then B24's replacement load reproduces the original value exactly.

### Practice target behavior

For accepted Practice target glyphs:

```text
t3 = corrected horizontal scale
scratch[0x28] = corrected scale value
X unchanged
```

This reproduces the current early+late state without mutating `s6`.

### Gold target behavior

For accepted Gold target glyphs:

```text
t3 = corrected horizontal scale
scratch[0x28] = corrected scale value
X at 0x58(sp) += dynamic Gold anchor shift
```

The current late helper already performs that X shift using the same stack X/Y values.

Moving the write earlier is statically safe because stock code does not consume `0x58(sp)` between A90 and B24.

## Why this is preferable to mutating s6

Do not write the corrected packed scale back to:

```text
s6+0x2C8
```

That state belongs to a shared renderer object and its writer/restoration lifetime is broader than one glyph call.

The stack-scratch design keeps the override local to the active function frame and lets stock code clear the scratch immediately afterward.

## Expected code-space effect

Current dedicated late helper:

```text
module+0x0C00 .. 0x0C3F
= 64 bytes
```

If B24 becomes a direct stack load, this entire helper becomes unnecessary.

The early hook also currently contains dispatch logic used only to distinguish A90 from the B24 late entry. Once B24 no longer calls the hook, those instructions can be repacked.

Expected outcome:

- reclaim the full 64-byte late helper;
- remove late-entry dispatch overhead from the early hook;
- spend some of those savings on bounded scratch preparation and the Gold X shift.

The exact net byte gain must be measured from the generated candidate rather than estimated in advance.

## Existing accepted capacity available to the experiment

Before EXP3:

```text
52 bytes hard-free table tail
24 bytes dead winner-glow X classifier
--------------------------------------
76 bytes general reusable capacity

+ 8 bytes startup-only instruction slots
```

OPT-EXP3 should not need to enlarge the PT_LOAD or use a second LOAD.

Hard invariant:

```text
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Candidate sequence

### OPT-EXP3A — state-equivalence candidate

Implement the one-hook/scratch architecture with minimal repacking.

Do not immediately overwrite all newly dead regions.

Acceptance focus:

1. Practice DAMAGE/HIT COMBO/DAMAGE width and placement;
2. Practice infinity;
3. Gold REWARD width and placement;
4. Gold ATTACK VARIATION width and placement;
5. Gold currency/value rows remain excluded;
6. Arcade/Story/Ghost text unchanged;
7. main menu / pause / character select unchanged;
8. replacement textures/fonts;
9. fast-forward;
10. all accepted battle HUD including winner glow and HP.

### OPT-EXP3B — compaction candidate

Only after EXP3A is device-equivalent:

- zero/reuse the old late helper;
- simplify the compact installer;
- remove the no-longer-needed late-entry dispatch;
- run the space auditor;
- publish the exact new reusable-byte budget.

## Success condition

OPT-EXP3 is accepted only if it:

- behaves identically to OPT-EXP2S3 on device;
- uses one dynamic mode-font hook;
- keeps B24 as a simple static load patch;
- does not mutate persistent s6 text state;
- preserves the 0x0EB0 resident layout;
- produces a positive measured net increase in reusable internal capacity.
