#!/usr/bin/env python3
"""Find simple MIPS direct-code and literal-pointer xrefs in the EBOOT."""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path

from analyze_eboot import DEFAULT_EBOOT, parse_elf


@dataclass(frozen=True)
class DirectXref:
    source_runtime: int
    source_file: int
    kind: str
    word: int


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def iter_words(data: bytes):
    for offset in range(0, len(data) - 3, 4):
        yield offset, read_u32(data, offset)


def jump_target(pc: int, word: int) -> int:
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def find_direct_xrefs(data: bytes, elf, target: int) -> list[DirectXref]:
    results: list[DirectXref] = []
    for source_file, word in iter_words(data):
        opcode = word >> 26
        if opcode not in {0x02, 0x03}:
            continue
        try:
            source_runtime = next(
                segment.vaddr + (source_file - segment.offset)
                for segment in elf.segments
                if segment.offset <= source_file < segment.offset + segment.filesz
            )
        except StopIteration:
            continue

        if jump_target(source_runtime, word) == target:
            results.append(
                DirectXref(
                    source_runtime=source_runtime,
                    source_file=source_file,
                    kind="jal" if opcode == 0x03 else "j",
                    word=word,
                )
            )
    return results


def find_literal_words(data: bytes, value: int) -> list[int]:
    return [offset for offset, word in iter_words(data) if word == value]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    parser.add_argument("target", nargs="+", type=lambda value: int(value, 0))
    args = parser.parse_args()

    data = args.eboot.read_bytes()
    elf = parse_elf(data)

    for target in args.target:
        print(f"Target 0x{target:08X}")

        direct = find_direct_xrefs(data, elf, target)
        print(f"  direct j/jal xrefs: {len(direct)}")
        for xref in direct:
            print(
                f"    {xref.kind:<3} runtime=0x{xref.source_runtime:08X} "
                f"file=0x{xref.source_file:08X} word=0x{xref.word:08X}"
            )

        literal = find_literal_words(data, target)
        print(f"  literal 32-bit pointer/data words: {len(literal)}")
        for source_file in literal:
            source_runtime = None
            for segment in elf.segments:
                if segment.offset <= source_file < segment.offset + segment.filesz:
                    source_runtime = segment.vaddr + (source_file - segment.offset)
                    break
            runtime_text = f"runtime=0x{source_runtime:08X} " if source_runtime else ""
            print(f"    {runtime_text}file=0x{source_file:08X}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
