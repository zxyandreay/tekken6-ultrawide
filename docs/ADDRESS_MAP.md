# Address Map

Last updated: 2026-09-03

Status labels used here:

- VERIFIED: confirmed directly from local files or reproducible commands.
- STRONG EVIDENCE: supported by static analysis but not fully proven.
- HYPOTHESIS: plausible but unverified.
- REJECTED: investigated and found unsuitable or false.

## Known CWCheat Patch Sites

These addresses come from the known-good `ULUS10466.ini`. The CWCheat addresses are known, but their PSP runtime addresses, EBOOT virtual addresses, file offsets, and containing functions have not yet been mapped.

| Status | CWCheat address | Replacement instruction | Restore instruction | Purpose |
| --- | --- | --- | --- | --- |
| VERIFIED cheat entry | `0x20145F10` | `0x3C01400E` | `0x3C013FE3` | Constructs aspect constant; exact function unknown |
| VERIFIED cheat entry | `0x20145F14` | `0x342138E4` | `0x34218E39` | Constructs aspect constant; exact function unknown |
| VERIFIED cheat entry | `0x20146794` | `0x3C01400E` | `0x3C013FE3` | Constructs aspect constant; exact function unknown |
| VERIFIED cheat entry | `0x20146798` | `0x342138E4` | `0x34218E39` | Constructs aspect constant; exact function unknown |
| VERIFIED cheat entry | `0x20146BC8` | `0x3C01400E` | `0x3C013FE3` | Constructs aspect constant; exact function unknown |
| VERIFIED cheat entry | `0x20146BCC` | `0x342138E4` | `0x34218E39` | Constructs aspect constant; exact function unknown |
| VERIFIED cheat entry | `0x20147D90` | `0x3C01400E` | `0x3C013FE3` | Constructs aspect constant; exact function unknown |
| VERIFIED cheat entry | `0x20147D94` | `0x342138E4` | `0x34218E39` | Constructs aspect constant; exact function unknown |

## Known Optional Camera Site

This is documented for completeness only. It is explicitly out of scope for initial plugin work.

| Status | CWCheat address | Values | Purpose |
| --- | --- | --- | --- |
| VERIFIED cheat entry | `0x1015350C` | `0x3F80`, `0x3F81`, `0x3F82`, `0x3F83` | Camera width adjustment; exact representation and function unknown |

## Mapping Work Still Required

HYPOTHESIS:

- CWCheat code type prefixes need to be translated into PSP memory writes before file offsets can be derived.
- The EBOOT load segment at virtual address `0x08804018` and file offset `0x00001018` will be central to mapping runtime addresses to file offsets.

Do not use these hypotheses as patch targets until the relationship is verified against actual bytes and disassembly.

## Pattern Signatures

No reusable signatures have been derived yet.
