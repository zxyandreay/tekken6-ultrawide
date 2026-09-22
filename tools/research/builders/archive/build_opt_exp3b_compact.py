#!/usr/bin/env python3
"""Build OPT-EXP3B-Compact from accepted OPT-EXP3A.

Pure compaction only:
- move the 52-byte OneHookScratch helper from 0x0C00..0x0C30 into the proven
  52-byte compressed-table tail at 0x0AC4..0x0AF7;
- retarget the three early-font branches to the relocated helper;
- zero the old 64-byte helper allocation at 0x0C00..0x0C3F;
- zero the previously verified-unreachable winner-glow X block at 0x0D40..0x0D57.

The builder performs pre/post xref checks so it refuses to zero either region
unless the expected control-flow facts still hold.

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
MODULE_EXEC_BASE = 0x08800000
REL_TEXT_FILE_OFFSET = 0x1280
REL_TEXT_SIZE = 0x1D0
BRANCH_OPS = {1, 4, 5, 6, 7, 20, 21, 22, 23}

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

    def branch_refs(start: int, end: int) -> list[tuple[int, int]]:
        refs: list[tuple[int, int]] = []
        for va in range(0, LOAD_SIZE, 4):
            word = read_word(va)
            op = word >> 26
            if op not in BRANCH_OPS:
                continue
            imm = word & 0xFFFF
            if imm & 0x8000:
                imm -= 0x10000
            target = va + 4 + imm * 4
            if start <= target < end:
                refs.append((va, target))
        return refs

    def jump_refs(start: int, end: int) -> list[tuple[int, int]]:
        refs: list[tuple[int, int]] = []
        abs_start = MODULE_EXEC_BASE + start
        abs_end = MODULE_EXEC_BASE + end
        for va in range(0, LOAD_SIZE, 4):
            word = read_word(va)
            op = word >> 26
            if op not in (2, 3):
                continue
            target = (word & 0x03FFFFFF) << 2
            if abs_start <= target < abs_end:
                refs.append((va, target - MODULE_EXEC_BASE))
        return refs

    def pointer_refs(start: int, end: int) -> list[tuple[int, int]]:
        refs: list[tuple[int, int]] = []
        abs_start = MODULE_EXEC_BASE + start
        abs_end = MODULE_EXEC_BASE + end
        for off in range(0, len(data) - 3, 4):
            word = struct.unpack_from("<I", data, off)[0]
            if start <= word < end or abs_start <= word < abs_end:
                refs.append((off, word))
        return refs

    def reloc_sites(start: int, end: int) -> list[int]:
        refs: list[int] = []
        for pos in range(REL_TEXT_FILE_OFFSET, REL_TEXT_FILE_OFFSET + REL_TEXT_SIZE, 8):
            offset, info = struct.unpack_from("<II", data, pos)
            if start <= offset < end and info != 0:
                refs.append(offset)
        return refs

    # Verify accepted EXP3A helper.
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

    # Pre-relocation xref proof.
    helper_branch_refs = branch_refs(0x0C00, 0x0C40)
    external_helper_refs = sorted(
        (src, dst) for src, dst in helper_branch_refs if not (0x0C00 <= src < 0x0C40)
    )
    if external_helper_refs != [(0x0E74, 0x0C00), (0x0E8C, 0x0C00), (0x0E9C, 0x0C00)]:
        raise RuntimeError(f"unexpected external helper refs: {external_helper_refs}")
    if jump_refs(0x0C00, 0x0C40):
        raise RuntimeError("unexpected direct J/JAL into old helper region")
    if pointer_refs(0x0C00, 0x0C40):
        raise RuntimeError("unexpected embedded pointer into old helper region")
    if reloc_sites(0x0C00, 0x0C40):
        raise RuntimeError("unexpected relocation inside old helper region")

    if branch_refs(0x0D40, 0x0D58):
        raise RuntimeError("alternate branch entry into glow-dead block")
    if jump_refs(0x0D40, 0x0D58):
        raise RuntimeError("direct J/JAL entry into glow-dead block")
    if pointer_refs(0x0D40, 0x0D58):
        raise RuntimeError("embedded pointer into glow-dead block")
    if reloc_sites(0x0D40, 0x0D58):
        raise RuntimeError("relocation inside glow-dead block")

    # Destination must remain the proven hard-free 52-byte table tail.
    cave = data[TEXT_FILE_OFFSET + 0x0AC4:TEXT_FILE_OFFSET + 0x0AF8]
    if len(cave) != 52 or any(cave):
        raise RuntimeError("0x0AC4..0x0AF7 is not the expected zero table tail")
    if branch_refs(0x0AC4, 0x0AF8) or jump_refs(0x0AC4, 0x0AF8):
        raise RuntimeError("unexpected executable entry into destination cave before relocation")
    if pointer_refs(0x0AC4, 0x0AF8) or reloc_sites(0x0AC4, 0x0AF8):
        raise RuntimeError("unexpected pointer/relocation into destination cave before relocation")

    # Relocate the 52-byte helper; regenerate internal branch offsets.
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

    # Retarget only the three known early-font branches.
    for va in (0x0E74, 0x0E8C, 0x0E9C):
        write_word(va, branch(4, 0, 0, va, 0x0AC4))

    # Old helper allocation is now detached.
    for va in range(0x0C00, 0x0C40, 4):
        write_word(va, 0)

    # Physically reclaim the already-proven-unreachable glow X block.
    if read_word(0x0D3C) != 0x10000006:
        raise RuntimeError("winner-glow bypass branch changed unexpectedly")
    for va in range(0x0D40, 0x0D58, 4):
        write_word(va, 0)

    # Post-relocation xref proof: zeroed blocks must now have no entries.
    if branch_refs(0x0C00, 0x0C40) or jump_refs(0x0C00, 0x0C40):
        raise RuntimeError("old helper still has executable references after relocation")
    if pointer_refs(0x0C00, 0x0C40) or reloc_sites(0x0C00, 0x0C40):
        raise RuntimeError("old helper still has pointer/relocation references after relocation")

    if branch_refs(0x0D40, 0x0D58) or jump_refs(0x0D40, 0x0D58):
        raise RuntimeError("glow-dead block gained an executable reference")
    if pointer_refs(0x0D40, 0x0D58) or reloc_sites(0x0D40, 0x0D58):
        raise RuntimeError("glow-dead block gained a pointer/relocation reference")

    relocated_external = sorted(
        (src, dst)
        for src, dst in branch_refs(0x0AC4, 0x0AF8)
        if not (0x0AC4 <= src < 0x0AF8)
    )
    if relocated_external != [(0x0E74, 0x0AC4), (0x0E8C, 0x0AC4), (0x0E9C, 0x0AC4)]:
        raise RuntimeError(f"unexpected relocated helper callers: {relocated_external}")

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
