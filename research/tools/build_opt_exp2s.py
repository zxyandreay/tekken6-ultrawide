#!/usr/bin/env python3
"""Build OPT-EXP2S (safe slot-installer compression) from validated OPT-EXP1.

Why this build exists
---------------------
OPT-EXP2/EXP2R/EXP2R2 changed runtime slot-hook topology and regressed round-win
rendering; EXP2R2 also introduced an unsafe PRX-local trampoline and crashed when
the battle HUD first became active.

OPT-EXP2S deliberately does NOT change runtime HUD topology. It preserves the same
13 game callsite hooks and the exact original v1.2.0/OPT-EXP1 slot wrapper.

The only optimization is startup metadata:
- original slot patch record: address + expected word + kind = 12 bytes
- compressed record: address + expected word = 8 bytes
- J vs JAL kind is derived from expected_word >> 26

13 records shrink from 156 to 104 bytes, reclaiming 52 contiguous bytes inside the
same one-PT_LOAD 0x0EB0 image.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

import build_opt_exp1 as exp1

TEXT_FILE_OFFSET = exp1.TEXT_FILE_OFFSET
OPT_EXP1_SHA256 = "91f84acad1047b80b474fe1b2f6df12888c9312fb0b9be34cfae45ff095495fa"
OPT_EXP2S_SHA256 = "a43777202277145acc28fa7d4a41848e7be63413fd43210c8ad8dee8455737ad"

def r_type(rs: int, rt: int, rd: int, shamt: int, funct: int) -> int:
    return (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | funct

def patch_exp2s(prx: bytes) -> bytes:
    data = bytearray(exp1.patch_prx(prx))
    if hashlib.sha256(data).hexdigest() != OPT_EXP1_SHA256:
        raise RuntimeError("OPT-EXP1 base hash mismatch")

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    expected = {
        0x0280: 0x2611009C,
        0x028C: 0x8C440000,
        0x0290: 0x8C4B0008,
        0x0294: 0x8C4A0004,
        0x0298: 0x8C880000,
        0x03B0: 0x3C090C00,
        0x03B4: 0x8CAB0008,
        0x03B8: 0x8CAA0000,
        0x05A0: 0x27BDFFC0,
        0x0610: 0x0E24B67E,
        0x0644: 0x27BD0040,
    }
    for va, wanted in expected.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(f"unexpected OPT-EXP1 word at {va:#x}: {got:#010x} != {wanted:#010x}")

    # Capture the 13 authoritative address/expected/kind records.
    records = []
    for va in range(0x0A5C, 0x0AF8, 12):
        address = read_word(va)
        expected_word = read_word(va + 4)
        kind = read_word(va + 8)
        if kind not in (0, 1):
            raise RuntimeError(f"unexpected slot kind {kind} at {va:#x}")
        opcode = (expected_word >> 26) & 0x3F
        if (kind == 1 and opcode != 3) or (kind == 0 and opcode != 2):
            raise RuntimeError(f"record kind/opcode mismatch at {va:#x}")
        records.append((address, expected_word))

    if len(records) != 13:
        raise RuntimeError("expected 13 slot records")

    # New compressed table length: 13 * 8 = 0x68.
    write_word(0x0280, exp1.i_type(9, 16, 17, 0x0068))

    # Validation loop:
    # each record is [address, expected]. Derive J/JAL opcode directly from
    # expected>>26 and combine it with the already-relocation-safe wrapper target.
    validation = {
        0x0290: exp1.i_type(0x23, 2, 10, 4),                 # lw t2,4(v0)
        0x0294: exp1.i_type(0x23, 4, 8, 0),                  # lw t0,0(a0)
        0x0298: r_type(0, 10, 11, 26, 2),                    # srl t3,t2,26
        0x029C: r_type(0, 11, 11, 26, 0),                    # sll t3,t3,26
        0x02A0: exp1.i_type(9, 2, 2, 8),                     # addiu v0,v0,8
        0x02A4: exp1.branch(4, 8, 10, 0x02A4, 0x02B4),       # beq actual,stock,ok
        0x02A8: r_type(7, 11, 12, 0, 0x25),                  # or t4,t7,t3
        0x02AC: exp1.branch(5, 8, 12, 0x02AC, 0x00E0),       # bne actual,patched,fail
        0x02B0: exp1.i_type(0x23, 29, 31, 0x24),             # lw ra,0x24(sp)
        0x02B4: exp1.branch(0x15, 2, 17, 0x02B4, 0x0290),    # bnel v0,s1,loop
        0x02B8: exp1.i_type(0x23, 2, 4, 0),                  # lw a0,0(v0)
        0x02BC: 0,
    }
    for va, word in validation.items():
        write_word(va, word)

    # Installation loop. Again, derive the J/JAL opcode from expected_word itself.
    install = {
        0x03B0: exp1.i_type(0x23, 5, 11, 4),                 # lw t3,4(a1)
        0x03B4: exp1.i_type(0x23, 5, 10, 0),                 # lw t2,0(a1)
        0x03B8: r_type(0, 11, 11, 26, 2),                    # srl t3,t3,26
        0x03BC: r_type(0, 11, 11, 26, 0),                    # sll t3,t3,26
        0x03C0: r_type(7, 11, 6, 0, 0x25),                   # or a2,t7,t3
        0x03C4: exp1.i_type(9, 5, 5, 8),                     # addiu a1,a1,8
        0x03C8: exp1.i_type(0x2B, 10, 6, 0),                 # sw a2,0(t2)
        0x03CC: exp1.branch(0x15, 5, 17, 0x03CC, 0x03B4),    # bnel a1,s1,loop
        0x03D0: exp1.i_type(0x23, 5, 11, 4),                 # lw t3,4(a1)
        0x03D4: 0,
    }
    for va, word in install.items():
        write_word(va, word)

    # Rewrite the table as 13 x [address, expected] and zero the freed tail.
    cursor = 0x0A5C
    for address, expected_word in records:
        write_word(cursor, address)
        write_word(cursor + 4, expected_word)
        cursor += 8

    if cursor != 0x0AC4:
        raise RuntimeError(f"unexpected compressed table end: {cursor:#x}")

    for va in range(cursor, 0x0AF8, 4):
        write_word(va, 0)

    # Critical safety proof: no battle-time wrapper/HUD code changes.
    exp1_bytes = exp1.patch_prx(prx)
    for start, end, name in (
        (0x05A0, 0x0934, "runtime HUD/text code"),
    ):
        a = TEXT_FILE_OFFSET + start
        b = TEXT_FILE_OFFSET + end
        if data[a:b] != exp1_bytes[a:b]:
            raise RuntimeError(f"{name} unexpectedly changed")

    # Resident-layout invariant.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError(f"resident layout changed: type={ph[0]} filesz={ph[4]:#x} memsz={ph[5]:#x}")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OPT_EXP2S_SHA256:
        raise RuntimeError("OPT-EXP2S output hash mismatch")
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP2S.prx"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    output = patch_exp2s(exp1.read_release_prx(root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")
    print("Runtime slot hooks: unchanged at 13")
    print("Reclaimed contiguous table capacity: 52 bytes")

if __name__ == "__main__":
    main()
