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

## Aspect Dispatch Tables

STRONG EVIDENCE:

- The four patched aspect pairs are selected through six-entry dispatch tables.
- All four dispatches use case/index `0` for the original 16:9 constant.
- Case/index `1` is 4:3 (`0x3FAAAAAB`, approximately `1.3333334`).
- Case/index `2` is 3:2 (`0x3FC00000`, `1.5`).
- Case/index `3` is 1:1 (`0x3F800000`, `1.0`).
- Case/index `4` is a near-16:9 value (`0x3FE2AAAB`, approximately `1.7708334`).
- Case/index `5` loads a custom aspect value from a structure field rather than using an inline constant.

This suggests the patched sites are part of an internal aspect-mode selection system.

| Dispatch | Selector evidence | Jump table runtime | Jump table file offset | Case 0 target | Case 5 target |
| --- | --- | --- | --- | --- | --- |
| `aspect_dispatch_1` | loads selector from `0x38($a0)` | `0x08B9E420` | `0x0039B420` | `0x08945F10` | `0x08945F08`, loads `0x3c($a1)` |
| `aspect_dispatch_2` | loads selector from `0x38($s0)` | `0x08B9E438` | `0x0039B438` | `0x08946794` | `0x08946870`, loads `0x3c($s0)` |
| `aspect_dispatch_3` | loads selector from `0x38($v0)` after object lookup | `0x08B9E450` | `0x0039B450` | `0x08946BC4` | `0x08946BB4`, loads `0x3c($a1)` |
| `aspect_dispatch_4` | loads selector from `0x38($s3)` | `0x08B9E550` | `0x0039B550` | `0x08947D90` | `0x08947B90`, loads `0x3c($s3)` |

## Disassembly Notes

STRONG EVIDENCE:

- `aspect_dispatch_1` begins at `0x08945ED4` and returns the selected aspect in `$f0`.
- `aspect_dispatch_2` begins at `0x089466EC`; before the dispatch it converts a value at `0x34($s0)` using `65536.0 / 360.0`, then passes the selected aspect in `$f12` with values from `0x2c($s0)` and `0x30($s0)` to a call at `0x08ACA6C4`.
- `aspect_dispatch_3` begins at `0x08946B6C`, resolves an object through `0xa4($a0)` and `0x6c($a0)`, then returns the selected aspect in `$f0`.
- `aspect_dispatch_4` dispatches at `0x08947B58`; selected constants are used as divisors in `div.s $f0, $f2, $f0` before common code at `0x08947B98` multiplies by `0x3C8EFA35`, approximately degrees-to-radians.

HYPOTHESIS:

- `aspect_dispatch_2` and `aspect_dispatch_4` are directly involved in projection or camera/frustum setup.
- `aspect_dispatch_1` and `aspect_dispatch_3` may be aspect getter/helper paths used by higher-level projection code.

## Pattern Signatures

VERIFIED:

- The exact original aspect pair `0x3C013FE3 0x34218E39` appears exactly four times in the original EBOOT.
- A conservative first plugin implementation could scan for exactly four occurrences of this two-instruction pair, verify that all mapped locations match the known runtime addresses for `ULUS10466`, and patch only if the count and instructions match.

HYPOTHESIS:

- Per-dispatch signatures should include nearby switch/custom-aspect context and wildcard absolute branch/jump targets where needed.
- Do not rely only on the two-instruction pair if future versions or regions contain additional identical constants.
