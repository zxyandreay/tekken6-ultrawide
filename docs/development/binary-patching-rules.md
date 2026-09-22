# Binary Patching Rules

**Status:** CURRENT

## Deterministic parent

Every experimental builder should require an exact parent SHA-256 and reject unexpected input.

For the current release baseline:

```text
v1.2.1 / OPT-EXP4A
PRX SHA-256:
6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8
```

## Before patching a hook

Document:

- hook address;
- exact stock word;
- delay-slot word;
- J/JAL/tail-J behavior;
- RA meaning;
- stack-pointer state;
- fifth+ stack arguments;
- live GPR/FPU inputs;
- state visible after return.

Do not rely only on generic MIPS ABI assumptions; preserve the behavior of the exact replaced path.

## Module addressing

Never hard-code a PRX runtime load address. Use relocation-safe module-local or proven PC-relative techniques.

## Cache/install discipline

If startup code patches executable game instructions:

- validation/install/cache walkers must agree on record layout and bounds;
- preserve instruction/data cache maintenance;
- verify every expected stock word before writing.

## Layout guard

Builders should verify:

```text
one PT_LOAD
p_filesz = 0x0EB0
p_memsz  = 0x0EB0
```

unless the experiment is specifically a memory-layout study.

## Frozen regions

Unrelated experiments should byte-guard accepted subsystems, especially winner-glow and the compact font/slot helpers.

Historical builders live under [`tools/research/builders/archive/`](../../tools/research/builders/archive/). They are evidence/reproduction tools, not the current source of truth.
