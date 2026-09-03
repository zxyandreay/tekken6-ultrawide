#!/usr/bin/env python3
"""Rank Tekken 6 functions that resemble a HUD/screen-space scale path.

This is a static-analysis helper for the decrypted ULUS10466 EBOOT. It is
inspired by the architecture used by The Warriors PPSSPP Fusion Fix: search for
a small live screen-space/HUD setup path where an aspect/scale operand can be
injected independently of the 3D projection aspect.

It does NOT patch the game and does not claim any candidate is HUD code.
"""
from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EBOOT = Path(__file__).resolve().parents[1] / "ULUS10466_EBOOT.BIN"
SEG_FILE = 0x00001018
SEG_VADDR = 0x08804018
SEG_SIZE = 0x003F62A8

SCREEN_UPPERS = {
    0x43F0: "480.0",
    0x4388: "272.0",
    0x4370: "240.0",
    0x4308: "136.0",
    0x4400: "512.0",
    0x43A0: "320.0",
    0x4380: "256.0",
    0x4320: "160.0",
}

# Paths that have already been classified negatively or are known to be too
# global. They are retained in the output, but deliberately penalized.
KNOWN_NOOP_RANGES = [
    (0x088631E0, 0x088632A0, "ortho Path A: user-visible no-op"),
    (0x08863450, 0x08863530, "ortho Path B: user-visible no-op"),
    (0x08864440, 0x08864510, "ortho Path C: user-visible no-op"),
]
KNOWN_GLOBAL_RANGES = [
    (0x08864ADC, 0x08864C40, "broad viewport/surface state; historical overlay regressions"),
    (0x08946390, 0x089464D0, "broad viewport/surface state"),
]


@dataclass
class Function:
    start_off: int
    end_off: int
    start_rt: int
    end_rt: int


def read_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def runtime_for_offset(offset: int) -> int:
    return SEG_VADDR + (offset - SEG_FILE)


def jump_target(pc: int, word: int) -> int:
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def is_probable_prologue(word: int) -> bool:
    # addiu sp, sp, negative_immediate
    if (word & 0xFFFF0000) != 0x27BD0000:
        return False
    imm = word & 0xFFFF
    signed = imm if imm < 0x8000 else imm - 0x10000
    return signed < 0


def collect_functions(data: bytes) -> list[Function]:
    starts: list[int] = []
    end = min(len(data), SEG_FILE + SEG_SIZE)

    for offset in range(SEG_FILE, end - 3, 4):
        word = read_u32(data, offset)
        if not is_probable_prologue(word):
            continue

        # Require an ra save shortly after the stack adjustment to reduce
        # false-positive function starts.
        has_ra_save = False
        for probe in range(offset + 4, min(offset + 0x34, end - 3), 4):
            if (read_u32(data, probe) & 0xFFFF0000) == 0xAFBF0000:
                has_ra_save = True
                break
        if has_ra_save:
            starts.append(offset)

    functions: list[Function] = []
    for index, start in enumerate(starts):
        stop = starts[index + 1] if index + 1 < len(starts) else end
        # Do not let a missed prologue create a huge pseudo-function.
        if stop - start > 0x3000:
            stop = start + 0x3000
        functions.append(
            Function(start, stop, runtime_for_offset(start), runtime_for_offset(stop))
        )
    return functions


def range_notes(start_rt: int, end_rt: int) -> list[str]:
    notes: list[str] = []
    for start, end, label in KNOWN_NOOP_RANGES:
        if start_rt < end and end_rt > start:
            notes.append("PENALTY: " + label)
    for start, end, label in KNOWN_GLOBAL_RANGES:
        if start_rt < end and end_rt > start:
            notes.append("PENALTY: " + label)
    return notes


def analyze_function(data: bytes, function: Function):
    constants: list[tuple[int, str]] = []
    calls: list[tuple[int, int]] = []
    swc1 = 0
    lwc1 = 0
    cop1 = 0

    for offset in range(function.start_off, function.end_off - 3, 4):
        word = read_u32(data, offset)
        opcode = word >> 26

        if opcode == 0x0F and (word & 0xFFFF) in SCREEN_UPPERS:
            constants.append((runtime_for_offset(offset), SCREEN_UPPERS[word & 0xFFFF]))

        if opcode == 0x03:  # jal
            calls.append((runtime_for_offset(offset), jump_target(runtime_for_offset(offset), word)))

        if opcode == 0x39:  # swc1
            swc1 += 1
        if opcode == 0x31:  # lwc1
            lwc1 += 1
        if opcode == 0x11:  # COP1 / floating point
            cop1 += 1

    labels = {label for _, label in constants}

    # This is intentionally a heuristic score. It favors screen-dimension
    # initialization mixed with floating-point state writes and calls, which is
    # closer to the kind of live HUD-scale path used by The Warriors than a
    # generic final viewport.
    score = 0
    score += len(constants) * 2
    if "480.0" in labels:
        score += 5
    if "272.0" in labels:
        score += 5
    if "480.0" in labels and "272.0" in labels:
        score += 8
    if "240.0" in labels or "136.0" in labels:
        score += 2
    score += min(swc1, 16)
    score += min(cop1 // 3, 8)
    score += min(len(calls), 8)

    size = function.end_off - function.start_off
    if 0x40 <= size <= 0x500:
        score += 4
    if size > 0x1000:
        score -= 5

    notes = range_notes(function.start_rt, function.end_rt)
    for note in notes:
        score -= 20 if "no-op" in note else 12

    return score, constants, calls, swc1, lwc1, cop1, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    data = args.eboot.read_bytes()
    minimum = SEG_FILE + SEG_SIZE
    if len(data) < minimum:
        raise SystemExit(f"EBOOT too small: 0x{len(data):X} < 0x{minimum:X}")

    rows = []
    for function in collect_functions(data):
        result = analyze_function(data, function)
        score, constants, *_ = result
        if constants:
            rows.append((score, function, result))
    rows.sort(key=lambda row: (-row[0], row[1].start_rt))

    lines = [
        "# Warriors-style HUD candidate ranking",
        "",
        "This report is a heuristic ranking, not proof of HUD ownership. It favors functions that combine PSP-sized screen constants with floating-point/render-state setup, while penalizing the A/B/C orthographic paths that produced no visible change and the broad viewport path that historically broke overlays.",
        "",
    ]

    for rank, (score, function, result) in enumerate(rows[: args.top], 1):
        _, constants, calls, swc1, lwc1, cop1, notes = result
        lines.extend(
            [
                f"## {rank}. `0x{function.start_rt:08X}`–`0x{function.end_rt:08X}` — score {score}",
                f"- size: `0x{function.end_off - function.start_off:X}` bytes",
                "- screen constants: "
                + ", ".join(f"`{name}` @ `0x{address:08X}`" for address, name in constants),
                f"- `swc1`: {swc1}; `lwc1`: {lwc1}; COP1 instructions: {cop1}",
                f"- direct calls: {len(calls)}",
            ]
        )
        for source, destination in calls[:12]:
            lines.append(f"  - `0x{source:08X}` -> `0x{destination:08X}`")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- The Warriors fix succeeded because it found a HUD-specific scale operand separate from the 3D aspect operand. These Tekken candidates should be investigated for the same kind of live screen-space scale/aspect value.",
            "- Do not patch every 480/272 occurrence. Trace data flow and caller ownership first.",
            "- Full-screen overlays/fades may require exclusion or caller-aware handling even if they share a sprite submission family.",
            "",
        ]
    )

    report = "\n".join(lines)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {args.output} ({len(rows)} functions with screen constants)")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
