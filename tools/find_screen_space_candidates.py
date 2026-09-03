#!/usr/bin/env python3
"""Find likely Tekken 6 HUD/UI screen-space setup code.

This scanner is intended for the decrypted ULUS10466 EBOOT already kept in the
project.  It does not patch anything.  It searches code for PSP-sized screen
constants (480, 272, centers, and the common 512x320 virtual size), disassembles
small windows around each hit, and records nearby direct calls.

The goal is to move away from blind sprite edits after the A/B/C orthographic
projection diagnostics showed no visible HUD/UI change on real hardware.
"""

from __future__ import annotations

import argparse
import struct
from collections import defaultdict
from pathlib import Path

try:
    from capstone import CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32, Cs
except ImportError as exc:
    raise SystemExit(
        "Capstone is required. Install it with: python -m pip install -r requirements.txt"
    ) from exc

DEFAULT_EBOOT = Path(__file__).resolve().parents[1] / "ULUS10466_EBOOT.BIN"
SEGMENT_FILE_OFFSET = 0x00001018
SEGMENT_VADDR = 0x08804018
SEGMENT_FILE_SIZE = 0x003F62A8

# Values chosen because they are plausible logical screen dimensions/centers,
# not because every occurrence is expected to be UI-related.
FLOAT_CONSTANTS = {
    "480.0": 0x43F00000,
    "272.0": 0x43880000,
    "240.0": 0x43700000,
    "136.0": 0x43080000,
    "512.0": 0x44000000,
    "320.0": 0x43A00000,
    "256.0": 0x43800000,
    "160.0": 0x43200000,
}

INTEGER_IMMEDIATES = {
    "480": 480,
    "272": 272,
    "240": 240,
    "136": 136,
    "512": 512,
    "320": 320,
    "256": 256,
    "160": 160,
}


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def file_to_runtime(offset: int) -> int:
    return SEGMENT_VADDR + (offset - SEGMENT_FILE_OFFSET)


def runtime_to_file(runtime: int) -> int:
    return SEGMENT_FILE_OFFSET + (runtime - SEGMENT_VADDR)


def jump_target(pc: int, word: int) -> int:
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def is_probable_code_word(word: int) -> bool:
    # This intentionally stays permissive.  We only use it to avoid treating
    # obviously zero/padding words as interesting instruction sites.
    return word not in (0x00000000, 0xFFFFFFFF)


def find_float_load_hits(data: bytes):
    hits = []
    start = SEGMENT_FILE_OFFSET
    end = min(len(data), SEGMENT_FILE_OFFSET + SEGMENT_FILE_SIZE)

    for offset in range(start, end - 3, 4):
        word = read_u32(data, offset)
        if not is_probable_code_word(word):
            continue

        # lui $rt, upper16. All selected floats have low 16 bits = 0, so this
        # is the common compiler form used by the already-verified 480.0 sites.
        if (word >> 26) == 0x0F:
            imm = word & 0xFFFF
            for label, bits in FLOAT_CONSTANTS.items():
                if imm == (bits >> 16):
                    hits.append((offset, f"float {label} via LUI", word))

        # Exact literal word. This can be code or read-only data; callers must
        # be inspected before deciding that a hit is relevant.
        for label, bits in FLOAT_CONSTANTS.items():
            if word == bits:
                hits.append((offset, f"literal float {label}", word))

    return hits


def find_integer_immediate_hits(data: bytes):
    hits = []
    start = SEGMENT_FILE_OFFSET
    end = min(len(data), SEGMENT_FILE_OFFSET + SEGMENT_FILE_SIZE)

    # Common I-type opcodes where a small screen dimension may appear as an
    # immediate. Restricting opcodes keeps the report manageable.
    interesting_opcodes = {
        0x08,  # addi
        0x09,  # addiu
        0x0A,  # slti
        0x0B,  # sltiu
        0x0C,  # andi
        0x0D,  # ori
        0x0E,  # xori
    }

    for offset in range(start, end - 3, 4):
        word = read_u32(data, offset)
        opcode = word >> 26
        if opcode not in interesting_opcodes:
            continue
        imm = word & 0xFFFF
        for label, value in INTEGER_IMMEDIATES.items():
            if imm == value:
                hits.append((offset, f"integer immediate {label}", word))
    return hits


