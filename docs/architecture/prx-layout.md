# PRX Layout and Runtime Constraints

**Status:** CURRENT / ACCEPTED  
**Authoritative release:** v1.2.1 / OPT-EXP4A

```text
Tekken6Ultrawide.prx
SHA-256:
6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8

file size: 5626 bytes
PT_LOAD count: 1
p_filesz: 0x0EB0
p_memsz:  0x0EB0
```

The fixed single-LOAD `0x0EB0` footprint is treated as part of compatibility, not just a size preference.

Earlier enlarged experimental modules correlated with unrelated replacement-texture and fast-forward regressions. New HUD work should therefore fit inside the accepted mapping unless a dedicated memory-layout study independently proves a safe change.

## Accepted detached capacity

```text
0x0604..0x0647   72 bytes
0x0C00..0x0C3F   64 bytes
-------------------------
general total    136 bytes
```

There is also:

```text
0x03F0..0x03F7    8 bytes
```

of startup-inline opportunity. It is **not** general-purpose detached space and must not be added to the 136-byte total.

## What the 136 bytes mean

This is module-side headroom for helpers, classifiers, small tables, or state. It is not a hard count of how many game callsites can be patched.

Prefer:

1. extending an existing safe choke point;
2. one shared helper/dispatcher;
3. data-driven classification;
4. only then a new wrapper.

See the accepted [space audit](../../research/renderer-optimization/findings/space-audit.md).
