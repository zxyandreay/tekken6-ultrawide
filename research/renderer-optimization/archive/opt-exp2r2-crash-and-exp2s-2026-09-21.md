# OPT-EXP2R2 crash analysis and OPT-EXP2S safe optimization — 2026-09-21

## Device result

OPT-EXP2R2 is rejected.

Observed behavior:

- game launch/loading succeeds;
- fighter intro succeeds;
- PPSSPP force-closes immediately before the battle HUD becomes visible.

That timing points directly at the slot-hook path first exercised when the fight HUD starts rendering.

## Crash cause in EXP2R2

EXP2R2 introduced a local trampoline using a hard-coded PRX-local address:

```text
jal 0x08800640
```

and also introduced new fixed `0x0880....` references for module-local state.

That is not valid architecture for this PRX. The module is relocatable and the released v1.2.0 implementation uses relocation entries for module-local pointers. A fixed local jump can therefore target the wrong runtime address when the tail route is first executed.

EXP2R2 also placed executable classifier code in the former slot-table tail. Although the LOAD segment is executable, this added another unnecessary runtime variable while the underlying slot-consolidation semantics were still not proven safe.

Because EXP2 and EXP2R had already demonstrated round-win regressions, the next test deliberately stops changing battle-time slot topology.

## OPT-EXP2S strategy

OPT-EXP2S returns battle-time rendering to the validated OPT-EXP1/v1.2.0 topology.

It keeps:

- all 13 original slot callsite hooks;
- the original module+0x05A0 slot wrapper;
- the original slot scope lifetime;
- the existing late earned-orb predicate;
- the dedicated winner-glow converter;
- OPT-EXP1 downstream HP consolidation.

The optimization is startup-only.

### Patch-table compression

The released/OPT-EXP1 slot installer stored 13 records as:

```text
address       4 bytes
expected word 4 bytes
kind          4 bytes
--------------------
record       12 bytes
```

The `kind` field is redundant because the expected instruction already encodes whether the site is J or JAL:

```text
0x0E24B67E -> JAL
0x0A24B67E -> J
```

OPT-EXP2S therefore stores only:

```text
address       4 bytes
expected word 4 bytes
--------------------
record        8 bytes
```

The startup validator/installer derives the replacement opcode from:

```text
expected_word >> 26
```

and combines it with the same relocation-safe wrapper target bits already used by v1.2.0.

## Capacity reclaimed

```text
13 * 12 = 156 bytes   old table
13 *  8 = 104 bytes   compressed table
---------------------------------------
            52 bytes   reclaimed
```

The freed region is contiguous:

```text
module-relative 0x0AC4 .. 0x0AF7
```

No battle-time code is placed there in OPT-EXP2S.

## Static equivalence proof

OPT-EXP2S was compared byte-for-byte with OPT-EXP1.

The entire runtime region:

```text
module 0x05A0 .. 0x0933
```

is identical.

That includes:

- slot wrapper;
- rectangle hook and late-orb classifier;
- HP downstream handler;
- side/rank handler;
- timer hooks;
- winner-glow hook;
- Practice/Gold text implementation.

Only:

- startup installer instructions;
- slot patch table representation;

are changed.

The compressed installer was also simulated against both stock callsite words and already-patched callsite words; both validation cases produce the same 13 wrapper instructions as OPT-EXP1.

## Binary invariant

```text
SHA-256:
a43777202277145acc28fa7d4a41848e7be63413fd43210c8ad8dee8455737ad

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Acceptance test

Because battle-time code is identical to OPT-EXP1, first verify the previous failure boundary:

1. enter a fight and confirm no crash when the HUD appears;
2. P1/P2 first-win orb and halo match OPT-EXP1;
3. HP, ranks/strips, timer and names match;
4. Practice/Gold text;
5. replacement textures/fonts;
6. fast-forward.

If this passes, the 52-byte table tail becomes validated reusable internal capacity without changing battle rendering.
