# Stock renderer census: 2026-09-20

This note records the first successful renderer census against a completely stock Tekken 6 USA runtime and separates proven observations from follow-up hypotheses.

The generated JSON remains ignored under `research/captures/` and is not committed.

## Control and transport validation

Runtime:

```text
PPSSPP:       v1.20.4
Game:         TEKKEN 6
Game ID:      ULUS10466
Debugger:     ws://192.168.0.101:39100/debugger
Subprotocol:  debugger.ppsspp.org
```

The first connection attempt failed below WebSocket:

```text
PingSucceeded:     True
TcpTestSucceeded:  False
curl:              connection refused
```

Restarting PPSSPP restored the listener. The same endpoint then returned `PPSSPPServer v0.1`, `/debugger/` redirected to the debugger UI, and the WebSocket smoke test returned version, game status, and a live CPU status.

The loaded-module list contained `tekken` and Sony libraries only. No `Tekken6Ultrawide` module was present. All documented 3D, HUD callsite, and renderer-entry words matched the stock image after disabling PPSSPP JIT replacements during code reads.

Static comparator:

```text
File:       D:\ULUS10466_EBOOT.BIN
SHA-256:   E0ED418952C51032796EBC54584592A9F6075495229F6D12D5065F3186BCB55F
ELF map:   virtual address - file offset = 0x08803000
```

## Debugger compatibility findings

Two probe issues were found without changing Tekken memory:

1. `memory.read_u32` preserved PPSSPP JIT/emuhack words. One stock LUI was observed as `0x6806F1F4`. The verifier now uses `memory.read` with `replacements: false` and decodes the four guest bytes little-endian.
2. The original stop handler required a newer nested `hit` object. PPSSPP v1.20.4 can report only `cpu.stepping` plus a stopped PC/related address. The handler now accepts only addresses owned by the active phase and supports both event shapes.

The frozen PC from the failed first breakpoint run was `0x08928FF4`, proving that breakpoint installation itself was correct and that only event decoding was wrong.

## Capture coverage

The successful run sampled 68 hits.

Useful coverage:

- full-HP battle: rectangle builder, both gauge layers/sides, gauge renderer, downstream HP sprite call, stock submission, and both timer callers;
- partial HP: widths for both players survived at the renderer and final submitter;
- round win: four slot-builder routes, rectangle draws, and four winner-glow conversions;
- Gold Rush: early text/glyph state plus ordinary battle rectangles/HP;
- character select: early common-text state;
- pause: underlying battle HP submission.

Important limitations:

- the per-target cap sampled only the first two stock submissions in each phase, which were HP packets rather than a general sprite census;
- the Gold text cap captured the reward-number string and only the start of `ATTACK VARIATION`, not every target glyph;
- Practice did not hit either documented text stage in this run and needs a focused repeat;
- character-select text samples decoded to `GHOST BATTLE`, so they do not yet identify the cursor/name renderer;
- zero hits at `0x08970B24` are expected in stock code, as shown below, and are not a failed breakpoint.

## 1. Shared slot-builder target

Static code shows `0x0892D9F8` is a thin wrapper:

```text
0x0892D9F8  addiu sp,sp,-0x20
...
0x0892DA04  jal   0x0892D72C
0x0892DA08  sw    v0,0(sp)       ; fifth argument = 1
```

At this shared target, the capture retained:

- the JAL caller return for direct callers;
- slot `a1=0xEF`;
- resource/family ID in `a2`;
- descriptor pointer in `a3`;
- flags in `t0/t1`;
- optional translation/scale pointers in `t2/t3`;
- `f12` and the original stack context.

Round-win examples included resource IDs `0x16`, `0x17`, `0x18`, and `0x13` with distinct caller/descriptor combinations. Descriptor memory still contained authored coordinate pairs such as `82,27` and `397,27`.

Preliminary conclusion:

> The ten JAL caller wrappers are candidates for one conditional hook at `0x0892D9F8`; their caller/resource/descriptor identity survives at the shared target.

The three tail-J routes need separate evidence. Their RA is inherited from the parent rather than identifying the tail-J site, so a consolidated classifier must use resource/descriptor/geometry state and must preserve the existing fifth stack argument.

