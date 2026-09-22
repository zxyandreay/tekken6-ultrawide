#!/usr/bin/env python3
"""Build OPT-EXP2S2: corrected safe installer compression.

OPT-EXP2S correctly compressed the 13 slot patch records from 12 bytes to 8 bytes,
but missed the third table walk used to invalidate instruction-cache lines after
installing the hooks. That loop still advanced by 12 bytes while the new table end
was start+0x68, so it could never reach the end and spun forever at startup.

OPT-EXP2S2 is exactly OPT-EXP2S plus:
    module+0x0414: addiu s0,s0,12 -> addiu s0,s0,8

Battle-time HUD code remains byte-identical to validated OPT-EXP1.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

import build_opt_exp2s as exp2s

TEXT_FILE_OFFSET = exp2s.TEXT_FILE_OFFSET
OPT_EXP2S_SHA256 = "a43777202277145acc28fa7d4a41848e7be63413fd43210c8ad8dee8455737ad"
OPT_EXP2S2_SHA256 = "1a23770194fe66f753554a1981d55d64e266f398f4f44b156ffa9385529a4409"

def patch_exp2s2(prx: bytes) -> bytes:
    data = bytearray(exp2s.patch_exp2s(prx))
    if hashlib.sha256(data).hexdigest() != OPT_EXP2S_SHA256:
        raise RuntimeError("OPT-EXP2S base hash mismatch")

    old = struct.unpack_from("<I", data, TEXT_FILE_OFFSET + 0x414)[0]
    if old != 0x2610000C:
        raise RuntimeError(f"unexpected cache-flush stride word: {old:#010x}")

    # Third slot-table walk: cache invalidation.
    # Compressed records are 8 bytes, so advance by 8 rather than 12.
    struct.pack_into("<I", data, TEXT_FILE_OFFSET + 0x414, 0x26100008)

    # Verify the three compressed table walkers now use the same 8-byte stride.
    checks = {
        0x2A0: 0x24420008,  # validation loop
        0x3C4: 0x24A50008,  # installation loop
        0x414: 0x26100008,  # cache invalidation loop
    }
    for va, wanted in checks.items():
        got = struct.unpack_from("<I", data, TEXT_FILE_OFFSET + va)[0]
        if got != wanted:
            raise RuntimeError(f"stride mismatch at {va:#x}: {got:#010x}")

    # Table start/end relationship: 13 * 8 = 0x68.
    start_word = struct.unpack_from("<I", data, TEXT_FILE_OFFSET + 0x280)[0]
    if start_word != 0x26110068:
        raise RuntimeError("compressed table end is not +0x68")

    # Resident layout stays fixed.
    e_phoff = struct.unpack_from("<I", data, 0x1C)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    if e_phentsize != 32 or e_phnum != 1:
        raise RuntimeError("unexpected program-header layout")
    ph = struct.unpack_from("<IIIIIIII", data, e_phoff)
    if (ph[0], ph[4], ph[5]) != (1, 0x0EB0, 0x0EB0):
        raise RuntimeError("resident layout changed")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OPT_EXP2S2_SHA256:
        raise RuntimeError("OPT-EXP2S2 output hash mismatch")
    return result

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP2S2.prx"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    output = patch_exp2s2(exp2s.exp1.read_release_prx(root))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("PT_LOAD p_filesz=p_memsz=0x0EB0")
    print("All three slot-table walks use 8-byte stride")
    print("Runtime HUD code remains OPT-EXP1-equivalent")
    print("Reclaimed contiguous table capacity: 52 bytes")

if __name__ == "__main__":
    main()
