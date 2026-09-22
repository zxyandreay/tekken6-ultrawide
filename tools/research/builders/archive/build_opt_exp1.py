#!/usr/bin/env python3
"""Build the renderer-optimization OPT-EXP1 test PRX from released v1.2.0.

This is a binary-level experiment because the exact compact v1.2.0 HUD implementation
is authoritative only in the released PRX. The build preserves the validated one-LOAD
0x0EB0/0x0EB0 layout.

OPT-EXP1 removes installation of the two upstream HP gauge hooks and reuses their dead
wrapper space for an exact downstream HP transform inside the already-hooked
D56C/D5B0 sprite dispatcher.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import struct
import zipfile
from pathlib import Path

BASE_PRX_SHA256 = "311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75"
BASE_ZIP_B64 = "release/v1.2.0/Tekken6-Ultrawide-v1.2.0.zip.b64"
PRX_PATH = "PSP/PLUGINS/Tekken6Ultrawide/Tekken6Ultrawide.prx"
TEXT_FILE_OFFSET = 0x60
REL_TEXT_FILE_OFFSET = 0x1280
REL_TEXT_SIZE = 0x1D0

def i_type(op: int, rs: int, rt: int, imm: int) -> int:
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)

def r_type(rs: int, rt: int, rd: int, shamt: int, funct: int) -> int:
    return (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | funct

def j_type(op: int, target: int) -> int:
    return (op << 26) | ((target >> 2) & 0x03FFFFFF)

def cop1_s(ft: int, fs: int, fd: int, funct: int) -> int:
    return (0x11 << 26) | (0x10 << 21) | (ft << 16) | (fs << 11) | (fd << 6) | funct

def branch(op: int, rs: int, rt: int, pc: int, target: int) -> int:
    delta = target - (pc + 4)
    if delta % 4:
        raise ValueError("unaligned branch target")
    offset = delta // 4
    if not -32768 <= offset <= 32767:
        raise ValueError("branch out of range")
    return i_type(op, rs, rt, offset)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_release_prx(root: Path) -> bytes:
    encoded = (root / BASE_ZIP_B64).read_bytes()
    archive = base64.b64decode(encoded)
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        prx = zf.read(PRX_PATH)
    if sha256(prx) != BASE_PRX_SHA256:
        raise RuntimeError("released v1.2.0 PRX hash mismatch")
    return prx

def patch_prx(prx: bytes) -> bytes:
    data = bytearray(prx)

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    expected = {
        0x3F0: 0xACA80000,
        0x3F4: 0xACA4007C,
        0x7E4: 0x8D2CFFD8,
        0x850: 0x8C8C0004,
        0x854: 0x3C0D41B0,
        0x858: 0x118D000B,
        0x85C: 0x00000000,
        0x860: 0x3C0D4260,
        0x864: 0x158D0031,
        0x868: 0x00000000,
        0x86C: 0x8C8C0018,
        0x92C: 0x0A2097AB,
    }
    for va, wanted in expected.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(f"unexpected base word at {va:#x}: {got:#010x} != {wanted:#010x}")

    # Do not install the two old upstream gauge-owner hooks.
    write_word(0x3F0, 0)
    write_word(0x3F4, 0)

    # Reuse the dead upstream wrapper as the downstream HP handler.
    # Entry is reached only after the shared wrapper sees packet Y == 21.0f.
    handler = {
        0x7E4: i_type(0x23, 4, 12, 0x08),                     # lw t4,8(a0) / Z
        0x7E8: i_type(0x0F, 0, 13, 0x447A),                  # 1000.0f
        0x7EC: branch(5, 12, 13, 0x7EC, 0x92C),              # reject wrong Z
        0x7F0: i_type(0x0F, 0, 13, 0x08BA),                  # descriptor base high
        0x7F4: i_type(9, 13, 13, -0x441C),                   # 0x08B9BBE4 (side ID 6)
        0x7F8: r_type(7, 13, 14, 0, 0x23),                   # subu t6,a3,t5
        0x7FC: i_type(0x0B, 14, 12, 0x31),                   # delta <= 0x30
        0x800: branch(4, 12, 0, 0x800, 0x92C),
        0x804: i_type(0x0C, 14, 13, 0x0F),                   # 16-byte descriptor alignment
        0x808: branch(5, 13, 0, 0x808, 0x92C),
        0x80C: i_type(0x0B, 14, 12, 0x20),                   # IDs 6/7 vs 8/9
        0x810: i_type(0x0E, 12, 12, 1),
        0x814: i_type(9, 12, 12, 0x0D),                      # expected resource 0D/0E
        0x818: branch(5, 5, 12, 0x818, 0x92C),
        0x81C: i_type(0x0F, 0, 13, 0x0880),                  # coefficient address base
        0x820: i_type(0x31, 13, 2, 0x2310),                  # lwc1 f2,hp_shift
        0x824: i_type(0x31, 4, 0, 0x0000),                   # lwc1 f0,x
        0x828: i_type(0x31, 4, 4, 0x0020),                   # lwc1 f4,orientation
        0x82C: cop1_s(2, 4, 4, 0x02),                        # mul.s f4,f4,f2
        0x830: cop1_s(4, 0, 0, 0x01),                        # sub.s f0,f0,f4
        0x834: i_type(0x39, 4, 0, 0x0000),                   # swc1 f0,x
        0x838: i_type(0x31, 4, 0, 0x0018),                   # lwc1 f0,width
        0x83C: i_type(0x31, 13, 4, 0x2314),                  # lwc1 f4,hp_scale
        0x840: cop1_s(4, 0, 0, 0x02),                        # mul.s f0,f0,f4
        0x844: i_type(0x39, 4, 0, 0x0018),                   # swc1 f0,width
        0x848: j_type(2, 0x08825EAC),
        0x84C: 0,
    }
    for va, word in handler.items():
        write_word(va, word)

    # Add a compact Y=21 HP handoff to the existing side/rank wrapper.
    write_word(0x854, i_type(0x0F, 0, 13, 0x41A8))
    write_word(0x858, branch(4, 12, 13, 0x858, 0x7E4))
    write_word(0x85C, i_type(0x0F, 0, 13, 0x41B0))
    write_word(0x860, branch(4, 12, 13, 0x860, 0x888))
    write_word(0x864, i_type(0x0F, 0, 13, 0x4260))
    write_word(0x868, branch(5, 12, 13, 0x868, 0x92C))

    # Old upstream wrapper used a module-local HI16/LO16 pair at 0x7F4/0x7F8.
    # These entries must become R_MIPS_NONE or the PSP loader would rewrite new instructions.
    found = set()
    for pos in range(REL_TEXT_FILE_OFFSET, REL_TEXT_FILE_OFFSET + REL_TEXT_SIZE, 8):
        offset, info = struct.unpack_from("<II", data, pos)
        if offset in (0x7F4, 0x7F8):
            found.add(offset)
            struct.pack_into("<I", data, pos + 4, 0)
    if found != {0x7F4, 0x7F8}:
        raise RuntimeError(f"expected relocation entries not found: {found}")

    # Preserve the resident-layout invariant.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phnum != 1 or e_phentsize != 32:
        raise RuntimeError("unexpected program header layout")
    p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from(
        "<IIIIIIII", data, e_phoff
    )
    if (p_type, p_filesz, p_memsz) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError(
            f"resident layout changed: type={p_type} filesz={p_filesz:#x} memsz={p_memsz:#x}"
        )

    return bytes(data)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP1.prx"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    patched = patch_prx(read_release_prx(root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    print(f"Wrote {args.output}")
    print(f"SHA-256 {sha256(patched)}")
    print(f"Size {len(patched)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")

if __name__ == "__main__":
    main()
