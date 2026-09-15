#!/usr/bin/env python3
"""Expand multi-rectangle mode-HUD draws into individual glyph/sprite rectangles.

Works on captures produced by ppsspp_mode_hud_capture.mjs.  The first stable
frame of each phase is enough because the parent draws were already identified
by the first-stage analyzer.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from ppdmp_hud_diff import extract_draws, load_dump

PHASES = ("practice-idle", "practice-hit", "goldrush")


def r3(value: float) -> float:
    return round(float(value), 3)


def pair_rect(a: dict[str, object], b: dict[str, object]) -> dict[str, object] | None:
    pa = a.get("position")
    pb = b.get("position")
    if not isinstance(pa, list) or not isinstance(pb, list) or len(pa) < 2 or len(pb) < 2:
        return None
    x0, y0 = float(pa[0]), float(pa[1])
    x1, y1 = float(pb[0]), float(pb[1])
    if not all(math.isfinite(v) for v in (x0, y0, x1, y1)):
        return None
    left, right = min(x0, x1), max(x0, x1)
    top, bottom = min(y0, y1), max(y0, y1)
    width, height = right - left, bottom - top
    if width <= 0 or height <= 0 or width > 520 or height > 300:
        return None
    return {
        "bbox": [r3(left), r3(top), r3(right), r3(bottom)],
        "size": [r3(width), r3(height)],
        "center": [r3((left + right) / 2.0), r3((top + bottom) / 2.0)],
        "uv0": a.get("uv"),
        "uv1": b.get("uv"),
        "color0": a.get("color"),
        "color1": b.get("color"),
    }


def expand_phase(path: Path) -> list[dict[str, object]]:
    dump = load_dump(path)
    parents: list[dict[str, object]] = []
    for draw in extract_draws(dump):
        if draw.primitive != 6 or draw.count < 4 or not (draw.vertex_type & 0x800000):
            continue
        rects: list[dict[str, object]] = []
        for i in range(0, len(draw.decoded) - 1, 2):
            rect = pair_rect(draw.decoded[i], draw.decoded[i + 1])
            if rect is not None:
                rect["pair_index"] = i // 2
                rects.append(rect)
        # Keep parents that contain at least one HUD-area rectangle.  We retain
        # the full rect list for those parents so disconnected batches remain visible.
        hud_rects = [r for r in rects if r["bbox"][3] >= -20 and r["bbox"][1] <= 180]
        if not hud_rects:
            continue
        parents.append({
            "ordinal": draw.ordinal,
            "command_index": draw.command_index,
            "count": draw.count,
            "vertex_type": f"0x{draw.vertex_type:06X}",
            "texture_sha256": draw.texture_hash,
            "clut_sha256": draw.clut_hash,
            "rectangles": rects,
        })
    return parents


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture_dir", type=Path)
    args = ap.parse_args()

    payload: dict[str, object] = {"schema": 1, "capture_dir": str(args.capture_dir), "phases": {}}
    phases_out: dict[str, object] = payload["phases"]  # type: ignore[assignment]

    for phase in PHASES:
        files = sorted(args.capture_dir.glob(f"{phase}-*.ppdmp"))
        if not files:
            phases_out[phase] = []
            continue
        rows = expand_phase(files[0])
        phases_out[phase] = rows
        print(f"{phase.upper()}: {len(rows)} multi-rectangle THROUGH parents")
        for parent in rows:
            tex = (parent["texture_sha256"] or "none")[:12]
            rects = parent["rectangles"]
            print(f"  #{parent['ordinal']} count={parent['count']} vtype={parent['vertex_type']} tex={tex} rects={len(rects)}")
            for rect in rects:
                bbox = rect["bbox"]
                # Print the areas relevant to the current bugs: top/center timer,
                # Practice left stats, and Gold Rush right stats.
                if bbox[1] <= 160 and (bbox[0] <= 220 or bbox[2] >= 260):
                    print(f"    [{rect['pair_index']:02d}] bbox={bbox} size={rect['size']} uv0={rect['uv0']} uv1={rect['uv1']}")

    out = args.capture_dir / "glyph-analysis.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
