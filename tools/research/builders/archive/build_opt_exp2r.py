#!/usr/bin/env python3
"""Build OPT-EXP2R from the device-validated OPT-EXP1 architecture.

OPT-EXP2 was rejected on-device because its compact internal slot wrapper used t0/t1
for scope bookkeeping before calling Tekken's 0x0892D72C renderer. The stock slot ABI
carries live renderer state in t0-t3, so that corrupted round-marker composition.

OPT-EXP2R keeps the 13 -> 1 slot-hook consolidation but makes the internal wrapper
ABI-transparent:
- a0-a3 untouched
- t0-t3 untouched
- f12 untouched
- sp untouched
- D9F8's fifth stack argument at 0(sp) untouched
- only t4/t5 used for scope bookkeeping (matching the released wrapper's scratch use)

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
OPT_EXP2R_SHA256 = "4e03a0949c3746e3eec657f55f37a81ea7121537ec1b549770b08c7351dd9e4f"

def patch_exp2r(prx: bytes) -> bytes:
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

    # Collapse the thirteen route records to the one internal JAL at 0x0892DA04.
    write_word(0x0280, exp1.i_type(9, 16, 17, 0x000C))
    write_word(0x0A5C, 0x0892DA04)
    write_word(0x0A60, 0x0E24B5CB)  # stock JAL 0x0892D72C
    write_word(0x0A64, 1)
    for va in range(0x0A68, 0x0AF8, 4):
        write_word(va, 0)

    # ABI-transparent internal slot wrapper.
    #
    # At entry, D9F8 has already executed:
    #   addiu sp,sp,-0x20
    #   addiu v0,zero,1
    #   sw    ra,0x10(sp)
    # and the patched JAL delay slot:
    #   sw    v0,0(sp)
    #
    # Therefore 0(sp) already contains the fifth argument expected by D72C.
    # Do not create another frame and do not touch t0-t3.
    wrapper = {
        0x05A0: exp1.i_type(9, 0, 12, 0x00EF),               # li t4,0xEF
        0x05A4: exp1.branch(5, 5, 12, 0x05A4, 0x05E4),       # bne a1,t4,pass-through
        0x05A8: 0,
        0x05AC: exp1.i_type(0x0F, 0, 12, 0),                 # relocated depth HI16
        0x05B0: exp1.i_type(9, 12, 12, 0x0C44),              # relocated depth LO16
        0x05B4: exp1.i_type(0x23, 12, 13, 0),                # lw t5,0(t4)
        0x05B8: exp1.i_type(9, 13, 13, 1),
        0x05BC: exp1.i_type(0x2B, 12, 13, 0),
        0x05C0: exp1.j_type(3, 0x0892D72C),                  # jal stock renderer
        0x05C4: 0,
        0x05C8: exp1.i_type(0x0F, 0, 12, 0),                 # relocated depth HI16
        0x05CC: exp1.i_type(9, 12, 12, 0x0C44),              # relocated depth LO16
        0x05D0: exp1.i_type(0x23, 12, 13, 0),
        0x05D4: exp1.i_type(9, 13, 13, -1),
        0x05D8: exp1.i_type(0x2B, 12, 13, 0),
        0x05DC: exp1.j_type(2, 0x0892DA0C),                  # resume D9F8 epilogue
        0x05E0: 0,
        0x05E4: exp1.j_type(2, 0x0892D72C),                  # non-EF tail call
        0x05E8: 0,
    }
    for va, word in wrapper.items():
        write_word(va, word)
    for va in range(0x05EC, 0x0648, 4):
        write_word(va, 0)

    # Move both released depth-counter relocation pairs to the compact wrapper.
    relocations = {}
    for pos in range(REL_TEXT_FILE_OFFSET, REL_TEXT_FILE_OFFSET + REL_TEXT_SIZE, 8):
        offset, info = struct.unpack_from("<II", data, pos)
        if offset in (0x05D8, 0x05DC, 0x0628, 0x062C):
            relocations[offset] = (pos, info)

    if set(relocations) != {0x05D8, 0x05DC, 0x0628, 0x062C}:
        raise RuntimeError(f"expected slot-wrapper relocations missing: {sorted(relocations)}")
    if [relocations[x][1] for x in (0x05D8, 0x05DC, 0x0628, 0x062C)] != [5, 6, 5, 6]:
        raise RuntimeError("unexpected slot-wrapper relocation types")

    for old, new in (
        (0x05D8, 0x05AC),
        (0x05DC, 0x05B0),
        (0x0628, 0x05C8),
        (0x062C, 0x05CC),
    ):
        struct.pack_into("<I", data, relocations[old][0], new)

    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError(f"resident layout changed: type={ph[0]} filesz={ph[4]:#x} memsz={ph[5]:#x}")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OPT_EXP2R_SHA256:
        raise RuntimeError("OPT-EXP2R output hash mismatch")
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP2R.prx"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    output = patch_exp2r(exp1.read_release_prx(root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")
    print("Slot game hooks: 13 -> 1")
    print("Newly unreferenced internal capacity: 236 bytes")

if __name__ == "__main__":
    main()
