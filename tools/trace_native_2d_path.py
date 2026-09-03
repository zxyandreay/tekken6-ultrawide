#!/usr/bin/env python3
"""Trace Tekken 6's likely common native-PSP 2D presentation paths.

This is intentionally analysis-only. The goal is to distinguish the live
screen-space/sprite transform used by visible HUD/menu rendering from the
already disproven generic 480x272 orthographic paths.
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

PERSPECTIVE = 0x08ACA6C4
ORTHO = 0x08ACA990
VIEWPORT_WRAPPER = 0x08AC5BA8
VIEWPORT_BUILDER = 0x08AC63AC

TARGETS = {
    0x08864ADC: "live flat/surface viewport owner containing 0x08864B88",
    0x08946390: "480x272 setup family feeding the alternate transform",
    VIEWPORT_WRAPPER: "thin wrapper / trampoline candidate",
    VIEWPORT_BUILDER: "forwarded six-float viewport transform behind 0x08AC5BA8",
    ORTHO: "known generic orthographic builder (negative control)",
    0x08ACAB14: "matrix-combine helper used by known ortho paths",
}

FOCUS_RANGES = [
    (0x08864ADC, 0x08864C40, "live flat/surface viewport owner"),
    (0x08946390, 0x0894650C, "480x272 setup family that calls 0x08AC5BA8"),
    (0x08AC5B8C, 0x08AC5C00, "wrapper cluster around 0x08AC5BA8"),
    (0x08AC6380, 0x08AC65C0, "forwarded viewport transform at 0x08AC63AC"),
    (0x08AA62D8, 0x08AA655C, "high-ranked 2D widget/render family"),
]

SCREEN_UPPERS = {
    0x43F0: "480.0",
    0x4388: "272.0",
    0x4370: "240.0",
    0x4308: "136.0",
    0x4400: "512.0",
    0x43A0: "320.0",
}


def r2o(addr: int) -> int:
    return SEG_FILE + addr - SEG_VADDR


def o2r(off: int) -> int:
    return SEG_VADDR + off - SEG_FILE


def u32(data: bytes, addr: int) -> int:
    return struct.unpack_from("<I", data, r2o(addr))[0]


def jump_target(pc: int, word: int) -> int:
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def direct_xrefs(data: bytes, target: int) -> list[int]:
    out: list[int] = []
    end = min(len(data), SEG_FILE + SEG_SIZE)
    for off in range(SEG_FILE, end - 3, 4):
        word = struct.unpack_from("<I", data, off)[0]
        if (word >> 26) in (2, 3) and jump_target(o2r(off), word) == target:
            out.append(o2r(off))
    return out


def probable_function_start(data: bytes, site: int, max_back: int = 0x1000) -> int:
    low = max(SEG_VADDR, site - max_back)
    for addr in range(site & ~3, low - 1, -4):
        word = u32(data, addr)
        if (word & 0xFFFF0000) != 0x27BD0000:
            continue
        imm = word & 0xFFFF
        if imm < 0x8000:
            continue
        for probe in range(addr + 4, min(site + 4, addr + 0x40), 4):
            if (u32(data, probe) & 0xFFFF0000) == 0xAFBF0000:
                return addr
    return max(SEG_VADDR, site - 0x100)


def probable_function_end(data: bytes, start: int, max_fwd: int = 0x1800) -> int:
    high = min(SEG_VADDR + SEG_SIZE - 8, start + max_fwd)
    for addr in range(start, high, 4):
        if u32(data, addr) == 0x03E00008:
            return addr + 8
    return min(high, start + 0x300)


def decode(md: Cs, data: bytes, addr: int) -> str:
    insns = list(md.disasm(data[r2o(addr):r2o(addr) + 4], addr, count=1))
    if not insns:
        return f".word 0x{u32(data, addr):08X}"
    ins = insns[0]
    return f"{ins.mnemonic} {ins.op_str}".rstrip()


def direct_calls_in_range(data: bytes, start: int, end: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for addr in range(max(SEG_VADDR, start), min(SEG_VADDR + SEG_SIZE, end), 4):
        word = u32(data, addr)
        if word >> 26 == 3:
            out.append((addr, jump_target(addr, word)))
    return out


def render_classification(data: bytes, start: int, end: int) -> str:
    calls = {target for _, target in direct_calls_in_range(data, start, end)}
    flags = []
    if PERSPECTIVE in calls:
        flags.append("perspective")
    if ORTHO in calls:
        flags.append("orthographic")
    if VIEWPORT_WRAPPER in calls or VIEWPORT_BUILDER in calls:
        flags.append("viewport")
    if not flags:
        return "no direct perspective/ortho/viewport marker"
    return ", ".join(flags)


def screen_constant_notes(data: bytes, start: int, end: int) -> list[str]:
    notes: list[str] = []
    for addr in range(max(SEG_VADDR, start), min(SEG_VADDR + SEG_SIZE, end), 4):
        word = u32(data, addr)
        if word >> 26 == 0x0F:
            imm = word & 0xFFFF
            if imm in SCREEN_UPPERS:
                notes.append(f"`0x{addr:08X}` loads upper half of {SCREEN_UPPERS[imm]}")
    return notes


def disasm_range(md: Cs, data: bytes, start: int, end: int, markers: set[int] | None = None) -> list[str]:
    markers = markers or set()
    lines = ["```text"]
    for addr in range(max(SEG_VADDR, start), min(SEG_VADDR + SEG_SIZE, end), 4):
        marker = " <==" if addr in markers else ""
        lines.append(f"0x{addr:08X}: {u32(data, addr):08X}  {decode(md, data, addr)}{marker}")
    lines.append("```")
    return lines


def caller_context(md: Cs, data: bytes, callsite: int) -> list[str]:
    start = max(SEG_VADDR, callsite - 0x60)
    end = min(SEG_VADDR + SEG_SIZE, callsite + 0x40)
    fn_start = probable_function_start(data, callsite)
    fn_end = probable_function_end(data, fn_start)
    scan_start = max(fn_start, callsite - 0x400)
    scan_end = min(SEG_VADDR + SEG_SIZE, max(fn_end, callsite + 0x400))
    notes = screen_constant_notes(data, scan_start, scan_end)
    lines = [
        f"- probable caller function: `0x{fn_start:08X}`–`0x{fn_end:08X}`",
        f"- render markers in caller scan: {render_classification(data, scan_start, scan_end)}",
        "- nearby PSP-screen constants: " + ("; ".join(notes) if notes else "none in caller scan"),
    ]
    marker_calls = [
        (src, target) for src, target in direct_calls_in_range(data, scan_start, scan_end)
        if target in {PERSPECTIVE, ORTHO, VIEWPORT_WRAPPER, VIEWPORT_BUILDER}
    ]
    if marker_calls:
        lines.append("- marker calls:")
        for src, target in marker_calls:
            lines.append(f"  - `0x{src:08X}` -> `0x{target:08X}`")
    lines += disasm_range(md, data, start, end, {callsite})
    return lines


def target_report(md: Cs, data: bytes, target: int, label: str) -> list[str]:
    callers = direct_xrefs(data, target)
    fn_start = probable_function_start(data, target)
    fn_end = probable_function_end(data, fn_start)
    scan_start = max(fn_start, target - 0x400)
    scan_end = min(SEG_VADDR + SEG_SIZE, max(fn_end, target + 0x400))
    lines = [
        f"## {label}: `0x{target:08X}`",
        f"- probable containing function: `0x{fn_start:08X}`–`0x{fn_end:08X}`",
        f"- direct xrefs: {len(callers)}",
        f"- render markers in function scan: {render_classification(data, scan_start, scan_end)}",
        "- function PSP-screen constants: " + ("; ".join(screen_constant_notes(data, scan_start, scan_end)) or "none"),
        "",
    ]
    body_start = max(SEG_VADDR, target - 0x80)
    body_end = min(SEG_VADDR + SEG_SIZE, target + 0x260)
    lines += disasm_range(md, data, body_start, body_end, {target})
    lines.append("")
    for callsite in callers:
        lines.append(f"### caller `0x{callsite:08X}`")
        lines += caller_context(md, data, callsite)
        lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data = args.eboot.read_bytes()
    if len(data) < SEG_FILE + SEG_SIZE:
        raise SystemExit("EBOOT is smaller than the mapped executable segment")

    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True

    lines = [
        "# Native PSP 2D safe-area trace",
        "",
        "Goal: find a common 2D presentation transform that can preserve Tekken's native 480x272 authored coordinates/proportions while the validated 3D projection remains ultrawide.",
        "",
    ]

    for target, label in TARGETS.items():
        lines += target_report(md, data, target, label)

    for start, end, label in FOCUS_RANGES:
        lines += [f"## Focus range: {label} `0x{start:08X}`–`0x{end:08X}`", ""]
        lines += disasm_range(md, data, start, end)
        lines.append("")

    report = "\n".join(lines) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
