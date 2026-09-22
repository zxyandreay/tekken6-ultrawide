#!/usr/bin/env python3
"""Build OPT-EXP2R2 (scope-equivalent slot consolidation) from v1.2.0.

Background
----------
OPT-EXP2 broadened the slot 0xEF scope and also clobbered live renderer inputs.
OPT-EXP2R fixed the ABI clobber, which restored the normal orange appearance, but
the win-burst halo/orb relationship still differed from v1.2.0/OPT-EXP1.

The v1.2.0 round-win design intentionally has two scope classes:
- persistent/owned round-marker routes run inside the broad slot-0xEF scope;
- the newly-earned late orb is submitted with scope depth == 0 and is handled by
  the narrow y=27/x-range late-orb predicate.

This build preserves that boundary while still reducing caller patches.

Design
------
- Keep the 3 original tail-J slot routes wrapped externally.
- Restore the 10 original direct JAL routes to stock.
- Patch the common internal call at 0x0892DA04 once.
- At that internal hook, open the broad scope only if the D9F8-saved caller
  actually came from a stock direct JAL to D9F8 (word at saved_ra-8 == 0x0E24B67E).
- Calls entering through the 3 external tail wrappers use a trampoline, so their
  saved_ra-8 is intentionally not the stock JAL word and the internal hook does
  not double-scope them.
- Indirect/dynamic D9F8 calls likewise remain outside the broad scope, allowing
  the existing late-orb predicate to handle them as in v1.2.0.

The winner-glow converter and late-orb rectangle code are not modified.
The one-PT_LOAD 0x0EB0/0x0EB0 layout is preserved.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

import build_opt_exp1 as exp1

TEXT_FILE_OFFSET = exp1.TEXT_FILE_OFFSET
REL_TEXT_FILE_OFFSET = exp1.REL_TEXT_FILE_OFFSET
REL_TEXT_SIZE = exp1.REL_TEXT_SIZE

OPT_EXP1_SHA256 = "91f84acad1047b80b474fe1b2f6df12888c9312fb0b9be34cfae45ff095495fa"
OPT_EXP2R2_SHA256 = "b6570ddc1127ce12cef02643b5f16703af01badd8728aa42624c177e42760b8c"

def patch_exp2r2(prx: bytes) -> bytes:
    data = bytearray(exp1.patch_prx(prx))
    if hashlib.sha256(data).hexdigest() != OPT_EXP1_SHA256:
        raise RuntimeError("OPT-EXP1 base hash mismatch")

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    expected = {
        0x0280: 0x2611009C,
        0x05A0: 0x27BDFFC0,
        0x0610: 0x0E24B67E,
        0x0644: 0x27BD0040,
        0x0A5C: 0x08929854,
        0x0A60: 0x0E24B67E,
        0x0A64: 0x00000001,
    }
    for va, wanted in expected.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(f"unexpected OPT-EXP1 word at {va:#x}: {got:#010x} != {wanted:#010x}")

    # Installer table now contains:
    #   1 common internal JAL + the 3 original tail-J routes.
    # All four still target module+0x5A0; that entry dispatches by current RA.
    write_word(0x0280, exp1.i_type(9, 16, 17, 0x0030))
    records = (
        (0x0892DA04, 0x0E24B5CB, 1),
        (0x08929228, 0x0A24B67E, 0),
        (0x089292F4, 0x0A24B67E, 0),
        (0x08929D4C, 0x0A24B67E, 0),
    )
    cursor = 0x0A5C
    for address, expected_word, kind in records:
        for word in (address, expected_word, kind):
            write_word(cursor, word)
            cursor += 4
    for va in range(cursor, 0x0A8C, 4):
        write_word(va, 0)

    # Replace the original universal caller wrapper with a two-mode dispatcher.
    #
    # Internal entry:
    #   0x0892DA04 JAL -> current RA == 0x0892DA0C -> branch to module+0xA8C.
    #
    # Tail-J entry:
    #   inherited RA != 0x0892DA0C -> compact outer wrapper below.
    for va in range(0x05A0, 0x0648, 4):
        write_word(va, 0)

    tail = {
        0x05A0: exp1.i_type(0x0F, 0, 12, 0x0893),                 # lui t4,0x0893
        0x05A4: exp1.i_type(9, 12, 12, -0x25F4),                  # t4=0x0892DA0C
        0x05A8: exp1.branch(4, 31, 12, 0x05A8, 0x0628),           # internal entry?
        0x05AC: 0,

        # Compact tail-J wrapper. Preserve inherited RA and fifth stack arg.
        0x05B0: exp1.i_type(9, 29, 29, -0x20),
        0x05B4: exp1.i_type(0x2B, 29, 31, 0x1C),
        0x05B8: exp1.i_type(0x23, 29, 12, 0x20),                  # old 0(sp)
        0x05BC: exp1.i_type(0x2B, 29, 12, 0x00),                  # forwarded fifth arg
        0x05C0: exp1.i_type(0x2B, 29, 0, 0x18),                   # scoped flag=0
        0x05C4: exp1.i_type(9, 0, 12, 0x00EF),
        0x05C8: exp1.branch(5, 5, 12, 0x05C8, 0x05EC),
        0x05CC: 0,
        0x05D0: exp1.i_type(9, 0, 13, 1),
        0x05D4: exp1.i_type(0x2B, 29, 13, 0x18),                  # scoped flag=1
        0x05D8: exp1.i_type(0x0F, 0, 12, 0x0880),
        0x05DC: exp1.i_type(9, 12, 12, 0x0C44),
        0x05E0: exp1.i_type(0x23, 12, 13, 0),
        0x05E4: exp1.i_type(9, 13, 13, 1),
        0x05E8: exp1.i_type(0x2B, 12, 13, 0),

        # Call a tiny trampoline rather than D9F8 directly. This deliberately
        # makes saved_ra-8 differ from stock JAL-D9F8 so the internal classifier
        # does not open a second scope.
        0x05EC: exp1.j_type(3, 0x08800640),
        0x05F0: 0,

        0x05F4: exp1.i_type(0x23, 29, 13, 0x18),
        0x05F8: exp1.branch(4, 13, 0, 0x05F8, 0x0614),
        0x05FC: 0,
        0x0600: exp1.i_type(0x0F, 0, 12, 0x0880),
        0x0604: exp1.i_type(9, 12, 12, 0x0C44),
        0x0608: exp1.i_type(0x23, 12, 13, 0),
        0x060C: exp1.i_type(9, 13, 13, -1),
        0x0610: exp1.i_type(0x2B, 12, 13, 0),
        0x0614: exp1.i_type(0x23, 29, 31, 0x1C),
        0x0618: exp1.r_type(31, 0, 0, 0, 8),
        0x061C: exp1.i_type(9, 29, 29, 0x20),

        # Internal entry gateway.
        0x0628: exp1.branch(4, 0, 0, 0x0628, 0x0A8C),
        0x062C: 0,

        # Tail wrapper trampoline: J does not change the RA created by JAL 0x0640.
        0x0640: exp1.j_type(2, 0x0892D9F8),
        0x0644: 0,
    }
    for va, word in tail.items():
        write_word(va, word)

    # Internal direct-JAL classifier lives in the now-unreferenced table tail.
    # It opens the broad slot scope only for calls whose original saved caller
    # instruction is the stock JAL to D9F8. Indirect/dynamic calls pass through
    # with scope depth unchanged, restoring the late-orb phase boundary.
    internal = {
        0x0A8C: exp1.i_type(9, 0, 12, 0x00EF),
        0x0A90: exp1.branch(5, 5, 12, 0x0A90, 0x0AE8),
        0x0A94: exp1.i_type(0x23, 29, 12, 0x10),               # D9F8-saved caller RA
        0x0A98: exp1.i_type(9, 12, 13, -8),
        0x0A9C: exp1.i_type(0x23, 13, 13, 0),                  # word at saved_ra-8
        0x0AA0: exp1.i_type(0x0F, 0, 12, 0x0E24),
        0x0AA4: exp1.i_type(0x0D, 12, 12, 0xB67E),             # 0x0E24B67E
        0x0AA8: exp1.branch(5, 13, 12, 0x0AA8, 0x0AE8),
        0x0AAC: 0,

        0x0AB0: exp1.i_type(0x0F, 0, 12, 0x0880),
        0x0AB4: exp1.i_type(9, 12, 12, 0x0C44),
        0x0AB8: exp1.i_type(0x23, 12, 13, 0),
        0x0ABC: exp1.i_type(9, 13, 13, 1),
        0x0AC0: exp1.i_type(0x2B, 12, 13, 0),
        0x0AC4: exp1.j_type(3, 0x0892D72C),
        0x0AC8: 0,
        0x0ACC: exp1.i_type(0x0F, 0, 12, 0x0880),
        0x0AD0: exp1.i_type(9, 12, 12, 0x0C44),
        0x0AD4: exp1.i_type(0x23, 12, 13, 0),
        0x0AD8: exp1.i_type(9, 13, 13, -1),
        0x0ADC: exp1.i_type(0x2B, 12, 13, 0),
        0x0AE0: exp1.j_type(2, 0x0892DA0C),
        0x0AE4: 0,

        # Pass-through path keeps the stock D9F8 return address (0x0892DA0C).
        0x0AE8: exp1.j_type(2, 0x0892D72C),
        0x0AEC: 0,
    }
    for va, word in internal.items():
        write_word(va, word)
    write_word(0x0AF0, 0)
    write_word(0x0AF4, 0)

    # The rewritten scope code uses absolute 0x08800C44 loads, so the four
    # released module-local relocation entries for the old wrapper must not
    # rewrite these instructions.
    wanted_offsets = {0x05D8, 0x05DC, 0x0628, 0x062C}
    found = set()
    for pos in range(REL_TEXT_FILE_OFFSET, REL_TEXT_FILE_OFFSET + REL_TEXT_SIZE, 8):
        offset, info = struct.unpack_from("<II", data, pos)
        if offset in wanted_offsets:
            found.add(offset)
            struct.pack_into("<I", data, pos + 4, 0)
    if found != wanted_offsets:
        raise RuntimeError(f"expected old slot-wrapper relocations not found: {sorted(found)}")

    # Resident-layout invariant.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError(f"resident layout changed: type={ph[0]} filesz={ph[4]:#x} memsz={ph[5]:#x}")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OPT_EXP2R2_SHA256:
        raise RuntimeError("OPT-EXP2R2 output hash mismatch")
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP2R2.prx"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    output = patch_exp2r2(exp1.read_release_prx(root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")
    print("Slot caller patches: 13 -> 4")
    print("Winner-glow and late-orb correction code unchanged")

if __name__ == "__main__":
    main()
