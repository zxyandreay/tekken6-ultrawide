# Accepted internal-space audit — OPT-EXP4A — 2026-09-22

## Authoritative baseline

```text
OPT-EXP4A — SlotScopeCompact
SHA-256:
6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

Resident allocation reduction:

```text
0 bytes
```

The fixed one-LOAD 0x0EB0 mapping remains part of runtime correctness.

## Accepted general-purpose hard-free capacity

### Region A — compacted slot-wrapper tail

OPT-EXP4A reduced the live slot-scope wrapper and left:

```text
0x0604 .. 0x0647
72 bytes
```

fully detached and zero.

Device validation passed the complete HUD/font/texture/fast-forward regression sweep.

Classification:

```text
72 bytes accepted general-purpose hard-free
```

### Region B — old Practice/Gold helper allocation

The live one-hook helper remains relocated to the former table tail.

Its old allocation remains:

```text
0x0C00 .. 0x0C3F
64 bytes
```

detached and zero.

Classification:

```text
64 bytes accepted general-purpose hard-free
```

## Authoritative hard-free total

```text
0x0604..0x0647   72 bytes
0x0C00..0x0C3F   64 bytes
-------------------------
accepted total   136 bytes
```

## Startup-inline opportunity

The removed upstream HP installer still leaves:

```text
0x03F0 .. 0x03F7
8 bytes
```

inside straight-line startup execution.

Classification:

```text
startup-only inline opportunity
NOT general hard-free space
```

Do not add these 8 bytes to the 136-byte general free-space figure.

## Regions that are live and must not be counted

### Former compressed-table tail

```text
0x0AC4 .. 0x0AF7
```

Contains the live Practice/Gold one-hook helper.

Free capacity:

```text
0 bytes
```

### Winner-glow classifier

The winner-glow ownership/predicate area is live and frozen after EXP3C/EXP3D-A.

Free capacity:

```text
0 bytes
```

Do not reclaim or repack it as part of unrelated work.

## Historical numbers that are obsolete

Do not cite as current accepted hard-free capacity:

- 52-byte pre-EXP3B table-tail cave;
- 24-byte proposed glow block;
- 76/84-byte EXP2S3 opportunity totals;
- 216/236-byte rejected runtime-consolidation estimates.

## Release implication

136 bytes of device-validated detached capacity is sufficient headroom for a maintenance release.

There is no current functional need to continue optimizing before release.

Further optimization should be driven by a concrete future requirement rather than by maximizing the free-byte count.

No GitHub Actions are used.
