#!/usr/bin/env python3
"""Verify the fixed hook addresses against a local ULUS10466 ELF payload."""

from __future__ import annotations

import struct
import sys
from pathlib import Path


SITES = [
    (0x08929854, 0x0E24B67E),
    (0x08929958, 0x0E24B67E),
    (0x089299E8, 0x0E24B67E),
    (0x08929DF0, 0x0E24B67E),
    (0x08929F3C, 0x0E24B67E),
    (0x0892A10C, 0x0E24B67E),
    (0x0892A170, 0x0E24B67E),
    (0x0892A1B4, 0x0E24B67E),
    (0x0892A1F0, 0x0E24B67E),
    (0x0892A268, 0x0E24B67E),
    (0x08929228, 0x0A24B67E),
    (0x089292F4, 0x0A24B67E),
    (0x08929D4C, 0x0A24B67E),
    (0x08AB9798, 0x0E2AE4E0),
    (0x08AB98AC, 0x0E2AE4E0),
    (0x0892C1F0, 0x0E24A3FD),
    (0x0892C26C, 0x0A24A3FD),
    (0x0892D56C, 0x0E2097AB),
    (0x0892D5B0, 0x0E2097AB),
    (0x08AC9C38, 0x0E2BA529),
]


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} ULUS10466_EBOOT.BIN", file=sys.stderr)
        return 2

    payload = Path(sys.argv[1]).read_bytes()
    phoff = struct.unpack_from("<I", payload, 28)[0]
    phentsize, phnum = struct.unpack_from("<HH", payload, 42)
    if phnum != 1 or phentsize < 32:
        raise SystemExit("expected the single-segment Tekken ELF layout")
    _ptype, file_offset, virtual_base, _vsize, _file_size, *_ = struct.unpack_from(
        "<IIIIIIII", payload, phoff
    )

    failures = 0
    for address, expected in SITES:
        offset = file_offset + address - virtual_base
        actual = struct.unpack_from("<I", payload, offset)[0]
        result = "OK" if actual == expected else "MISMATCH"
        print(f"0x{address:08X}: {actual:08X} {result}")
        failures += actual != expected
    return int(failures != 0)


if __name__ == "__main__":
    raise SystemExit(main())
