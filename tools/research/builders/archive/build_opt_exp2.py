#!/usr/bin/env python3
"""Build OPT-EXP2 from the device-validated OPT-EXP1 architecture.

OPT-EXP2 keeps OPT-EXP1's downstream HP consolidation and collapses the thirteen
slot-builder caller hooks to the single internal JAL at Tekken 6 USA 0x0892DA04.

The exact stock function at 0x0892D9F8 is:
    addiu sp,sp,-0x20
    addiu v0,zero,1
    sw    ra,0x10(sp)
    jal   0x0892D72C
    sw    v0,0(sp)
    ...
so a1 (the slot id) is unchanged at the internal call. The compact wrapper therefore
preserves the original slot==0xEF gate exactly.

The validated one-PT_LOAD 0x0EB0/0x0EB0 layout is preserved.
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
OPT_EXP2_SHA256 = "21eb39873ddf1bc335e2fbb519bc8a6e21e7484aa0beb50d864559907504428a"

def patch_exp2(prx: bytes) -> bytes:
    data = bytearray(exp1.patch_prx(prx))
    if hashlib.sha256(data).hexdigest() != OPT_EXP1_SHA256:
        raise RuntimeError("OPT-EXP1 base hash mismatch")

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    # Verify the exact OPT-EXP1 slot installer/wrapper we are replacing.
    expected = {
        0x0280: 0x2611009C,  # table end = start + 13*12
        0x05A0: 0x27BDFFC0,
        0x0610: 0x0E24B67E,  # old wrapper calls 0x0892D9F8
        0x0644: 0x27BD0040,
        0x0A5C: 0x08929854,
        0x0A60: 0x0E24B67E,
        0x0A64: 0x00000001,
    }
    for va, wanted in expected.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(f"unexpected OPT-EXP1 word at {va:#x}: {got:#010x} != {wanted:#010x}")

    # Both the validation and installation loops use this same table bound.
    # Collapse 13 route records to one record for the shared internal JAL.
    write_word(0x0280, exp1.i_type(9, 16, 17, 0x000C))
    write_word(0x0A5C, 0x0892DA04)
    write_word(0x0A60, 0x0E24B5CB)  # stock JAL 0x0892D72C
    write_word(0x0A64, 1)           # install a JAL to module+0x5A0
    for va in range(0x0A68, 0x0AF8, 4):
        write_word(va, 0)

    # Compact shared slot wrapper at module+0x5A0.
    #
    # Non-0xEF slot:
    #   tail-jump directly to stock 0x0892D72C, preserving D9F8's RA and stack arg.
    #
    # Slot 0xEF:
    #   forward the fifth stack argument, increment the existing scoped rectangle
    #   depth, call stock 0x0892D72C, decrement depth, then return to D9F8.
    wrapper = {
        0x05A0: exp1.i_type(9, 0, 8, 0x00EF),
        0x05A4: exp1.branch(5, 5, 8, 0x05A4, 0x05F8),
        0x05A8: 0,
        0x05AC: exp1.i_type(9, 29, 29, -0x20),
        0x05B0: exp1.i_type(0x2B, 29, 31, 0x1C),
        0x05B4: exp1.i_type(0x23, 29, 8, 0x20),
        0x05B8: exp1.i_type(0x2B, 29, 8, 0x00),
        0x05BC: exp1.i_type(0x0F, 0, 8, 0),
        0x05C0: exp1.i_type(9, 8, 8, 0x0C44),
        0x05C4: exp1.i_type(0x2B, 29, 8, 0x18),
        0x05C8: exp1.i_type(0x23, 8, 9, 0),
        0x05CC: exp1.i_type(9, 9, 9, 1),
        0x05D0: exp1.i_type(0x2B, 8, 9, 0),
        0x05D4: exp1.j_type(3, 0x0892D72C),
        0x05D8: 0,
        0x05DC: exp1.i_type(0x23, 29, 8, 0x18),
        0x05E0: exp1.i_type(0x23, 8, 9, 0),
        0x05E4: exp1.i_type(9, 9, 9, -1),
        0x05E8: exp1.i_type(0x2B, 8, 9, 0),
        0x05EC: exp1.i_type(0x23, 29, 31, 0x1C),
        0x05F0: exp1.r_type(31, 0, 0, 0, 8),
        0x05F4: exp1.i_type(9, 29, 29, 0x20),
        0x05F8: exp1.j_type(2, 0x0892D72C),
        0x05FC: 0,
    }
    for va, word in wrapper.items():
        write_word(va, word)

    # The old wrapper occupied through 0x647. This tail is now unused.
    for va in range(0x0600, 0x0648, 4):
        write_word(va, 0)

    # Relocate the remaining module-local depth pointer to the compact wrapper.
    # Disable the old second HI16/LO16 pair, which is no longer needed.
    relocations = {}
    for pos in range(REL_TEXT_FILE_OFFSET, REL_TEXT_FILE_OFFSET + REL_TEXT_SIZE, 8):
        offset, info = struct.unpack_from("<II", data, pos)
        if offset in (0x05D8, 0x05DC, 0x0628, 0x062C):
            relocations[offset] = (pos, info)

    if set(relocations) != {0x05D8, 0x05DC, 0x0628, 0x062C}:
        raise RuntimeError(f"expected slot-wrapper relocations missing: {sorted(relocations)}")
    if [relocations[x][1] for x in (0x05D8, 0x05DC, 0x0628, 0x062C)] != [5, 6, 5, 6]:
        raise RuntimeError("unexpected slot-wrapper relocation types")

    struct.pack_into("<I", data, relocations[0x05D8][0], 0x05BC)
    struct.pack_into("<I", data, relocations[0x05DC][0], 0x05C0)
    struct.pack_into("<I", data, relocations[0x0628][0] + 4, 0)
    struct.pack_into("<I", data, relocations[0x062C][0] + 4, 0)

    # Resident-layout invariant.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError(f"resident layout changed: type={ph[0]} filesz={ph[4]:#x} memsz={ph[5]:#x}")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OPT_EXP2_SHA256:
        raise RuntimeError("OPT-EXP2 output hash mismatch")
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP2.prx"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    output = patch_exp2(exp1.read_release_prx(root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")
    print("Slot game hooks: 13 -> 1")
    print("Newly unreferenced internal capacity: 216 bytes")

if __name__ == "__main__":
    main()
