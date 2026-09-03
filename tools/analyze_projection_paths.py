#!/usr/bin/env python3
"""Analyze Tekken 6 perspective/orthographic projection call paths.

This helper intentionally avoids Capstone so it can run with only Python's
standard library. It verifies the known 480x272 orthographic setup sites and
finds direct MIPS j/jal references to the projection builders identified during
static analysis.
"""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EBOOT = Path(__file__).resolve().parents[1] / "ULUS10466_EBOOT.BIN"

SEGMENT_FILE_OFFSET = 0x00001018
SEGMENT_VADDR = 0x08804018
SEGMENT_FILE_SIZE = 0x003F62A8

PERSPECTIVE_BUILDER = 0x08ACA6C4
ORTHO_BUILDER = 0x08ACA990

ORIGINAL_RIGHT_BOUND_WORD = 0x3C0143F0  # lui $at, 0x43f0 -> 480.0f
DIAGNOSTIC_RIGHT_BOUND_WORD = 0x3C014416  # lui $at, 0x4416 -> 600.0f


@dataclass(frozen=True)
class OrthoPath:
    name: str
    right_bound_runtime: int
    ortho_call_runtime: int
    matrix_combine_call_runtime: int


ORTHO_PATHS = (
    OrthoPath("A", 0x08863230, 0x08863258, 0x0886327C),
    OrthoPath("B", 0x088634A0, 0x088634E4, 0x088634F4),
    OrthoPath("C", 0x08864494, 0x088644B8, 0x088644D4),
)


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def file_offset_for_runtime(runtime: int) -> int:
    if not SEGMENT_VADDR <= runtime < SEGMENT_VADDR + SEGMENT_FILE_SIZE:
        raise ValueError(f"runtime address 0x{runtime:08X} is outside the file-backed segment")
    return SEGMENT_FILE_OFFSET + (runtime - SEGMENT_VADDR)


def runtime_for_file_offset(offset: int) -> int:
    if not SEGMENT_FILE_OFFSET <= offset < SEGMENT_FILE_OFFSET + SEGMENT_FILE_SIZE:
        raise ValueError(f"file offset 0x{offset:08X} is outside the load segment")
    return SEGMENT_VADDR + (offset - SEGMENT_FILE_OFFSET)


def jump_target(pc: int, word: int) -> int:
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def scan_direct_calls(data: bytes, target: int) -> list[tuple[int, str, int]]:
    results: list[tuple[int, str, int]] = []
    start = SEGMENT_FILE_OFFSET
    end = min(len(data), SEGMENT_FILE_OFFSET + SEGMENT_FILE_SIZE)

    for offset in range(start, end - 3, 4):
        word = read_u32(data, offset)
        opcode = word >> 26
        if opcode not in (0x02, 0x03):
            continue
        runtime = runtime_for_file_offset(offset)
        if jump_target(runtime, word) == target:
            results.append((runtime, "jal" if opcode == 0x03 else "j", word))

    return results


def cwcheat_write32_for_runtime(runtime: int) -> int:
    user_offset = runtime - 0x08800000
    if not 0 <= user_offset <= 0x0FFFFFFF:
        raise ValueError(f"runtime address 0x{runtime:08X} is outside expected PSP user mapping")
    return 0x20000000 | user_offset


def print_calls(data: bytes, label: str, target: int) -> None:
    calls = scan_direct_calls(data, target)
    print(f"{label}: 0x{target:08X}")
    print(f"  direct j/jal references: {len(calls)}")
    for runtime, kind, word in calls:
        print(f"    {kind:<3} 0x{runtime:08X}  word=0x{word:08X}")
    print()


def verify_ortho_paths(data: bytes) -> bool:
    ok = True
    print("Known 480x272 orthographic paths")
    for path in ORTHO_PATHS:
        offset = file_offset_for_runtime(path.right_bound_runtime)
        word = read_u32(data, offset)
        status = "OK" if word == ORIGINAL_RIGHT_BOUND_WORD else "MISMATCH"
        if status != "OK":
            ok = False
        cheat = cwcheat_write32_for_runtime(path.right_bound_runtime)
        print(
            f"  Path {path.name}: right-bound runtime=0x{path.right_bound_runtime:08X} "
            f"file=0x{offset:08X} word=0x{word:08X} [{status}]"
        )
        print(f"    ortho builder call: 0x{path.ortho_call_runtime:08X}")
        print(f"    matrix combine call: 0x{path.matrix_combine_call_runtime:08X}")
        print(f"    diagnostic: _L 0x{cheat:08X} 0x{DIAGNOSTIC_RIGHT_BOUND_WORD:08X}")
        print(f"    restore:    _L 0x{cheat:08X} 0x{ORIGINAL_RIGHT_BOUND_WORD:08X}")
    print()
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    args = parser.parse_args()

    data = args.eboot.read_bytes()
    minimum_size = SEGMENT_FILE_OFFSET + SEGMENT_FILE_SIZE
    if len(data) < minimum_size:
        raise SystemExit(
            f"EBOOT is too small for the documented load segment: "
            f"0x{len(data):X} < 0x{minimum_size:X}"
        )

    print_calls(data, "Perspective builder", PERSPECTIVE_BUILDER)
    print_calls(data, "Orthographic builder", ORTHO_BUILDER)

    if not verify_ortho_paths(data):
        raise SystemExit("One or more documented orthographic sites did not match the expected original word")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
