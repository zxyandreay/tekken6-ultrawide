#!/usr/bin/env python3
"""Focused v0.5 trace for aspect-site ownership and HUD setter callsites."""
from __future__ import annotations

import argparse
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32

DEFAULT_EBOOT = Path(__file__).resolve().parents[1] / "ULUS10466_EBOOT.BIN"
SEG_FILE = 0x00001018
SEG_VADDR = 0x08804018
SEG_SIZE = 0x003F62A8
ASPECT_SITES = [0x08945F10, 0x08946794, 0x08946BC8, 0x08947D90]
XY_SETTER = 0x08A39158
FOCUSED_RANGES = [
    (0x08A39080, 0x08A39170, "2D descriptor tiny-setter family"),
    (0x08998F80, 0x08999040, "UI helper before property lookup"),
    (0x08934E80, 0x08934F40, "2D property-ID mapper"),
    (0x08A31FC0, 0x08A320C0, "fourth property-setter caller"),
    (0x08BC7D60, 0x08BC7DC0, "2D property table data"),
]
DESCRIPTOR_OFFSETS = {0x10, 0x14, 0x18, 0x28, 0x2C, 0x30, 0x34, 0x40, 0x44, 0x48, 0x4C}


def r2o(addr: int) -> int:
    return SEG_FILE + addr - SEG_VADDR


def o2r(off: int) -> int:
    return SEG_VADDR + off - SEG_FILE


def u32(data: bytes, addr: int) -> int:
    return struct.unpack_from("<I", data, r2o(addr))[0]


def jt(pc: int, word: int) -> int:
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def direct_xrefs(data: bytes, target: int) -> list[int]:
    out = []
    end = min(len(data), SEG_FILE + SEG_SIZE)
    for off in range(SEG_FILE, end - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if (w >> 26) in (2, 3) and jt(o2r(off), w) == target:
            out.append(o2r(off))
    return out


def decode(md: Cs, data: bytes, addr: int) -> str:
    ins = list(md.disasm(data[r2o(addr):r2o(addr) + 4], addr, count=1))
    return f"{ins[0].mnemonic} {ins[0].op_str}" if ins else f".word 0x{u32(data, addr):08X}"


def disasm(data: bytes, start: int, end: int, title: str) -> list[str]:
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    lines = [f"## {title}: `0x{start:08X}`–`0x{end:08X}`", "", "```text"]
    for a in range(start, end, 4):
        lines.append(f"0x{a:08X}: {u32(data, a):08X}  {decode(md, data, a)}")
    lines += ["```", ""]
    return lines


def probable_function_start(data: bytes, site: int) -> int:
    # Prefer a normal addiu sp,sp,-N prologue with an RA save nearby.
    for a in range(site, max(SEG_VADDR, site - 0x800), -4):
        w = u32(data, a)
        if (w >> 16) == 0x27BD and (w & 0x8000):
            for b in range(a, min(a + 0x30, site + 4), 4):
                wb = u32(data, b)
                if (wb >> 16) == 0xAFBF:  # sw ra,imm(sp)
                    return a
    return max(SEG_VADDR, site - 0x100)


def probable_function_end(data: bytes, site: int) -> int:
    for a in range(site, min(SEG_VADDR + SEG_SIZE - 8, site + 0x1000), 4):
        if u32(data, a) == 0x03E00008:  # jr ra
            return a + 8
    return site + 0x100


def aspect_report(data: bytes) -> list[str]:
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    lines = ["# v0.5 aspect-site ownership trace", ""]
    for i, site in enumerate(ASPECT_SITES, 1):
        start = probable_function_start(data, site)
        end = probable_function_end(data, site)
        callers = direct_xrefs(data, start)
        lines += [
            f"## Aspect site {i}: `0x{site:08X}`",
            f"- probable containing function: `0x{start:08X}`–`0x{end:08X}`",
            "- direct callers of probable function entry: " + (", ".join(f"`0x{x:08X}`" for x in callers) if callers else "none"),
            f"- patched pair: `0x{u32(data, site):08X}` / `0x{u32(data, site + 4):08X}`",
            "", "```text",
        ]
        lo = max(start, site - 0x60)
        hi = min(end, site + 0x80)
        for a in range(lo, hi, 4):
            marker = "  <== ASPECT" if a == site else ""
            lines.append(f"0x{a:08X}: {u32(data, a):08X}  {decode(md, data, a)}{marker}")
        lines += ["```", ""]
    return lines


def tiny_setter_report(data: bytes) -> list[str]:
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    lines = ["## Tiny descriptor setters near candidate #2", ""]
    start, end = 0x08A39000, 0x08A39900
    found = set()
    for a in range(start, end - 8, 4):
        words = [u32(data, a + i * 4) for i in range(3)]
        # Identify a store to a known descriptor offset followed within 2 words by jr ra.
        useful = False
        for w in words:
            if (w >> 26) == 0x39 and (w & 0xFFFF) in DESCRIPTOR_OFFSETS:  # swc1
                useful = True
        if useful and 0x03E00008 in words:
            found.add(a)
    for a in sorted(found):
        callers = direct_xrefs(data, a)
        lines.append(f"### possible setter `0x{a:08X}`")
        lines.append("- callers: " + (", ".join(f"`0x{x:08X}`" for x in callers) if callers else "none"))
        lines.append("```text")
        for p in range(a, a + 0x10, 4):
            lines.append(f"0x{p:08X}: {u32(data, p):08X}  {decode(md, data, p)}")
        lines += ["```", ""]
    return lines


def xy_report(data: bytes) -> list[str]:
    callers = direct_xrefs(data, XY_SETTER)
    lines = ["## XY setter caller map", "", f"Setter: `0x{XY_SETTER:08X}`", ""]
    for c in callers:
        lines.append(f"### callsite `0x{c:08X}` (return address `0x{c + 8:08X}`)")
        lines += disasm(data, c - 0x18, c + 0x20, "local caller context")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eboot", type=Path, default=DEFAULT_EBOOT)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    data = args.eboot.read_bytes()
    if len(data) < SEG_FILE + SEG_SIZE:
        raise SystemExit("EBOOT is smaller than the mapped executable segment")
    lines = aspect_report(data)
    lines += tiny_setter_report(data)
    lines += xy_report(data)
    for start, end, title in FOCUSED_RANGES:
        lines += disasm(data, start, end, title)
    report = "\n".join(lines)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
