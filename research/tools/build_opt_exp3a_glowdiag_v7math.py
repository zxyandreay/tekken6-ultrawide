#!/usr/bin/env python3
"""Build EXP3A GlowDiag-V7Math.

Diagnostic purpose:
Use the current device-stable EXP3A build, but replace only the dynamic winner
glow scale/center load sequence with the exact fixed-20:9 math used by historical
RoundWin v7:

    x' = 0.8*x + 48

This does not change the glow callsite, predicate, source-save/restore, original
converter call, font optimization, HP path, slot table, or module layout.

If this diagnostic fixes the visible halo on a 20:9 device while normal EXP3A
does not, the later AutoHUD dynamic glow-parameter rewrite is causal.

No GitHub Actions are used or required.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

BASE_SHA256 = "46063c6097e3dfaa51aafd077e0e5c65f02487bdbe420f8884f2a292edf8cf1f"
OUT_SHA256 = "24f6b9e3b243728de0e6a04d7f9b3b1e75641d3156a8c1fe355f3a79b06b3a67"
TEXT_FILE_OFFSET = 0x60

def patch(prx: bytes) -> bytes:
    if hashlib.sha256(prx).hexdigest() != BASE_SHA256:
        raise RuntimeError("EXP3A base hash mismatch")
    data = bytearray(prx)

    expected = {
        0x0D84: 0xC5042304, # lwc1 f4,scale
        0x0D88: 0xC5062328, # lwc1 f6,center-span
        0x0D8C: 0x3C083F00, # lui t0,0x3f00 (0.5)
        0x0D90: 0x44881000, # mtc1 t0,f2
        0x0D94: 0x46023182, # mul.s f6,f6,f2
    }
    for va,wanted in expected.items():
        got=struct.unpack_from("<I",data,TEXT_FILE_OFFSET+va)[0]
        if got != wanted:
            raise RuntimeError(f"unexpected glow math word at {va:#x}: {got:#010x}")

    replacement = {
        0x0D84: 0x3C083F4C, # lui t0,0x3f4c
        0x0D88: 0x3508CCCD, # ori t0,t0,0xcccd => 0.8f
        0x0D8C: 0x44882000, # mtc1 t0,f4
        0x0D90: 0x3C084240, # lui t0,0x4240 => 48.0f
        0x0D94: 0x44883000, # mtc1 t0,f6
    }
    for va,word in replacement.items():
        struct.pack_into("<I",data,TEXT_FILE_OFFSET+va,word)

    # Preserve fixed resident layout.
    e_phoff=struct.unpack_from("<I",data,0x1C)[0]
    e_phentsize,e_phnum=struct.unpack_from("<HH",data,0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected ELF layout")
    ph=struct.unpack_from("<IIIIIIII",data,e_phoff)
    if (ph[0],ph[4],ph[5]) != (1,0x0EB0,0x0EB0):
        raise RuntimeError("resident layout changed")

    result=bytes(data)
    if hashlib.sha256(result).hexdigest() != OUT_SHA256:
        raise RuntimeError("GlowDiag-V7Math hash mismatch")
    return result

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=Path,required=True)
    ap.add_argument("--output",type=Path,default=Path("Tekken6Ultrawide-OPT-EXP3A-GlowDiag-V7Math.prx"))
    args=ap.parse_args()
    out=patch(args.base.read_bytes())
    args.output.write_bytes(out)
    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(out).hexdigest()}")
    print("Glow transform forced to historical v7 fixed 20:9: x' = 0.8*x + 48")
    print("PT_LOAD remains 0x0EB0")

if __name__=="__main__":
    main()
