#!/usr/bin/env python3
"""Small ELF/CWCheat helper for Tekken 6 ULUS10466 research.

The script intentionally avoids external dependencies so it can be run in a
fresh Codex or ChatGPT handoff environment.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EBOOT = Path("ULUS10466_EBOOT.BIN")
PSP_USER_BASE = 0x08800000

KNOWN_ASPECT_CODES = [
    0x20145F10,
    0x20145F14,
    0x20146794,
    0x20146798,
    0x20146BC8,
    0x20146BCC,
    0x20147D90,
    0x20147D94,
]

EXPECTED_RESTORE = {
    0x20145F10: 0x3C013FE3,
    0x20145F14: 0x34218E39,
    0x20146794: 0x3C013FE3,
    0x20146798: 0x34218E39,
    0x20146BC8: 0x3C013FE3,
    0x20146BCC: 0x34218E39,
    0x20147D90: 0x3C013FE3,
    0x20147D94: 0x34218E39,
}

ORIGINAL_ASPECT_PAIR = bytes.fromhex("E33F013C398E2134")
PATCHED_20_9_PAIR = bytes.fromhex("0E40013CE4382134")


@dataclass(frozen=True)
class ProgramHeader:
    p_type: int
    offset: int
    vaddr: int
    paddr: int
    filesz: int
    memsz: int
    flags: int
    align: int

    def contains_vaddr(self, address: int) -> bool:
        return self.vaddr <= address < self.vaddr + self.filesz

    def file_offset_for_vaddr(self, address: int) -> int:
        if not self.contains_vaddr(address):
            raise ValueError(f"0x{address:08X} is outside this segment")
        return self.offset + (address - self.vaddr)


@dataclass(frozen=True)
class ElfInfo:
    entry: int
    phoff: int
    shoff: int
    flags: int
    ehsize: int
    phentsize: int
    phnum: int
    shentsize: int
    shnum: int
    shstrndx: int
    segments: tuple[ProgramHeader, ...]

    def file_offset_for_vaddr(self, address: int) -> int:
        for segment in self.segments:
            if segment.contains_vaddr(address):
                return segment.file_offset_for_vaddr(address)
        raise ValueError(f"0x{address:08X} is outside all file-backed segments")


def read_u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def parse_elf(data: bytes) -> ElfInfo:
    if data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")
    if data[4] != 1:
        raise ValueError("expected ELF32")
    if data[5] != 1:
        raise ValueError("expected little-endian ELF")
    if read_u16(data, 0x12) != 8:
        raise ValueError("expected MIPS machine type")

    phoff = read_u32(data, 0x1C)
    phentsize = read_u16(data, 0x2A)
    phnum = read_u16(data, 0x2C)
    segments: list[ProgramHeader] = []

    for index in range(phnum):
        off = phoff + index * phentsize
        segments.append(
            ProgramHeader(
                p_type=read_u32(data, off + 0x00),
                offset=read_u32(data, off + 0x04),
                vaddr=read_u32(data, off + 0x08),
                paddr=read_u32(data, off + 0x0C),
                filesz=read_u32(data, off + 0x10),
                memsz=read_u32(data, off + 0x14),
                flags=read_u32(data, off + 0x18),
                align=read_u32(data, off + 0x1C),
            )
        )

    return ElfInfo(
        entry=read_u32(data, 0x18),
        phoff=phoff,
        shoff=read_u32(data, 0x20),
        flags=read_u32(data, 0x24),
        ehsize=read_u16(data, 0x28),
        phentsize=phentsize,
        phnum=phnum,
        shentsize=read_u16(data, 0x2E),
        shnum=read_u16(data, 0x30),
        shstrndx=read_u16(data, 0x32),
        segments=tuple(segments),
    )


def cwcheat_data_address(code_word: int) -> int:
    return code_word & 0x0FFFFFFF


def cwcheat_runtime_address(code_word: int, user_base: int = PSP_USER_BASE) -> int:
    return user_base + cwcheat_data_address(code_word)


def iter_occurrences(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        found = data.find(needle, start)
        if found == -1:
            return offsets
        offsets.append(found)
        start = found + 1


def format_word(data: bytes, offset: int) -> str:
    word = read_u32(data, offset)
    return f"0x{word:08X}"


def print_header(data: bytes, elf: ElfInfo) -> None:
    print("ELF")
    print(f"  sha256: {hashlib.sha256(data).hexdigest().upper()}")
    print(f"  size: {len(data)} bytes (0x{len(data):X})")
    print("  class: ELF32")
    print("  endian: little")
    print("  machine: MIPS")
    print(f"  entry: 0x{elf.entry:08X}")
    print(f"  program_headers: offset=0x{elf.phoff:08X} count={elf.phnum} entry_size=0x{elf.phentsize:X}")
    print(f"  section_headers: offset=0x{elf.shoff:08X} count={elf.shnum} entry_size=0x{elf.shentsize:X}")
    print(f"  flags: 0x{elf.flags:08X}")
    print()
    print("Segments")
    for index, segment in enumerate(elf.segments):
        print(
            f"  [{index}] type=0x{segment.p_type:08X} "
            f"offset=0x{segment.offset:08X} vaddr=0x{segment.vaddr:08X} "
            f"paddr=0x{segment.paddr:08X} filesz=0x{segment.filesz:08X} "
            f"memsz=0x{segment.memsz:08X} flags=0x{segment.flags:08X} "
            f"align=0x{segment.align:08X}"
        )


def print_pattern_counts(data: bytes) -> None:
    original_offsets = iter_occurrences(data, ORIGINAL_ASPECT_PAIR)
    patched_offsets = iter_occurrences(data, PATCHED_20_9_PAIR)
    print()
    print("Aspect pair byte patterns")
    print(f"  original 16:9 pair count: {len(original_offsets)}")
    for offset in original_offsets:
        print(f"    file_offset=0x{offset:08X}")
    print(f"  patched 20:9 pair count: {len(patched_offsets)}")
    for offset in patched_offsets:
        print(f"    file_offset=0x{offset:08X}")


def print_cwcheat_map(data: bytes, elf: ElfInfo, codes: list[int]) -> None:
    print()
    print("CWCheat address map")
    for code in codes:
        data_address = cwcheat_data_address(code)
        runtime_address = cwcheat_runtime_address(code)
        file_offset = elf.file_offset_for_vaddr(runtime_address)
        current_word = read_u32(data, file_offset)
        expected = EXPECTED_RESTORE.get(code)
        result = ""
        if expected is not None:
            result = " OK" if current_word == expected else f" MISMATCH expected=0x{expected:08X}"
        print(
            f"  code=0x{code:08X} data=0x{data_address:08X} "
            f"runtime=0x{runtime_address:08X} file=0x{file_offset:08X} "
            f"word=0x{current_word:08X}{result}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    parser.add_argument(
        "--code",
        action="append",
        type=lambda value: int(value, 0),
        help="CWCheat code word to map, such as 0x20145F10. May be repeated.",
    )
    args = parser.parse_args()

    data = args.eboot.read_bytes()
    elf = parse_elf(data)
    print_header(data, elf)
    print_pattern_counts(data)
    print_cwcheat_map(data, elf, args.code or KNOWN_ASPECT_CODES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
