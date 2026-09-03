#!/usr/bin/env python3
"""Disassemble windows around the known Tekken 6 aspect patch sites."""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path

try:
    from capstone import CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32, Cs
except ImportError as exc:  # pragma: no cover - exercised by missing environment
    raise SystemExit(
        "Capstone is required. Install it with: python -m pip install -r requirements.txt"
    ) from exc

from analyze_eboot import DEFAULT_EBOOT, cwcheat_runtime_address, parse_elf


@dataclass(frozen=True)
class AspectSite:
    label: str
    code: int
    table_runtime: int
    table_index: int


ASPECT_SITES = [
    AspectSite("aspect_dispatch_1", 0x20145F10, 0x08B9E420, 0),
    AspectSite("aspect_dispatch_2", 0x20146794, 0x08B9E438, 0),
    AspectSite("aspect_dispatch_3", 0x20146BC8, 0x08B9E450, 0),
    AspectSite("aspect_dispatch_4", 0x20147D90, 0x08B9E550, 0),
]


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def word_to_float(word: int) -> float:
    return struct.unpack("<f", struct.pack("<I", word))[0]


def describe_case(data: bytes, file_offset: int) -> str:
    words = [read_u32(data, file_offset + index * 4) for index in range(6)]

    for word in words[:3]:
        if (word & 0xFC000000) == 0xC4000000 and (word & 0xFFFF) == 0x003C:
            return "custom aspect load from +0x3c"

    for index, first in enumerate(words[:4]):
        if (first & 0xFFFF0000) != 0x3C010000:
            continue

        bits = (first & 0xFFFF) << 16
        mtc1_index = index + 1
        if (words[index + 1] & 0xFFFF0000) == 0x34210000:
            bits |= words[index + 1] & 0xFFFF
            mtc1_index = index + 2

        if words[mtc1_index] & 0xFFE007FF == 0x44800000:
            return f"constant 0x{bits:08X} ({word_to_float(bits):.7g})"

    return "non-constant case or needs manual inspection"


def dump_jump_table(data: bytes, elf, site: AspectSite) -> None:
    table_file = elf.file_offset_for_vaddr(site.table_runtime)
    print(f"Jump table {site.label}: runtime=0x{site.table_runtime:08X} file=0x{table_file:08X}")
    for index in range(6):
        target = read_u32(data, table_file + index * 4)
        target_file = elf.file_offset_for_vaddr(target)
        description = describe_case(data, target_file)
        print(
            f"  [{index}] runtime=0x{target:08X} file=0x{target_file:08X} {description}"
        )


def disassemble_window(data: bytes, elf, site: AspectSite, before: int, after: int) -> None:
    runtime = cwcheat_runtime_address(site.code)
    file_offset = elf.file_offset_for_vaddr(runtime)
    start = max(0, file_offset - before)
    end = min(len(data), file_offset + 8 + after)
    start_runtime = runtime - (file_offset - start)

    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True

    print(
        f"Disassembly {site.label}: runtime=0x{runtime:08X} file=0x{file_offset:08X}"
    )
    for insn in md.disasm(data[start:end], start_runtime):
        marker = ">>" if runtime <= insn.address < runtime + 8 else "  "
        print(f"{marker} {insn.address:08X}: {insn.mnemonic:<10} {insn.op_str}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    parser.add_argument("--before", type=lambda value: int(value, 0), default=0x40)
    parser.add_argument("--after", type=lambda value: int(value, 0), default=0x80)
    parser.add_argument("--tables-only", action="store_true")
    parser.add_argument("--disasm-only", action="store_true")
    args = parser.parse_args()

    data = args.eboot.read_bytes()
    elf = parse_elf(data)

    for site in ASPECT_SITES:
        if not args.disasm_only:
            dump_jump_table(data, elf, site)
        if not args.tables_only:
            if not args.disasm_only:
                print()
            disassemble_window(data, elf, site, args.before, args.after)
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
