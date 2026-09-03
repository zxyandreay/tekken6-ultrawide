# Address Map

Last updated: 2026-09-03

Status labels used here:

- VERIFIED: confirmed directly from local files or reproducible commands.
- STRONG EVIDENCE: supported by static analysis but not fully proven.
- HYPOTHESIS: plausible but unverified.
- REJECTED: investigated and found unsuitable or false.

## CWCheat Mapping Rule

VERIFIED:

- The high nibble of a CWCheat write code is the code type, not part of the target address.
- For the known `0x2` 32-bit write codes, the target PSP user-memory offset is `code & 0x0FFFFFFF`.
- For these EBOOT-resident addresses, PSP runtime address is `0x08800000 + (code & 0x0FFFFFFF)`.
- With `ULUS10466_EBOOT.BIN`, runtime-to-file mapping uses the load segment:
  - segment virtual address: `0x08804018`
  - segment file offset: `0x00001018`
  - file offset = `runtime_address - 0x08804018 + 0x00001018`
  - equivalently for these addresses, file offset = `runtime_address - 0x08803000`
- This rule was verified by finding the expected original restore instruction words at all eight known 3D aspect patch locations.

## Known CWCheat Patch Sites

These addresses come from the known-good `ULUS10466.ini`.

| Status | CWCheat address | PSP user offset | PSP runtime address | EBOOT file offset | Replacement instruction | Original instruction | Purpose |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VERIFIED | `0x20145F10` | `0x00145F10` | `0x08945F10` | `0x00142F10` | `0x3C01400E` | `0x3C013FE3` | Constructs aspect constant; exact function unknown |
| VERIFIED | `0x20145F14` | `0x00145F14` | `0x08945F14` | `0x00142F14` | `0x342138E4` | `0x34218E39` | Constructs aspect constant; exact function unknown |
| VERIFIED | `0x20146794` | `0x00146794` | `0x08946794` | `0x00143794` | `0x3C01400E` | `0x3C013FE3` | Constructs aspect constant; exact function unknown |
| VERIFIED | `0x20146798` | `0x00146798` | `0x08946798` | `0x00143798` | `0x342138E4` | `0x34218E39` | Constructs aspect constant; exact function unknown |
| VERIFIED | `0x20146BC8` | `0x00146BC8` | `0x08946BC8` | `0x00143BC8` | `0x3C01400E` | `0x3C013FE3` | Constructs aspect constant; exact function unknown |
| VERIFIED | `0x20146BCC` | `0x00146BCC` | `0x08946BCC` | `0x00143BCC` | `0x342138E4` | `0x34218E39` | Constructs aspect constant; exact function unknown |
| VERIFIED | `0x20147D90` | `0x00147D90` | `0x08947D90` | `0x00144D90` | `0x3C01400E` | `0x3C013FE3` | Constructs aspect constant; exact function unknown |
| VERIFIED | `0x20147D94` | `0x00147D94` | `0x08947D94` | `0x00144D94` | `0x342138E4` | `0x34218E39` | Constructs aspect constant; exact function unknown |

## Known Optional Camera Site

This is documented for completeness only. It is explicitly out of scope for initial plugin work.

| Status | CWCheat address | Values | Purpose |
| --- | --- | --- | --- |
| VERIFIED cheat entry | `0x1015350C` | `0x3F80`, `0x3F81`, `0x3F82`, `0x3F83` | Camera width adjustment; exact representation and function unknown |

## Aspect Pair Occurrences

VERIFIED:

- The original 16:9 instruction pair byte sequence appears exactly four times in `ULUS10466_EBOOT.BIN`.
- The four occurrences are the same four sites referenced by the known CWCheat.
- The patched 20:9 instruction pair byte sequence does not appear in the original EBOOT.

| Pair | Count | EBOOT file offsets |
| --- | ---: | --- |
| Original `0x3C013FE3 0x34218E39` | 4 | `0x00142F10`, `0x00143794`, `0x00143BC8`, `0x00144D90` |
| Patched `0x3C01400E 0x342138E4` | 0 | none |

## Mapping Work Still Required

The address conversion above is verified for the eight known EBOOT-resident 3D aspect instructions. The containing functions, callers, and rendering-mode meanings are not yet identified.

## Pattern Signatures

No reusable signatures have been derived yet.
