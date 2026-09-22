# OPT-EXP3A one-hook-font checkpoint — 2026-09-21

## Corrected status

Accepted for the Practice/Gold one-hook font architecture, but **NOT accepted as proof of winner-glow correctness**.

Build:

```text
Tekken6Ultrawide-OPT-EXP3A-OneHookScratch.prx

SHA-256:
46063c6097e3dfaa51aafd077e0e5c65f02487bdbe420f8884f2a292edf8cf1f

file size = 5626 bytes
one PT_LOAD
p_filesz = p_memsz = 0x0EB0
```

## Device-result correction

Initial testing reported no visible regressions and was interpreted as including the winner glow.

A later deliberate recheck showed that the spinning winner/earned-round halo was already on the wrong orb in EXP3A.

Therefore:

- Practice/Gold one-hook behavior remains device-validated;
- startup/loading remains good;
- general battle HUD remains good;
- EXP3A does **not** establish a correct winner-glow baseline.

## Validated font architecture

Dynamic mode-font game hooks:

```text
before: 0x08970A90 + 0x08970B24
after:  0x08970A90 only
```

Late site:

```text
0x08970B24 -> lw a0,0x28(sp)
```

The bounded stack scratch is cleared by stock code and persistent s6 text state is not mutated.

This architecture may continue to be used for optimization work after the halo investigation is separated from it.

## Winner-glow rule

Do not use EXP3A or any descendant as evidence that the halo is fixed unless a dedicated round-win test explicitly verifies:

- P1 first win;
- P2 first win;
- later earned slots where practical;
- spinning halo center relative to the newly lit orb.

No GitHub Actions are used.
