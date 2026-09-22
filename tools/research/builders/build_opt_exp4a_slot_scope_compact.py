#!/usr/bin/env python3
"""Build OPT-EXP4A-SlotScopeCompact from accepted OPT-EXP3D-A.

This candidate keeps the exact 13 slot callsites and the same scope-counter
semantics. It only compacts the module-local wrapper at 0x05A0..0x0647.

Why the old wrapper can be reduced
----------------------------------
Before calling stock 0x0892D9F8, the accepted wrapper saves/restores:
- a0-a3
- t0-t3
- f12

But the wrapper itself does not modify those values. It only uses t4/t5 and the
scope counter, and it needs original a1 after the stock call to know whether to
decrement the scope.

The compact wrapper therefore preserves only:
- original ra
- original a1
- the scope-counter pointer for the matched 0xEF path

It intentionally preserves the same t4/t5 values at the stock-call boundary and
at wrapper return as the accepted wrapper.

Four old module-local HI16/LO16 relocation entries belong to the two removed
counter-address materializations. They are changed to R_MIPS_NONE.

No callsite topology changes.
No winner-glow code changes.
No GitHub Actions are used or required.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

BASE_SHA256 = "d8afe941dc3198107a460511d78fa2d8acde6f709020a7b351605e6a6fdfe17f"
OUT_SHA256 = "6a537691e758dabc912910b9cfb1758e9ea9b5a2554242a43ff87e281c32a8e8"

TEXT_FILE_OFFSET = 0x60
REL_TEXT_FILE_OFFSET = 0x1280
REL_TEXT_SIZE = 0x1D0

def i_type(op: int, rs: int, rt: int, imm: int) -> int:
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)

def j_type(op: int, target: int) -> int:
    return (op << 26) | ((target >> 2) & 0x03FFFFFF)

def branch(op: int, rs: int, rt: int, pc: int, target: int) -> int:
    delta = target - (pc + 4)
    if delta % 4:
        raise ValueError("unaligned branch")
    off = delta // 4
    if not -32768 <= off <= 32767:
        raise ValueError("branch out of range")
    return i_type(op, rs, rt, off)

def patch(prx: bytes) -> bytes:
    if hashlib.sha256(prx).hexdigest() != BASE_SHA256:
        raise RuntimeError("OPT-EXP3D-A base hash mismatch")

    data = bytearray(prx)

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    # Exact accepted wrapper anchors.
    expected = {
        0x05A0: 0x27BDFFC0,
        0x05A4: 0xAFBF003C,
        0x05A8: 0xAFA40000,
        0x05AC: 0xAFA50004,
        0x05C8: 0xE7AC0020,
        0x05CC: 0x240C00EF,
        0x05D8: 0x3C0C0000,
        0x05DC: 0x258C0C44,
        0x0610: 0x0E24B67E,
        0x0618: 0x8FAC0004,
        0x0628: 0x3C0C0000,
        0x062C: 0x258C0C44,
        0x0640: 0x03E00008,
        0x0644: 0x27BD0040,
        0x0648: 0x3C0C0000,
    }
    for va, wanted in expected.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(
                f"unexpected accepted word at {va:#x}: {got:#010x} != {wanted:#010x}"
            )

    # Compact wrapper: 0x60 bytes, ending at module+0x0600 inclusive.
    compact = {
        0x05A0: i_type(9, 29, 29, -0x10),                # addiu sp,sp,-16
        0x05A4: i_type(0x2B, 29, 31, 0x0C),             # sw ra,12(sp)
        0x05A8: i_type(9, 0, 12, 0x00EF),               # li t4,0xef
        0x05AC: branch(5, 5, 12, 0x05AC, 0x05D0),       # bne a1,t4,call
        0x05B0: i_type(0x2B, 29, 5, 0x08),              # delay: save original a1
        0x05B4: branch(1, 0, 17, 0x05B4, 0x05BC),       # bal local PC getter
        0x05B8: 0,
        0x05BC: i_type(9, 31, 12, 0x0688),              # t4 = module+0x0c44
        0x05C0: i_type(0x2B, 29, 12, 0x04),             # save counter pointer
        0x05C4: i_type(0x23, 12, 13, 0),                # lw t5,0(t4)
        0x05C8: i_type(9, 13, 13, 1),                   # ++scope
        0x05CC: i_type(0x2B, 12, 13, 0),                # sw scope
        0x05D0: j_type(3, 0x0892D9F8),                  # stock slot builder
        0x05D4: 0,
        0x05D8: i_type(0x23, 29, 12, 0x08),             # original a1
        0x05DC: i_type(9, 0, 13, 0x00EF),               # li t5,0xef
        0x05E0: branch(5, 12, 13, 0x05E0, 0x05F8),      # non-scope -> return
        0x05E4: 0,
        0x05E8: i_type(0x23, 29, 12, 0x04),             # saved counter pointer
        0x05EC: i_type(0x23, 12, 13, 0),                # lw t5,0(t4)
        0x05F0: i_type(9, 13, 13, -1),                  # --scope
        0x05F4: i_type(0x2B, 12, 13, 0),                # sw scope
        0x05F8: i_type(0x23, 29, 31, 0x0C),             # restore original ra
        0x05FC: 0x03E00008,                              # jr ra
        0x0600: i_type(9, 29, 29, 0x10),                # delay: restore sp
    }

    for va in range(0x05A0, 0x0648, 4):
        write_word(va, compact.get(va, 0))

    # The removed wrapper had two relocated address-materialization pairs for
    # module+0x0c44. The compact wrapper uses a relocation-free BAL-relative
    # pointer, so all four old relocations must be disabled.
    expected_relocs = {
        0x05D8: 5,
        0x05DC: 6,
        0x0628: 5,
        0x062C: 6,
    }
    found = {}
    for pos in range(REL_TEXT_FILE_OFFSET, REL_TEXT_FILE_OFFSET + REL_TEXT_SIZE, 8):
        offset, info = struct.unpack_from("<II", data, pos)
        if offset in expected_relocs:
            found[offset] = info
            if info != expected_relocs[offset]:
                raise RuntimeError(
                    f"unexpected relocation type at {offset:#x}: {info}"
                )
            struct.pack_into("<I", data, pos + 4, 0)

    if found != expected_relocs:
        raise RuntimeError(f"missing wrapper relocations: {found}")

    # Newly detached tail must be zero.
    if any(data[TEXT_FILE_OFFSET + 0x0604:TEXT_FILE_OFFSET + 0x0648]):
        raise RuntimeError("new wrapper tail is not fully zero")

    # Keep adjacent runtime topology byte-identical.
    if data[TEXT_FILE_OFFSET + 0x0648:TEXT_FILE_OFFSET + 0x0934] !=        prx[TEXT_FILE_OFFSET + 0x0648:TEXT_FILE_OFFSET + 0x0934]:
        raise RuntimeError("rectangle/HP runtime code changed unexpectedly")

    # Frozen winner-glow path must remain exact.
    if data[TEXT_FILE_OFFSET + 0x0CF0:TEXT_FILE_OFFSET + 0x0E08] !=        prx[TEXT_FILE_OFFSET + 0x0CF0:TEXT_FILE_OFFSET + 0x0E08]:
        raise RuntimeError("frozen winner-glow path changed")

    # Relocated one-hook font helper must remain exact.
    if data[TEXT_FILE_OFFSET + 0x0AC4:TEXT_FILE_OFFSET + 0x0AF8] !=        prx[TEXT_FILE_OFFSET + 0x0AC4:TEXT_FILE_OFFSET + 0x0AF8]:
        raise RuntimeError("font helper changed")

    # Existing 64-byte hard-free block remains free.
    if any(data[TEXT_FILE_OFFSET + 0x0C00:TEXT_FILE_OFFSET + 0x0C40]):
        raise RuntimeError("existing 64-byte hard-free block was consumed")

    # Resident-layout invariant.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError("resident layout changed")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OUT_SHA256:
        raise RuntimeError("OPT-EXP4A output hash mismatch")
    return result

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP4A-SlotScopeCompact.prx"))
    args = ap.parse_args()

    out = patch(args.base.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(out).hexdigest()}")
    print("Slot wrapper: 168 bytes -> 96 bytes")
    print("New detached zero tail: 72 bytes at 0x0604..0x0647")
    print("Existing detached zero block: 64 bytes at 0x0C00..0x0C3F")
    print("Candidate general hard-free total after validation: 136 bytes")
    print("Winner-glow path: frozen and byte-identical")

if __name__ == "__main__":
    main()
