#!/usr/bin/env python3
"""Emit focused disassembly traces for the current Tekken 6 HUD/camera research.

The repository already ranks likely Warriors-style HUD candidates. This helper
adds exact MIPS context, references to interesting entry points, caller windows,
field-use scans, and the known camera CWCheat instruction. It is read-only and
deterministic so CI can preserve the evidence used for plugin decisions.
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
CALLER_RANGES = [
    (0x08A27FC0, 0x08A28100, "caller of candidate #2 batch/setup"),
    (0x089A9280, 0x089A9320, "initializer-B caller family A"),
    (0x089AB350, 0x089AB3F0, "initializer-B caller family B"),
    (0x089AD830, 0x089AD8D0, "initializer-B caller family C"),
    (0x08A321D0, 0x08A32300, "initializer-B caller family D"),
]
HELPER_RANGES = [
    (0x08ACE140, 0x08ACE240, "candidate allocation/query helpers"),
    (0x08ADB650, 0x08ADB760, "candidate descriptor submit helper"),
]
ENTRY_TARGETS = [
    (0x08AA62D8, "candidate #1 entry"),
    (0x08A3916C, "candidate #2 scale/set entry"),
    (0x08A39284, "candidate #2 initializer A"),
    (0x08A392F0, "candidate #2 initializer B"),
    (0x08A3935C, "candidate #2 batch/setup entry"),
]
CAMERA_SITE = 0x0895350C
CAMERA_VALUES = {
    0x3F80: "Original",
    0x3F81: "Slightly Wider",
    0x3F82: "Wider",
    0x3F83: "Widest",
}
SCREEN_UPPERS = {0x43F0: "480.0", 0x4388: "272.0", 0x4370: "240.0", 0x4308: "136.0"}


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
        if word >> 26 not in (0x02, 0x03):
            continue
        pc = offset_to_runtime(off)
        if jump_target(pc, word) == target:
            refs.append(pc)
    return refs


def literal_pointer_refs(data: bytes, target: int) -> list[int]:
    refs: list[int] = []
    end = min(len(data), SEG_FILE + SEG_SIZE)
    for off in range(SEG_FILE, end - 3, 4):
        if struct.unpack_from("<I", data, off)[0] == target:
            refs.append(offset_to_runtime(off))
    return refs


def constructed_address_refs(data: bytes, target: int) -> list[tuple[int, int]]:
    refs: list[tuple[int, int]] = []
    end = min(len(data), SEG_FILE + SEG_SIZE)
    target_hi_ori = (target >> 16) & 0xFFFF
    target_lo = target & 0xFFFF
    signed_lo = target_lo if target_lo < 0x8000 else target_lo - 0x10000
    target_hi_addiu = ((target - signed_lo) >> 16) & 0xFFFF
    for off in range(SEG_FILE, end - 3, 4):
        first = struct.unpack_from("<I", data, off)[0]
        if first >> 26 != 0x0F:
            continue
        rt = (first >> 16) & 0x1F
        imm = first & 0xFFFF
        if imm not in (target_hi_ori, target_hi_addiu):
            continue
        for step in range(1, 6):
            probe = off + step * 4
            if probe + 4 > end:
                break
            word = struct.unpack_from("<I", data, probe)[0]
            opcode = word >> 26
            rs = (word >> 21) & 0x1F
            rt2 = (word >> 16) & 0x1F
            low = word & 0xFFFF
            if rs != rt or rt2 != rt:
                continue
            if opcode == 0x0D and imm == target_hi_ori and low == target_lo:
                refs.append((offset_to_runtime(off), offset_to_runtime(probe)))
                break
            if opcode == 0x09 and imm == target_hi_addiu and low == target_lo:
                refs.append((offset_to_runtime(off), offset_to_runtime(probe)))
                break
    return refs


def decode_word(md: Cs, data: bytes, address: int) -> tuple[str, str]:
    off = runtime_to_offset(address)
    insns = list(md.disasm(data[off : off + 4], address, count=1))
    if not insns:
        return ".word", f"0x{read_u32(data, address):08X}"
    return insns[0].mnemonic, insns[0].op_str


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
    lines = [f"## {title}: `0x{start:08X}`–`0x{end:08X}`", "", "```text"]
    for address in range(start, end, 4):
        word = read_u32(data, address)
        mnemonic, op_str = decode_word(md, data, address)
        note = annotate(address, word)
        suffix = f"    # {note}" if note else ""
        lines.append(f"0x{address:08X}: {word:08X}  {mnemonic:<8} {op_str}{suffix}")
    lines.extend(["```", ""])
    return lines


def reference_report(data: bytes) -> list[str]:
    lines = ["## Entry-point reference scan", ""]
    for target, label in ENTRY_TARGETS:
        direct = direct_xrefs(data, target)
        literal = literal_pointer_refs(data, target)
        constructed = constructed_address_refs(data, target)
        lines.append(f"### {label}: `0x{target:08X}`")
        lines.append("- direct j/jal: " + (", ".join(f"`0x{x:08X}`" for x in direct) if direct else "none"))
        lines.append("- literal 32-bit pointer words: " + (", ".join(f"`0x{x:08X}`" for x in literal) if literal else "none"))
        lines.append("- LUI + ORI/ADDIU constructions: " + (", ".join(f"`0x{a:08X}`→`0x{b:08X}`" for a, b in constructed) if constructed else "none"))
        lines.append("")
    return lines


def field_4c_report(data: bytes) -> list[str]:
    """Find all COP1 loads/stores at structure offset +0x4C and show local context."""
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    end = min(len(data), SEG_FILE + SEG_SIZE)
    hits: list[int] = []
    for off in range(SEG_FILE, end - 3, 4):
        word = struct.unpack_from("<I", data, off)[0]
        opcode = word >> 26
        if opcode in (0x31, 0x39) and (word & 0xFFFF) == 0x004C:  # lwc1/swc1 +0x4c(base)
            hits.append(offset_to_runtime(off))
    lines = ["## Global COP1 uses of structure offset `+0x4C`", "", f"Found {len(hits)} lwc1/swc1 hits.", ""]
    for hit in hits:
        lines.append(f"### hit `0x{hit:08X}`")
        lines.append("```text")
        for address in range(hit - 0x10, hit + 0x14, 4):
            word = read_u32(data, address)
            m, ops = decode_word(md, data, address)
            marker = "  <== +0x4C" if address == hit else ""
            lines.append(f"0x{address:08X}: {word:08X}  {m:<8} {ops}{marker}")
        lines.extend(["```", ""])
    return lines


def camera_trace(data: bytes) -> list[str]:
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    word = read_u32(data, CAMERA_SITE)
    low = word & 0xFFFF
    high = word >> 16
    mnemonic, op_str = decode_word(md, data, CAMERA_SITE)
    lines = [
        "## Known camera site", "",
        f"- runtime address: `0x{CAMERA_SITE:08X}`",
        f"- file offset: `0x{runtime_to_offset(CAMERA_SITE):08X}`",
        f"- original 32-bit word: `0x{word:08X}` = `{mnemonic} {op_str}`",
        f"- high halfword preserved by CWCheat: `0x{high:04X}`",
        f"- original low halfword: `0x{low:04X}` ({CAMERA_VALUES.get(low, 'unknown')})",
        "- documented replacements: " + ", ".join(f"`0x{k:04X}`={v}" for k, v in CAMERA_VALUES.items()),
        "- `0x3F82` therefore means full instruction `0x3C013F82` (`lui $at, 0x3F82`).",
        "", "```text",
    ]
    for address in range(CAMERA_SITE - 0x18, CAMERA_SITE + 0x24, 4):
        w = read_u32(data, address)
        m, ops = decode_word(md, data, address)
        marker = "  <== camera site" if address == CAMERA_SITE else ""
        lines.append(f"0x{address:08X}: {w:08X}  {m:<8} {ops}{marker}")
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

    lines = ["# Focused HUD / camera trace", "", "Generated from ULUS10466_EBOOT.BIN.", ""]
    lines.extend(camera_trace(data))
    lines.extend(reference_report(data))
    lines.extend(field_4c_report(data))
    for start, end, title in CALLER_RANGES:
        lines.extend(disassemble_range(data, start, end, title))
    for start, end, title in HUD_RANGES:
        lines.extend(disassemble_range(data, start, end, title))
    for start, end, title in HELPER_RANGES:
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