## 2. HP information at the shared downstream sprite call

The full-HP packet at `0x0892D56C` retained:

```text
packet +0x00: X = 205 (P1) or 275 (P2)
packet +0x04: Y = 21
packet +0x08: Z = 1000
packet +0x18: width = 191
packet +0x20: orientation = -1 (P1) or +1 (P2)
a1:           resource 0x0E or 0x0D
```

The renderer's saved state also retained side/resource IDs:

```text
P1: 8/0x0E and 6/0x0D
P2: 9/0x0E and 7/0x0D
```

In partial-HP samples, the same packet identity survived while `packet+0x18` and `f12` carried player-specific widths around `168.717` and `180.389`.

The callsite delay slot is significant:

```text
0x0892D56C  jal   0x08825EAC
0x0892D570  swc1  f0,0x2C(sp)
```

Preliminary conclusion:

> HP side, resource, X, width, and depletion direction all survive at the existing shared side/rank callsite. Moving HP correction into that dispatcher appears feasible and could remove the upstream gauge-owner wrapper.

The safer consolidation point is the already-hooked `0x0892D56C`/`0x0892D5B0` callsite family, not the global `0x08825EAC` submitter. Any implementation must preserve the delay slot and use an exact HP predicate such as Y/resource/Z/orientation rather than a broad sprite rule.

## 3. Early and late text stages

At `0x08970A90`, each captured glyph retained all of the desired semantic state:

```text
backtrace owner:     0x08973C84
saved a1:            stack +0x54 = 1
authored X/Y:        stack +0x58 / +0x5C
live X/Y scale:      100 / 100
glyph pointer:       s2 (UTF-16)
glyph code:          s3
font/render state:   s6
```

For example, Gold samples carried authored positions such as `399,133` and the UTF-16 text `+1014 G ... ATTACK VARIATION`. Character-select-phase samples carried authored X values `186..260`, Y `150`, and the text `GHOST BATTLE`.

The stock EBOOT explains why `0x08970B24` never fired:

```text
0x08970B1C  beq t1,t0,0x08971120   ; t0=100, stock t1=100
...
0x08970B24  lw  a0,0x2C8(s6)      ; only on non-100 X-scale path
```

The v1.2.0 early hook changes live X scale from 100 to 80. That change makes the branch fall through and activates the later packed-state path. The late hook is therefore a consequence of the early modification, not an independently traversed stock stage.

Preliminary conclusion:

> `0x08970A90` is a genuine pre-split point where owner, authored position, scale, and glyph identity coexist. A one-hook design is plausible, but it must synchronize the live scale and packed/global state that the non-100 slow path consumes. Mutating shared `s6` fields without a proven restore/lifetime rule is not yet safe.

The next text probe should trace writers/lifetime for `s6+0x2C6` and the packed word at `s6+0x2C8`, then test whether one earlier producer can update both values without a second hook.

## 4. Pause and character-select UI

During the pause phase, none of the following captured the pause UI:

```text
0x0892D9F8
0x08AB9380
0x08970A90
0x08970B24
```

The two `0x08825EAC` samples were ordinary underlying HP packets. This is evidence that pause UI is not already covered by these known battle-HUD choke points, although a broader renderer census is still required.

During character select, the known slot/rectangle/stock-sprite paths did not fire. The early text path did fire, but the capped samples represented `GHOST BATTLE`, not enough to classify character names, cursor, or panels.

Preliminary conclusion:

> Pause likely needs a new owner discovery pass. Character select may share the broad text function, but the current samples do not prove that its uncorrected elements reach the v1.2.0 target classifier.

## Next focused work

1. Repeat Practice with a focused text-only capture and enough sampling to include updated combo rows.
2. Repeat Gold with phase-specific filtering/limits so `REWARD` and all of `ATTACK VARIATION` are captured.
3. Trace writes and restoration of `s6+0x2C6` / `s6+0x2C8` to evaluate a one-hook text design.
4. Capture the three tail-J slot routes and map descriptor/resource families at `0x0892D9F8`.
5. Capture side-strip and rank packets at `0x0892D56C` beside HP packets to design one exact downstream dispatcher.
6. Start separate pause/character-select ownership discovery rather than assuming battle renderer coverage.
