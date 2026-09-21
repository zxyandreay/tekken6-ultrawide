# OPT-EXP3A accepted checkpoint — 2026-09-21

## Status

Accepted on device.

Build:

```text
Tekken6Ultrawide-OPT-EXP3A-OneHookScratch.prx

SHA-256:
46063c6097e3dfaa51aafd077e0e5c65f02487bdbe420f8884f2a292edf8cf1f

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Device result

User testing reported no visible regressions in EXP3A.

Observed result:

- Practice/Gold text behavior appears correct;
- no visible battle-HUD regression;
- no visible winner-orb/glow regression;
- no visible startup/loading regression.

This validates the one-dynamic-hook Practice/Gold architecture well enough to proceed to a pure compaction candidate.

## Validated architecture

Dynamic mode-font game hooks:

```text
before: 0x08970A90 + 0x08970B24
after:  0x08970A90 only
```

The late site is a static instruction patch:

```text
0x08970B24 -> lw a0,0x28(sp)
```

The early hook prepares a bounded stack scratch for the slow path and preserves stock behavior on the fast path.

Persistent `s6` text state is not mutated.

## Next step

OPT-EXP3B may now compact the proven architecture without changing semantics:

- move the 52-byte helper into the proven 52-byte table-tail cave;
- retarget only the three internal branches that call that helper;
- zero the old 64-byte helper region;
- zero the already-proven unreachable 24-byte old winner-glow X block;
- keep all other accepted code unchanged.

No GitHub Actions are used.