def nearby_calls(data: bytes, center_offset: int, radius: int = 0x80):
    start = max(SEGMENT_FILE_OFFSET, center_offset - radius)
    end = min(SEGMENT_FILE_OFFSET + SEGMENT_FILE_SIZE, center_offset + radius)
    calls = []
    for offset in range(start & ~3, end - 3, 4):
        word = read_u32(data, offset)
        opcode = word >> 26
        if opcode not in (0x02, 0x03):
            continue
        runtime = file_to_runtime(offset)
        calls.append(
            (
                runtime,
                "jal" if opcode == 0x03 else "j",
                jump_target(runtime, word),
            )
        )
    return calls


def find_probable_prologue(data: bytes, center_offset: int, max_back: int = 0x300):
    """Find a nearby addiu sp,sp,-N with an ra save following it."""
    lower = max(SEGMENT_FILE_OFFSET, center_offset - max_back)
    for offset in range(center_offset & ~3, lower - 1, -4):
        word = read_u32(data, offset)
        # addiu sp, sp, signed_imm : opcode 0x09, rs=sp(29), rt=sp(29)
        if (word & 0xFFFF0000) != 0x27BD0000:
            continue
        imm = word & 0xFFFF
        signed = imm if imm < 0x8000 else imm - 0x10000
        if signed >= 0:
            continue
        # Look forward for sw ra, offset(sp) within 0x30 bytes.
        for probe in range(offset + 4, min(offset + 0x34, center_offset + 4), 4):
            w = read_u32(data, probe)
            if (w & 0xFFFF0000) == 0xAFBF0000:
                return offset
    return None


def disasm_window(md, data: bytes, center_offset: int, before: int, after: int):
    start = max(SEGMENT_FILE_OFFSET, center_offset - before)
    end = min(SEGMENT_FILE_OFFSET + SEGMENT_FILE_SIZE, center_offset + after)
    start &= ~3
    runtime = file_to_runtime(start)
    return list(md.disasm(data[start:end], runtime))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--before", type=lambda v: int(v, 0), default=0x40)
    parser.add_argument("--after", type=lambda v: int(v, 0), default=0x80)
    args = parser.parse_args()

    data = args.eboot.read_bytes()
    minimum = SEGMENT_FILE_OFFSET + SEGMENT_FILE_SIZE
    if len(data) < minimum:
        raise SystemExit(f"EBOOT too small: 0x{len(data):X} < 0x{minimum:X}")

    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True

    raw_hits = find_float_load_hits(data) + find_integer_immediate_hits(data)

    # Group multiple labels that point at the same instruction/data word.
    grouped = defaultdict(list)
    words = {}
    for offset, label, word in raw_hits:
        grouped[offset].append(label)
        words[offset] = word

    lines = []
    lines.append("# Tekken 6 screen-space candidate report")
    lines.append("")
    lines.append(f"EBOOT: {args.eboot}")
    lines.append(f"Candidate offsets: {len(grouped)}")
    lines.append("")

    for index, offset in enumerate(sorted(grouped), 1):
        runtime = file_to_runtime(offset)
        prologue = find_probable_prologue(data, offset)
        calls = nearby_calls(data, offset)

        lines.append(f"## Candidate {index}: runtime 0x{runtime:08X} / file 0x{offset:08X}")
        lines.append(f"- labels: {', '.join(sorted(set(grouped[offset])))}")
        lines.append(f"- raw word: 0x{words[offset]:08X}")
        if prologue is not None:
            lines.append(
                f"- probable containing function start: 0x{file_to_runtime(prologue):08X}"
            )
        else:
            lines.append("- probable containing function start: not found")
        if calls:
            lines.append("- nearby direct branches/calls:")
            for source, kind, target in calls:
                lines.append(f"  - {kind} 0x{source:08X} -> 0x{target:08X}")
        else:
            lines.append("- nearby direct branches/calls: none")
        lines.append("")
        lines.append("```asm")
        for insn in disasm_window(md, data, offset, args.before, args.after):
            marker = ">>" if insn.address == runtime else "  "
            lines.append(f"{marker} {insn.address:08X}: {insn.mnemonic:<10} {insn.op_str}")
        lines.append("```")
        lines.append("")

    report = "\n".join(lines) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {args.output} ({len(grouped)} candidates)")
    else:
        print(report, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
