#!/usr/bin/env python3
"""Build OPT-EXP2S3-GlowSlots from the stable OPT-EXP2S2 base.

The original winner-glow hook was proven only against first-win P1/P2 X-sum
families. Its existing predicate checks:
- a3 == 4
- exact 64x64 UV corner sequence
- X-sum within one narrow P1 or P2 first-slot family
- Y-sum on the winner-orb row
- then applies the existing dynamic CENTER transform and restores source X.

The archived P1/P2 round-win captures show that every 0x80019E, primitive-4,
4-vertex draw centered around Y=35 used the same winner-glow texture identity.
No alternate texture appeared in that row.

This experiment therefore removes only the narrow X-family gate while preserving
the exact UV/count/Y checks. That generalizes the same glow transform to later
earned-win slots without touching the ordinary round-marker rectangle path.

Base SHA-256:
1a23770194fe66f753554a1981d55d64e266f398f4f44b156ffa9385529a4409

Output SHA-256:
7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

BASE_SHA256 = "1a23770194fe66f753554a1981d55d64e266f398f4f44b156ffa9385529a4409"
OUT_SHA256 = "7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805"
TEXT_FILE_OFFSET = 0x60

def branch(op: int, rs: int, rt: int, pc: int, target: int) -> int:
    delta = target - (pc + 4)
    if delta % 4:
        raise ValueError("unaligned branch target")
    off = delta // 4
    if not -32768 <= off <= 32767:
        raise ValueError("branch out of range")
    return (op << 26) | (rs << 21) | (rt << 16) | (off & 0xFFFF)

def patch(prx: bytes) -> bytes:
    if hashlib.sha256(prx).hexdigest() != BASE_SHA256:
        raise RuntimeError("OPT-EXP2S2 base hash mismatch")

    data = bytearray(prx)

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    # Existing first-slot-only winner-glow X classifier.
    expected = {
        0x0D3C: 0x2509BC3B,  # addiu t1,t0,-0x43c5
        0x0D40: 0x2D290003,  # sltiu t1,t1,3
        0x0D44: 0x15200004,  # bnez t1, P1-match
        0x0D48: 0x2509BBF5,  # addiu t1,t0,-0x440b
        0x0D4C: 0x2D290002,  # sltiu t1,t1,2
        0x0D50: 0x1120002B,  # beqz t1, reject
        0x0D58: 0xC4C00004,  # Y-sum classifier starts here
    }
    for va, wanted in expected.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(f"unexpected base word at {va:#x}: {got:#010x}")

    # After exact count + 64x64 UV checks and X-sum calculation, skip the
    # first-slot-only X family test and continue directly to the existing Y-row
    # test. This keeps all later safety gates and the original transform intact.
    write_word(0x0D3C, branch(4, 0, 0, 0x0D3C, 0x0D58))
    write_word(0x0D40, 0)

    # Preserve the known-good fixed resident layout.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError("resident layout changed")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OUT_SHA256:
        raise RuntimeError("OPT-EXP2S3 output hash mismatch")
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        type=Path,
        default=Path("Tekken6Ultrawide-OPT-EXP2S2.prx"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Tekken6Ultrawide-OPT-EXP2S3-GlowSlots.prx"),
    )
    args = parser.parse_args()

    output = patch(args.base.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")
    print("Winner glow: exact UV/count/Y gates preserved; X first-slot gate removed")

if __name__ == "__main__":
    main()
