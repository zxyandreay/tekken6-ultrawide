#!/usr/bin/env python3
"""Build OPT-EXP3D later-slot winner-glow diagnostics from EXP3C-A.

Historical audit:
- RoundWin v7 captured only P1/P2 first wins.
- Its winner-glow X gate admits only the first stock center family per side.
- The ordinary late earned-orb rectangle family is wider:
    P1 authored X 150..206
    P2 authored X 273..310
- EXP3C repaired the compact 64x64 UV identity, so X generalization can now be
  tested against the correct rotating quad instead of the wrong related layer.

Candidate A widens the X ownership gate to the full known round-marker family,
with small float/rotation margin.

Candidate B removes only the X gate while retaining:
- a3 == 4
- exact 64x64 packed UV sequence
- winner-row Y gate
- dynamic AutoHUD CENTER transform
- source save/restore
- original converter

No GitHub Actions are used or required.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

BASE_SHA256 = "6a2954bf2fa768d63d66c61e7770c22303a05dce2569f24f363b425552ec972c"
SLOTRANGE_SHA256 = "7a12f929dbf7f6b0c0d5bb87222164469ed5228f3d65db908a55b265775b83a4"
UVYONLY_SHA256 = "3501bafa786ce8cd96cf5a2a449b8c45424459f5cee1354c8144cf6e96ef8c34"

TEXT_FILE_OFFSET = 0x60

def write_word(data: bytearray, va: int, word: int) -> None:
    struct.pack_into("<I", data, TEXT_FILE_OFFSET + va, word & 0xFFFFFFFF)

def patch_slot_range(prx: bytes) -> bytes:
    if hashlib.sha256(prx).hexdigest() != BASE_SHA256:
        raise RuntimeError("EXP3C-A base hash mismatch")

    data = bytearray(prx)

    # Current EXP3C first-slot gate:
    # P1 high-half family 0x43c5..0x43c7
    # P2 high-half family 0x440b..0x440c
    #
    # Broaden to the whole known late-round authored family.
    #
    # P1 rectangle x=150..206 -> center approximately x+8 -> x0+x3 around
    # 316..428. Include small rotation/float margin -> high16 0x439c..0x43d7.
    #
    # P2 rectangle x=273..310 -> center approximately x+8 -> x0+x3 around
    # 562..636. First captured glow was ~559, so use high16 0x440b..0x441f.
    write_word(data, 0x0D3C, 0x2509BC64) # addiu t1,t0,-0x439c
    write_word(data, 0x0D40, 0x2D29003C) # sltiu t1,t1,0x3c => 0x439c..0x43d7
    # 0xD44 branch remains: if P1 family -> Y check
    write_word(data, 0x0D48, 0x2509BBF5) # addiu t1,t0,-0x440b
    write_word(data, 0x0D4C, 0x2D290015) # sltiu t1,t1,0x15 => 0x440b..0x441f
    # 0xD50 reject remains.

    out = bytes(data)
    if hashlib.sha256(out).hexdigest() != SLOTRANGE_SHA256:
        raise RuntimeError("slot-range output hash mismatch")
    return out

def patch_uvy_only(prx: bytes) -> bytes:
    if hashlib.sha256(prx).hexdigest() != BASE_SHA256:
        raise RuntimeError("EXP3C-A base hash mismatch")

    data = bytearray(prx)
    # After exact 64x64 UV identity and X sum calculation, bypass only the
    # X-family check and continue to the existing winner-row Y gate.
    write_word(data, 0x0D3C, 0x10000006) # b 0xD58
    write_word(data, 0x0D40, 0x00000000)

    out = bytes(data)
    if hashlib.sha256(out).hexdigest() != UVYONLY_SHA256:
        raise RuntimeError("UV/Y-only output hash mismatch")
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--mode", choices=("slot-range", "uvy-only"), required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    base = args.base.read_bytes()
    if args.mode == "slot-range":
        out = patch_slot_range(base)
    else:
        out = patch_uvy_only(base)

    args.output.write_bytes(out)
    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(out).hexdigest()}")
    print("Mode:", args.mode)
    print("PT_LOAD/layout inherited unchanged from EXP3C-A")

if __name__ == "__main__":
    main()
