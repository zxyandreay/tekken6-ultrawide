#!/usr/bin/env python3
"""Build OPT-EXP3C winner-glow predicate fix candidates.

Root cause discovered by comparing historical RoundWin v7 with AutoHUD-era code:

Historical v7 requires exact 64x64 UV corners:
    (0,0), (0,64), (64,0), (64,64)

The compact AutoHUD predicate intended to compare packed UV pairs, but it did:
    lui   t1,0x0040       # 0x00400000
    ...
    li    t1,0x0040       # overwrites high half -> 0x00000040
    ...
    ori   t1,t1,0x0040    # still 0x00000040

Therefore the fourth packed UV check compared against 0x00000040 instead of
0x00400040. The compact hook was not identifying the same rotating quad as v7.

EXP2S3 also bypassed the X-center ownership gate, which broadened the mismatch.

Candidate A:
- fixes the packed UV construction without adding code;
- restores the pre-S3 P1/P2 X-center gate;
- keeps AutoHUD dynamic scale/center math.

Candidate B:
- same ownership fix;
- forces exact historical 20:9 v7 math (0.8*x + 48) as an A/B control.

No GitHub Actions are used or required.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

BASE_SHA256 = "fa41e928aeecba2e2a2bd9d537e38d2dca96499ad084166de6ea854ad9e1bce8"
DYNAMIC_SHA256 = "6a2954bf2fa768d63d66c61e7770c22303a05dce2569f24f363b425552ec972c"
V7MATH_SHA256 = "e21aaffd568d2aa609f3a89be721488bef7e2d86007d6e4c91474e9884551281"

TEXT_FILE_OFFSET = 0x60

def branch(op: int, rs: int, rt: int, pc: int, target: int) -> int:
    off = (target - (pc + 4)) // 4
    return (op << 26) | (rs << 21) | (rt << 16) | (off & 0xFFFF)

def patch(prx: bytes, fixed_v7_math: bool) -> bytes:
    if hashlib.sha256(prx).hexdigest() != BASE_SHA256:
        raise RuntimeError("OPT-EXP3B base hash mismatch")

    data = bytearray(prx)

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    expected = {
        0x0D04: 0x3C090040, # t1 = 0x00400000 for packed (0,64)
        0x0D10: 0x24090040, # BUG: destroys high half
        0x0D14: 0x1509003A,
        0x0D1C: 0x35290040, # intended to make 0x00400040
        0x0D3C: 0x10000006, # EXP2S3 X-gate bypass
        0x0D40: 0x00000000,
        0x0D44: 0x00000000,
        0x0D48: 0x00000000,
        0x0D4C: 0x00000000,
        0x0D50: 0x00000000,
        0x0D54: 0x00000000,
    }
    for va, wanted in expected.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(f"unexpected EXP3B word at {va:#x}: {got:#010x}")

    # Preserve t1=0x00400000 from 0xD04. Validate the third corner's packed
    # value by subtracting 64 from the loaded 0x00000040 and branching if nonzero.
    # Then 0xD1C ORs 0x40 into preserved t1, correctly producing 0x00400040
    # for the fourth (64,64) packed corner.
    write_word(0x0D10, 0x2508FFC0)                       # addiu t0,t0,-64
    write_word(0x0D14, branch(5, 8, 0, 0x0D14, 0x0E00)) # bnez t0,fallback

    # Restore the compact P1/P2 X-center ownership gate that EXP2S3 bypassed.
    x_gate = {
        0x0D3C: 0x2509BC3B,
        0x0D40: 0x2D290003,
        0x0D44: 0x15200004,
        0x0D48: 0x2509BBF5,
        0x0D4C: 0x2D290002,
        0x0D50: 0x1120002B,
        0x0D54: 0x00000000,
    }
    for va, word in x_gate.items():
        write_word(va, word)

    expected_hash = DYNAMIC_SHA256

    if fixed_v7_math:
        v7_math = {
            0x0D84: 0x3C083F4C,
            0x0D88: 0x3508CCCD,
            0x0D8C: 0x44882000,
            0x0D90: 0x3C084240,
            0x0D94: 0x44883000,
        }
        for va, word in v7_math.items():
            write_word(va, word)
        expected_hash = V7MATH_SHA256

    # Fixed resident layout remains mandatory.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected ELF layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError("resident layout changed")

    out = bytes(data)
    if hashlib.sha256(out).hexdigest() != expected_hash:
        raise RuntimeError("output hash mismatch")
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--fixed-v7-math", action="store_true")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    out = patch(args.base.read_bytes(), args.fixed_v7_math)
    args.output.write_bytes(out)
    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(out).hexdigest()}")
    print("UV predicate fixed; P1/P2 X ownership gate restored")
    print("Math:", "fixed v7 20:9" if args.fixed_v7_math else "AutoHUD dynamic")

if __name__ == "__main__":
    main()
