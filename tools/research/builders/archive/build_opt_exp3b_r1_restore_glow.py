#!/usr/bin/env python3
"""Build OPT-EXP3B-R1 by restoring the winner-glow block in EXP3B.

Purpose
-------
Strict A/B isolate for the EXP3B round-win halo regression.

EXP3B changed only:
- relocation of the validated 52-byte OneHookScratch helper;
- three branch retargets;
- zeroing the old 64-byte helper allocation;
- zeroing the old winner-glow X-classifier block.

EXP3B-R1 keeps the helper relocation/64-byte compaction intact and restores
0x0D40..0x0D57 exactly to the device-validated EXP3A bytes.

If device behavior returns to normal, the glow block was not safely reclaimable
despite the static direct-xref audit.

No GitHub Actions are used or required.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

BASE_SHA256 = "fa41e928aeecba2e2a2bd9d537e38d2dca96499ad084166de6ea854ad9e1bce8"
EXP3A_SHA256 = "46063c6097e3dfaa51aafd077e0e5c65f02487bdbe420f8884f2a292edf8cf1f"
OUT_SHA256 = "d4f48aeb3e15fb476826dd545d078a28e071430e199917626fa0756d4a7845ae"

TEXT_FILE_OFFSET = 0x60

def patch(base: bytes, exp3a: bytes) -> bytes:
    if hashlib.sha256(base).hexdigest() != BASE_SHA256:
        raise RuntimeError("EXP3B base hash mismatch")
    if hashlib.sha256(exp3a).hexdigest() != EXP3A_SHA256:
        raise RuntimeError("EXP3A reference hash mismatch")

    data = bytearray(base)

    # Restore the entire historically validated winner-glow sub-block exactly.
    start = TEXT_FILE_OFFSET + 0x0D40
    end = TEXT_FILE_OFFSET + 0x0D58
    data[start:end] = exp3a[start:end]

    # Keep the 64-byte old helper allocation physically zero.
    if any(data[TEXT_FILE_OFFSET + 0x0C00:TEXT_FILE_OFFSET + 0x0C40]):
        raise RuntimeError("old helper region unexpectedly nonzero")

    result = bytes(data)
    if hashlib.sha256(result).hexdigest() != OUT_SHA256:
        raise RuntimeError("EXP3B-R1 output hash mismatch")
    return result

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--exp3a", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("Tekken6Ultrawide-OPT-EXP3B-R1-RestoreGlow.prx"))
    args = ap.parse_args()

    output = patch(args.base.read_bytes(), args.exp3a.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)

    print(f"Wrote {args.output}")
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")
    print(f"Size {len(output)} bytes")
    print("Hard-free candidate retained: 64 bytes at 0x0C00..0x0C3F")
    print("Winner-glow block restored exactly from accepted EXP3A")

if __name__ == "__main__":
    main()
