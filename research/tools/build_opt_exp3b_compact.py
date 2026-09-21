#!/usr/bin/env python3
"""Build OPT-EXP3B-Compact from accepted OPT-EXP3A.

This is a pure compaction candidate.

Changes:
- relocate the 52-byte OneHookScratch helper from 0x0C00..0x0C30 into the proven
  52-byte compressed-table tail at 0x0AC4..0x0AF7;
- retarget the three early-font branches to the relocated helper;
- zero the old 64-byte helper allocation at 0x0C00..0x0C3F;
- zero the previously verified-unreachable winner-glow X block at 0x0D40..0x0D57.

No other behavior is intentionally changed.
No GitHub Actions are used or required.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

BASE_SHA256 = "46063c6097e3dfaa51aafd077e0e5c65f02487bdbe420f8884f2a292edf8cf1f"
OUT_SHA256 = "fa41e928aeecba2e2a2bd9d537e38d2dca96499ad084166de6ea854ad9e1bce8"

TEXT_FILE_OFFSET = 0x60
LOAD_SIZE = 0x0EB0

def i_type(op: int, rs: int, rt: int, imm: int) -> int:
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)

def r_type(rs: int, rt: int, rd: int, shamt: int, funct: int) -> int:
    return (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | funct

def j_type(op: int, target: int) -> int:
    return (op << 26) | ((target >> 2) & 0x03FFFFFF)

def branch(op: int, rs: int, rt: int, pc: int, target: int) -> int:
    delta = target - (pc + 4)
    if delta % 4:
        raise ValueError("unaligned branch")
    off = delta // 4
    if not -32768 <= off <= 32767:
        raise ValueError("branch out of range")
    return i_type(op, rs, rt, off)

def patch_exp3b(prx: bytes) -> bytes:
    if hashlib.sha256(prx).hexdigest() != BASE_SHA256:
        raise RuntimeError("OPT-EXP3A base hash mismatch")

    data = bytearray(prx)

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    # Verify the accepted EXP3A helper before relocating it.
    expected_helper = {
        0x0C00: 0x3C020880,
        0x0C04: 0x8C4B2318,
        0x0C08: 0x24030064,
        0x0C0C: 0x11230007,
        0x0C10: 0x00000000,
        0x0C14: 0x11000004,
        0x0C18: 0x8C43231C,
        0x0C1C: 0x8FA80058,
        0x0C20: 0x01034021,
        0x0C24: 0xAFA80058,
        0x0C28: 0xAFAB0028,
        0x0C2C: 0x0A25C2A6,
        0x0C30: 0x00000000,
    }
    for va, wanted in expected_helper.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(
                f"unexpected EXP3A helper word at {va:#x}: {got:#010x} != {wanted:#010x}"
            )

    # The destination must still be the proven hard-free 52-byte table tail.
    cave = data[
        TEXT_FILE_OFFSET + 0x0AC4:
        TEXT_FILE_OFFSET + 0x0AF8
    ]
    if len(cave) != 52 or any(cave):
        raise RuntimeError("0x0AC4..0x0AF7 is not the expected zero table tail")

    # Relocate the 52-byte helper. Internal branch offsets are regenerated.
    helper = {
        0x0AC4: i_type(0x0F, 0, 2, 0x0880),
        0x0AC8: i_type(0x23, 2, 11, 0x2318),
        0x0ACC: i_type(9, 0, 3, 100),
        0x0AD0: branch(4, 9, 3, 0x0AD0, 0x0AF0),
        0x0AD4: 0,
        0x0AD8: branch(4, 8, 0, 0x0AD8, 0x0AEC),
        0x0ADC: i_type(0x23, 2, 3, 0x231C),
        0x0AE0: i_type(0x23, 29, 8, 0x58),
        0x0AE4: r_type(8, 3, 8, 0, 0x21),
        0x0AE8: i_type(0x2B, 29, 8, 0x58),
        0x0AEC: i_type(0x2B, 29, 11, 0x28),
        0x0AF0: j_type(2, 0x08970A98),
        0x0AF4: 0,
    }
    for va, word in helper.items():
        write_word(va, word)

    # Retarget only the three target-row branches to the relocated helper.
    for va in (0x0E74, 0x0E8C, 0x0E9C):
        write_word(va, branch(4, 0, 0, va, 0x0AC4))

    # Old helper allocation is now detached.
    for va in range(0x0C00, 0x0C40, 4):
        write_word(va, 0)

    # S3 proved this winner-glow X classifier unreachable and the accepted
    # reclaimed-space audit found no alternate branch/J/JAL/pointer/reloc entry.
    if read_word(0x0D3C) != 0x10000006:
        raise RuntimeError("winner-glow bypass branch changed unexpectedly")
    for va in range(0x0D40, 0x0D58, 4):
        write_word(va, 0)

    # Resident-layout invariant.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError("resident layout changed")

    # Candidate hard-free regions must be physically zero.
    for start, end, name in (
        (0x0C00, 0x0C40, "old 64-byte helper region"),
        (0x0D40, 0x0D58, "old 24-byte glow X block"),
    ):
        region = data[TEXT_FILE_OFFSET + start:TEXT_FILE_OFFSET + end]
        if any(region):
            raise RuntimeError(f"{name} is not fully zero after compaction")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OUT_SHA256:
        raise RuntimeError("OPT-EXP3B output hash mismatch")
    return result

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP3B-Compact.prx"))
    args = ap.parse_args()

    output = patch_exp3b(args.base.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")
    print("Candidate physically hard-free capacity: 88 bytes")
    print("  0x0C00..0x0C3F = 64 bytes")
    print("  0x0D40..0x0D57 = 24 bytes")

if __name__ == "__main__":
    main()
