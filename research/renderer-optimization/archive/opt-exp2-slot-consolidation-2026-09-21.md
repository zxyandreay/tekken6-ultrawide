# OPT-EXP2 slot-route consolidation — 2026-09-21

## Result

OPT-EXP2 keeps the device-validated OPT-EXP1 downstream HP architecture and consolidates the slot-builder interception from thirteen game callsites to one internal JAL.

The released/OPT-EXP1 architecture patched:

```text
10 JAL callers
3 tail-J callers
        ↓
module+0x05A0 wrapper
        ↓
0x0892D9F8
```

OPT-EXP2 leaves those thirteen callers stock and instead patches:

```text
0x0892DA04
```

inside the common `0x0892D9F8` function.

## Static proof for the 0xEF gate

The authoritative ULUS10466 EBOOT SHA-256 is:

```text
E0ED418952C51032796EBC54584592A9F6075495229F6D12D5065F3186BCB55F
```

The exact stock function is:

```text
0x0892D9F8  addiu sp,sp,-0x20
0x0892D9FC  addiu v0,zero,1
0x0892DA00  sw    ra,0x10(sp)
0x0892DA04  jal   0x0892D72C
0x0892DA08  sw    v0,0(sp)
0x0892DA0C  lw    ra,0x10(sp)
0x0892DA10  jr    ra
0x0892DA14  addiu sp,sp,0x20
```

No instruction before `0x0892DA04` modifies `a1`.

Therefore the new wrapper sees the same slot ID that the old caller wrapper saw. It can preserve the original condition:

```text
a1 == 0xEF
```

exactly.

For non-`0xEF` calls the wrapper tail-jumps directly to `0x0892D72C`, preserving the D9F8 return address and fifth stack argument.

For `0xEF` calls it copies D9F8's stack-passed fifth argument into its outgoing frame, increments the existing rectangle-depth counter, calls `0x0892D72C`, decrements the counter, and returns to D9F8.

## Installer consolidation

The original slot patch table at module-relative `0x0A5C` contained thirteen 12-byte records.

OPT-EXP2 changes the common loop bound from:

```text
13 * 12 = 0x9C
```

to:

```text
1 * 12 = 0x0C
```

and replaces the first record with:

```text
address  = 0x0892DA04
expected = 0x0E24B5CB   ; stock JAL 0x0892D72C
kind     = JAL
```

The remaining twelve records are no longer referenced and are zeroed.

## Compact wrapper

The old caller wrapper occupied:

```text
0x05A0 .. 0x0647
```

The new internal-call wrapper occupies:

```text
0x05A0 .. 0x05FF
```

with code ending at `0x05FC`.

The tail:

```text
0x0600 .. 0x0647
```

is now unused.

The remaining depth-counter HI16/LO16 relocation pair was moved to the new compact wrapper. The second old pair was changed to `R_MIPS_NONE`.

## Reclaimed capacity

The PRX allocation intentionally remains unchanged:

```text
file size = 5626 bytes
one PT_LOAD
p_filesz  = 0x0EB0
p_memsz   = 0x0EB0
```

But OPT-EXP2 creates newly unreferenced capacity inside that fixed image:

```text
unused slot table records: 144 bytes
unused old-wrapper tail:     72 bytes
---------------------------------
total:                      216 bytes
```

That is approximately 5.7% of the 0x0EB0 PT_LOAD.

The bytes are left inside the same resident allocation specifically so later corrections can reuse them without enlarging `p_memsz`.

## Test artifact

```text
OPT-EXP2 PRX SHA-256:
21eb39873ddf1bc335e2fbb519bc8a6e21e7484aa0beb50d864559907504428a
```

## Required validation

Cold-boot an official PPSSPP release after replacing the PRX.

The critical OPT-EXP2 checks are:

1. HP shell/frame placement;
2. P1/P2 character names;
3. round rails/orbs, including the immediate earned orb;
4. center timer;
5. ranks and side strips;
6. winner effects;
7. Practice and Gold Rush text;
8. replacement textures/fonts;
9. main menu, pause and character select for collateral;
10. fast-forward and normal input.

If behavior matches OPT-EXP1/v1.2.0, the thirteen caller-level slot hooks are redundant and the 216-byte region can become the first confirmed reclaimed capacity for further HUD work.
