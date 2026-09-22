#!/usr/bin/env python3
"""Build OPT-EXP3A-OneHookScratch from accepted OPT-EXP2S3.

Purpose
-------
Collapse the two dynamic Practice/Gold font hook entries into one dynamic game
hook at 0x08970A90 while preserving the accepted visible behavior.

The late game site at 0x08970B24 becomes a simple static instruction:
    lw a0,0x28(sp)

The early hook prepares 0x28(sp) only for the slow path. The scratch lifetime is
bounded inside the same stock function frame and stock code clears it at
0x08970B40.

This candidate deliberately does NOT consume:
- the 52-byte hard-free compressed-table tail;
- the 24-byte unreachable winner-glow X classifier;
- the 8 startup-only NOP words.

No GitHub Actions are used or required.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

import build_opt_exp1 as exp1
import build_opt_exp2s2 as exp2s2
import build_opt_exp2s3_glowslots as exp2s3

TEXT_FILE_OFFSET = 0x60
BASE_SHA256 = "7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805"
OUT_SHA256 = "46063c6097e3dfaa51aafd077e0e5c65f02487bdbe420f8884f2a292edf8cf1f"

def i_type(op: int, rs: int, rt: int, imm: int) -> int:
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)

def r_type(rs: int, rt: int, rd: int, shamt: int, funct: int) -> int:
    return (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | funct

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

def patch_exp3a(prx: bytes) -> bytes:
    if hashlib.sha256(prx).hexdigest() != BASE_SHA256:
        raise RuntimeError("OPT-EXP2S3 base hash mismatch")

    data = bytearray(prx)

    def read_word(va: int) -> int:
        return struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]

    def write_word(va: int, word: int) -> None:
        struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

    # Protect the accepted S3 checkpoint before editing.
    expected = {
        0x0C00: 0x8EC402C8,  # old late helper: lw a0,0x2c8(s6)
        0x0C38: 0x03E00008,
        0x0C60: 0xAFBF000C,
        0x0C98: 0x3C0C0897,
        0x0CA0: 0xAD8B0000,  # old A90 dynamic hook install
        0x0CE4: 0x258C0094,  # old helper computes B24
        0x0CEC: 0xAD8B0000,  # old B24 dynamic hook install
        0x0E08: 0x3C030897,  # old dual-entry font hook
        0x0EA8: 0x1000FF55,  # old late-entry branch to C00
    }
    for va, wanted in expected.items():
        got = read_word(va)
        if got != wanted:
            raise RuntimeError(
                f"unexpected accepted-S3 word at {va:#x}: {got:#010x} != {wanted:#010x}"
            )

    # Repurpose the existing 64-byte late helper as the bounded early-hook
    # postprocessor. It is reached only from the early dynamic hook.
    for va in range(0x0C00, 0x0C40, 4):
        write_word(va, 0)

    helper = {
        0x0C00: i_type(0x0F, 0, 2, 0x0880),              # lui v0,0x0880
        0x0C04: i_type(0x23, 2, 11, 0x2318),             # lw t3,dynamic X scale
        0x0C08: i_type(9, 0, 3, 100),                    # li v1,100
        0x0C0C: branch(4, 9, 3, 0x0C0C, 0x0C2C),         # fast vertical path -> return
        0x0C10: 0,
        0x0C14: branch(4, 8, 0, 0x0C14, 0x0C28),         # Practice: no Gold X shift
        0x0C18: i_type(0x23, 2, 3, 0x231C),              # delay: dynamic Gold shift
        0x0C1C: i_type(0x23, 29, 8, 0x58),               # lw t0,authored X
        0x0C20: r_type(8, 3, 8, 0, 0x21),                # addu t0,t0,v1
        0x0C24: i_type(0x2B, 29, 8, 0x58),               # sw shifted X
        0x0C28: i_type(0x2B, 29, 11, 0x28),              # slow path scratch = corrected scale
        0x0C2C: j_type(2, 0x08970A98),                   # resume stock after A90
        0x0C30: 0,
    }
    for va, word in helper.items():
        write_word(va, word)

    # Repack the compact startup extension:
    # - winner-glow call still gets its dynamic JAL;
    # - A90 gets the one dynamic font JAL;
    # - B24 gets a static lw a0,0x28(sp), not another dynamic hook;
    # - cache maintenance remains explicit and relocation-safe.
    installer = {
        0x0C60: i_type(0x2B, 29, 31, 0x0C),
        0x0C64: branch(1, 0, 17, 0x0C64, 0x0C6C),        # bal
        0x0C68: 0,
        0x0C6C: i_type(9, 31, 8, 0x84),                 # local glow hook VA
        0x0C70: r_type(0, 8, 9, 2, 2),                  # srl t1,t0,2
        0x0C74: i_type(0x0F, 0, 10, 0x0C00),
        0x0C78: r_type(9, 10, 9, 0, 0x25),              # form JAL
        0x0C7C: i_type(9, 31, 8, 0x019C),               # local font hook VA
        0x0C80: r_type(0, 8, 11, 2, 2),
        0x0C84: r_type(11, 10, 11, 0, 0x25),            # form JAL
        0x0C88: i_type(0x0F, 0, 12, 0x08AC),
        0x0C8C: i_type(0x0D, 12, 12, 0x9C38),
        0x0C90: i_type(0x2B, 12, 9, 0),                 # patch glow call
        0x0C94: i_type(0x0F, 0, 12, 0x0897),
        0x0C98: i_type(0x0D, 12, 12, 0x0A90),
        0x0C9C: i_type(0x2B, 12, 11, 0),                # patch A90 -> one font hook
        0x0CA0: i_type(9, 12, 12, 0x94),                # B24
        0x0CA4: i_type(0x0F, 0, 11, 0x8FA4),
        0x0CA8: i_type(0x0D, 11, 11, 0x0028),           # lw a0,0x28(sp)
        0x0CAC: i_type(0x2B, 12, 11, 0),                # patch B24 statically
        0x0CB0: branch(1, 0, 17, 0x0CB0, 0x0CB8),       # bal for local stubs
        0x0CB4: 0,
        0x0CB8: i_type(9, 31, 14, -0x374),              # -> 0x944
        0x0CBC: r_type(14, 0, 31, 0, 9),                # jalr t6
        0x0CC0: 0,
        0x0CC4: i_type(9, 31, 14, -0x378),              # return RA -> 0x94c
        0x0CC8: i_type(0x0F, 0, 4, 0x0897),
        0x0CCC: i_type(0x0D, 4, 4, 0x0A90),
        0x0CD0: i_type(0x0F, 0, 5, 0x0015),
        0x0CD4: i_type(0x0D, 5, 5, 0x91AC),             # flush A90..glow site
        0x0CD8: r_type(14, 0, 31, 0, 9),
        0x0CDC: 0,
        0x0CE0: i_type(0x23, 29, 31, 0x0C),
        0x0CE4: branch(4, 0, 0, 0x0CE4, 0x0B28),
        0x0CE8: 0,
        0x0CEC: 0,
    }
    for va, word in installer.items():
        write_word(va, word)

    # One dynamic early hook. For slow-path calls only, prefill 0x28(sp) with
    # the original packed state so non-target traffic remains stock-equivalent.
    # Target Practice/Gold calls branch to C00, which sets corrected t3 and
    # overwrites scratch only on the slow path. Gold X is shifted only on that
    # same slow path, exactly matching the accepted two-stage behavior.
    for va in range(0x0E08, 0x0EB0, 4):
        write_word(va, 0)

    RET = 0x0EA4
    hook = {
        0x0E08: i_type(0x25, 22, 11, 0x2C8),            # stock lhu t3,0x2c8(s6)
        0x0E0C: i_type(9, 0, 2, 100),
        0x0E10: branch(4, 9, 2, 0x0E10, 0x0E1C),        # fast path: scratch unused
        0x0E14: i_type(0x23, 22, 3, 0x2C8),             # delay: original packed state
        0x0E18: i_type(0x2B, 29, 3, 0x28),              # slow path scratch prefill
        0x0E1C: i_type(0x23, 29, 2, 0xA4),              # saved owner return
        0x0E20: i_type(0x0F, 0, 3, 0x0897),
        0x0E24: i_type(0x0D, 3, 3, 0x3C84),
        0x0E28: branch(5, 2, 3, 0x0E28, RET),
        0x0E2C: i_type(0x23, 29, 2, 0x54),
        0x0E30: i_type(9, 0, 3, 1),
        0x0E34: branch(5, 2, 3, 0x0E34, RET),
        0x0E38: i_type(9, 0, 2, 100),
        0x0E3C: branch(5, 11, 2, 0x0E3C, RET),
        0x0E40: i_type(0x23, 29, 8, 0x5C),              # authored Y
        0x0E44: i_type(0x23, 29, 3, 0x58),              # authored X
        0x0E48: i_type(9, 8, 2, -104),
        0x0E4C: i_type(0x0B, 2, 2, 36),
        0x0E50: branch(5, 2, 0, 0x0E50, 0x0E90),        # Practice row
        0x0E54: i_type(9, 0, 2, 25),
        0x0E58: branch(4, 8, 2, 0x0E58, 0x0E7C),        # Gold REWARD
        0x0E5C: i_type(9, 0, 2, 73),
        0x0E60: branch(5, 8, 2, 0x0E60, RET),
        0x0E64: 0,
        0x0E68: i_type(0x0B, 3, 2, 128),
        0x0E6C: branch(5, 2, 0, 0x0E6C, RET),
        0x0E70: i_type(9, 0, 8, 1),                     # Gold flag
        0x0E74: branch(4, 0, 0, 0x0E74, 0x0C00),
        0x0E78: 0,
        0x0E7C: i_type(9, 3, 2, -270),
        0x0E80: i_type(0x0B, 2, 2, 110),
        0x0E84: branch(4, 2, 0, 0x0E84, RET),
        0x0E88: i_type(9, 0, 8, 1),                     # Gold flag
        0x0E8C: branch(4, 0, 0, 0x0E8C, 0x0C00),
        0x0E90: i_type(0x0B, 3, 2, 200),                # safe delay + Practice check
        0x0E94: branch(4, 2, 0, 0x0E94, RET),
        0x0E98: r_type(0, 0, 8, 0, 0x21),               # Practice flag = 0
        0x0E9C: branch(4, 0, 0, 0x0E9C, 0x0C00),
        0x0EA0: 0,
        0x0EA4: j_type(2, 0x08970A98),
        0x0EA8: 0,
        0x0EAC: 0,
    }
    for va, word in hook.items():
        write_word(va, word)

    # Do not consume the previously audited capacity in this state-equivalence test.
    for start, end, name in (
        (0x0AC4, 0x0AF8, "52-byte hard-free table tail"),
        (0x0D40, 0x0D58, "24-byte unreachable glow block"),
        (0x03F0, 0x03F8, "startup-only HP NOP slots"),
    ):
        a = TEXT_FILE_OFFSET + start
        b = TEXT_FILE_OFFSET + end
        if data[a:b] != prx[a:b]:
            raise RuntimeError(f"EXP3A unexpectedly consumed {name}")

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
        raise RuntimeError("OPT-EXP3A output hash mismatch")
    return result

def build_base(root: Path) -> bytes:
    release = exp1.read_release_prx(root)
    s2 = exp2s2.patch_exp2s2(release)
    return exp2s3.patch(s2)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP3A-OneHookScratch.prx"))
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    base = build_base(root)
    if hashlib.sha256(base).hexdigest() != BASE_SHA256:
        raise RuntimeError("generated accepted base does not match OPT-EXP2S3")

    output = patch_exp3a(base)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")
    print("Dynamic Practice/Gold hooks: 2 -> 1")
    print("Previously audited free/dead regions remain untouched")

if __name__ == "__main__":
    main()
