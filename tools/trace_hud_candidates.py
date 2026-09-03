#!/usr/bin/env python3
"""Emit focused disassembly traces for the current Tekken 6 HUD/camera research.

The repository already ranks likely Warriors-style HUD candidates. This helper
adds the missing next layer: exact MIPS disassembly around those candidates,
direct xrefs to their function starts, and context around the known camera
CWCheat halfword site.

It is intentionally read-only and deterministic so GitHub Actions can run it
against the checked-in decrypted ULUS10466 EBOOT and preserve the evidence.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32

DEFAULT_EBOOT = Path(__file__).resolve().parents[1] / "ULUS10466_EBOOT.BIN"
SEG_FILE = 0x00001018
SEG_VADDR = 0x08804018
SEG_SIZE = 0x003F62A8

HUD_RANGES = [
    (0x08AA62D8, 0x08AA655C, "HUD candidate #1"),
    (0x08A3916C, 0x08A396D8, "HUD candidate #2"),
]
CAMERA_SITE = 0x0895350C
CAMERA_VALUES = {
    0x3F80: "Original",
    0x3F81: "Slightly Wider",
    0x3F82: "Wider",
    0x3F83: "Widest",
}
SCREEN_UPPERS = {
    0x43F0: "480.0",
    0x4388: "272.0",
    0x4370: "240.0",
    0x4308: "136.0",
}


def runtime_to_offset(address: int) -> int:
    return SEG_FILE + (address - SEG_VADDR)


def offset_to_runtime(offset: int) -> int:
    return SEG_VADDR + (offset - SEG_FILE)


def read_u32(data: bytes, address: int) -> int:
    return struct.unpack_from("<I", data, runtime_to_offset(address))[0]


def jump_target(pc: int, word: int) -> int:
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def direct_xrefs(data: bytes, target: int) -> list[int]:
    refs: list[int] = []
    end = min(len(data), SEG_FILE + SEG_SIZE)
    for off in range(SEG_FILE, end - 3, 4):
        word = struct.unpack_from("<I", data, off)[0]
        opcode = word >> 26
        if opcode not in (0x02, 0x03):
            continue
        pc = offset_to_runtime(off)
        if jump_target(pc, word) == target:
            refs.append(pc)
    return refs


def annotate(address: int, word: int) -> str:
    notes: list[str] = []
    opcode = word >> 26
    if opcode == 0x0F and (word & 0xFFFF) in SCREEN_UPPERS:
        notes.append("screen-upper=" + SCREEN_UPPERS[word & 0xFFFF])
    if opcode == 0x03:
        notes.append(f"jal->0x{jump_target(address, word):08X}")
    elif opcode == 0x02:
        notes.append(f"j->0x{jump_target(address, word):08X}")
    return "; ".join(notes)


def disassemble_range(data: bytes, start: int, end: int, title: str) -> list[str]:
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    md.detail = False
    off = runtime_to_offset(start)
    blob = data[off : off + (end - start)]
    lines = [f"## {title}: `0x{start:08X}`–`0x{end:08X}`", ""]
    refs = direct_xrefs(data, start)
    if refs:
        lines.append("Direct xrefs to function start: " + ", ".join(f"`0x{x:08X}`" for x in refs))
    else:
        lines.append("Direct xrefs to function start: none found")
    lines.extend(["", "```text"])
    for insn in md.disasm(blob, start):
        word = read_u32(data, insn.address)
        note = annotate(insn.address, word)
        suffix = f"    # {note}" if note else ""
        lines.append(f"0x{insn.address:08X}: {word:08X}  {insn.mnemonic:<8} {insn.op_str}{suffix}")
    lines.extend(["```", ""])
    return lines


def camera_trace(data: bytes) -> list[str]:
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    word = read_u32(data, CAMERA_SITE)
    low = word & 0xFFFF
    high = word >> 16
    lines = [
        "## Known camera site",
        "",
        f"- runtime address: `0x{CAMERA_SITE:08X}`",
        f"- file offset: `0x{runtime_to_offset(CAMERA_SITE):08X}`",
        f"- original 32-bit word: `0x{word:08X}`",
        f"- high halfword preserved by CWCheat: `0x{high:04X}`",
        f"- original low halfword: `0x{low:04X}` ({CAMERA_VALUES.get(low, 'not one of documented values')})",
        "- documented replacement low halfwords: "
        + ", ".join(f"`0x{k:04X}`={v}" for k, v in CAMERA_VALUES.items()),
        "",
        "Nearby disassembly:",
        "",
        "```text",
    ]
    start = CAMERA_SITE - 0x40
    end = CAMERA_SITE + 0x44
    off = runtime_to_offset(start)
    for insn in md.disasm(data[off : off + (end - start)], start):
        w = read_u32(data, insn.address)
        marker = "  <== camera halfword site" if insn.address == CAMERA_SITE else ""
        lines.append(f"0x{insn.address:08X}: {w:08X}  {insn.mnemonic:<8} {insn.op_str}{marker}")
    lines.extend(["```", ""])
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = args.eboot.read_bytes()
    minimum = SEG_FILE + SEG_SIZE
    if len(data) < minimum:
        raise SystemExit(f"EBOOT too small: 0x{len(data):X} < 0x{minimum:X}")

    lines = [
        "# Focused HUD / camera trace",
        "",
        "Generated from the checked-in decrypted ULUS10466 EBOOT.",
        "This report is evidence only; candidate ownership still requires interpretation.",
        "",
    ]
    lines.extend(camera_trace(data))
    for start, end, title in HUD_RANGES:
        lines.extend(disassemble_range(data, start, end, title))

    report = "\n".join(lines)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(report)
        print(f"\nWrote {args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
