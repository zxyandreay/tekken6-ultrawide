#!/usr/bin/env python3
"""Audit accepted internal capacity in Tekken6Ultrawide optimization builds."""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

LOAD_FILE_OFFSET = 0x60
LOAD_SIZE = 0x0EB0

OFFICIAL_SHA = "311720e8aa115865343df4fcd13fa5e9f8f074ff1e05348ab165e9c6ef81ee75"
EXP2S3_SHA = "7496824d8b6827ecb39589d37f966cf638cf9232058f6f8dc2a2f1db355a3805"

def u32(data: bytes, va: int) -> int:
    return struct.unpack_from("<I", data, LOAD_FILE_OFFSET + va)[0]

def check_layout(data: bytes) -> None:
    phoff = struct.unpack_from("<I", data, 0x1C)[0]
    phentsize, phnum = struct.unpack_from("<HH", data, 0x2A)
    if phentsize != 32 or phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, phoff)
    if ph[0] != 1 or ph[1] != LOAD_FILE_OFFSET or ph[4] != LOAD_SIZE or ph[5] != LOAD_SIZE:
        raise RuntimeError("PT_LOAD invariant failed")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("official", type=Path)
    ap.add_argument("accepted", type=Path)
    args = ap.parse_args()

    official = args.official.read_bytes()
    accepted = args.accepted.read_bytes()

    if hashlib.sha256(official).hexdigest() != OFFICIAL_SHA:
        raise RuntimeError("official v1.2.0 hash mismatch")
    if hashlib.sha256(accepted).hexdigest() != EXP2S3_SHA:
        raise RuntimeError("OPT-EXP2S3 hash mismatch")

    check_layout(official)
    check_layout(accepted)

    # A: physically zero table tail.
    table = accepted[LOAD_FILE_OFFSET + 0x0AC4:LOAD_FILE_OFFSET + 0x0AF8]
    if len(table) != 52 or any(table):
        raise RuntimeError("52-byte table tail is not fully zero")

    # B: generalized glow branches over the old X gate.
    if u32(accepted, 0x0D3C) != 0x10000006:
        raise RuntimeError("winner-glow bypass branch mismatch")
    if u32(accepted, 0x0D40) != 0:
        raise RuntimeError("winner-glow branch delay slot mismatch")

    # C: removed upstream HP installer writes.
    if u32(accepted, 0x03F0) != 0 or u32(accepted, 0x03F4) != 0:
        raise RuntimeError("upstream HP installer slots are not NOP")

    print("official:", OFFICIAL_SHA)
    print("accepted:", EXP2S3_SHA)
    print("PT_LOAD: one segment, p_filesz=p_memsz=0x0EB0")
    print()
    print("General reusable capacity:")
    print("  0x0AC4..0x0AF7  hard-free table tail       52 bytes")
    print("  0x0D40..0x0D57  dead glow X classifier     24 bytes")
    print("                                             --------")
    print("                                             76 bytes")
    print()
    print("Startup-only instruction slots:")
    print("  0x03F0..0x03F7  removed HP hook installs     8 bytes")
    print()
    print("Total opportunity with context restrictions: 84 bytes")
    print("Resident allocation reduction: 0 bytes")

if __name__ == "__main__":
    main()
