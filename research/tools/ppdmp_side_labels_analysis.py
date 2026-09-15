#!/usr/bin/env python3
"""Inventory stable top-HUD THROUGH draws for Arcade/Story/Ghost label research."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from ppdmp_hud_diff import extract_draws, load_dump


def r3(value: float) -> float:
    return round(float(value), 3)


def summarize(draw) -> dict[str, object] | None:
    if not (draw.vertex_type & 0x800000) or not draw.decoded:
        return None

    xs = [float(v["position"][0]) for v in draw.decoded]
    ys = [float(v["position"][1]) for v in draw.decoded]
    if not all(math.isfinite(v) for v in xs + ys):
        return None

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if max_y < -30 or min_y > 100 or max_x < -100 or min_x > 580:
        return None

    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0 or width > 520 or height > 160:
        return None

    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    if center_x < 220:
        side = "left"
    elif center_x > 260:
        side = "right"
    else:
        side = "center"

    return {
        "ordinal": draw.ordinal,
        "command_index": draw.command_index,
        "primitive": draw.primitive,
        "count": draw.count,
        "vertex_type": f"0x{draw.vertex_type:06X}",
        "texture_sha256": draw.texture_hash,
        "clut_sha256": draw.clut_hash,
        "bbox": [r3(min_x), r3(min_y), r3(max_x), r3(max_y)],
        "center": [r3(center_x), r3(center_y)],
        "size": [r3(width), r3(height)],
        "side": side,
        "authored_x": list(draw.authored_x) if draw.authored_x else None,
    }


def load_mode(root: Path, mode: str) -> list[dict[str, object]]:
    reports: list[list[dict[str, object]]] = []
    for path in sorted(root.glob(f"{mode}-*.ppdmp")):
        dump = load_dump(path)
        rows = []
        for draw in extract_draws(dump):
            item = summarize(draw)
            if item is not None:
                rows.append(item)
        reports.append(rows)

    if not reports:
        return []

    # Keep stable records present with the same semantic geometry/texture in all
    # captures of the mode. This removes transient particles and one-frame noise.
    def key(item: dict[str, object]) -> tuple[object, ...]:
        return (
            item["primitive"], item["count"], item["vertex_type"],
            item["texture_sha256"], item["clut_sha256"],
            tuple(item["bbox"]), item["side"],
        )

    common = set(map(key, reports[0]))
    for rows in reports[1:]:
        common &= set(map(key, rows))

    first_by_key = {key(item): item for item in reports[0]}
    stable = [first_by_key[k] for k in common]
    stable.sort(key=lambda x: (x["side"], x["center"][1], x["center"][0], x["ordinal"]))
    return stable


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture_dir", type=Path)
    args = ap.parse_args()

    modes = {mode: load_mode(args.capture_dir, mode) for mode in ("arcade", "story", "ghost")}
    payload = {"schema": 1, "capture_dir": str(args.capture_dir), "modes": modes}
    out = args.capture_dir / "analysis.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    for mode, rows in modes.items():
        print(f"{mode.upper()}: {len(rows)} stable top-HUD THROUGH draws")
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            grouped[str(row["side"])].append(row)
        for side in ("left", "center", "right"):
            print(f"  {side}: {len(grouped[side])}")
            for row in grouped[side][:24]:
                tex = (row["texture_sha256"] or "none")[:12]
                print(
                    f"    #{row['ordinal']} bbox={row['bbox']} size={row['size']} "
                    f"vtype={row['vertex_type']} tex={tex}"
                )
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
