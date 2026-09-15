#!/usr/bin/env python3
"""Analyze Tekken 6 round-win HUD phases from PPSSPP frame dumps.

The analyzer inventories top-HUD THROUGH draws across pre-KO, immediate
round-win, and stable next-round phases without preselecting a known texture.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from ppdmp_hud_diff import extract_draws, load_dump


def r3(v: float) -> float:
    return round(float(v), 3)


def identity(draw) -> str:
    payload = {
        "primitive": draw.primitive,
        "count": draw.count,
        "vertex_type": draw.vertex_type,
        "texture": draw.texture_hash,
        "clut": draw.clut_hash,
        "uv": [v.get("uv") for v in draw.decoded],
        "colors": [v.get("color") for v in draw.decoded],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def summarize_draw(draw) -> dict[str, object] | None:
    if not (draw.vertex_type & 0x800000) or not draw.decoded:
        return None

    xs = [float(v["position"][0]) for v in draw.decoded]
    ys = [float(v["position"][1]) for v in draw.decoded]
    if not all(math.isfinite(v) for v in xs + ys):
        return None

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if max_y < -80 or min_y > 140 or max_x < -160 or min_x > 640:
        return None

    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0 or width > 500 or height > 260:
        return None

    axis_aligned = (
        len({round(v, 3) for v in xs}) <= 2
        and len({round(v, 3) for v in ys}) <= 2
    )
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    orb_sized = (
        8.0 <= width <= 22.0
        and 12.0 <= height <= 22.0
        and 20.0 <= center_y <= 45.0
    )

    return {
        "ordinal": draw.ordinal,
        "command_index": draw.command_index,
        "primitive": draw.primitive,
        "count": draw.count,
        "vertex_type": f"0x{draw.vertex_type:06X}",
        "texture_sha256": draw.texture_hash,
        "clut_sha256": draw.clut_hash,
        "identity": identity(draw),
        "bbox": [r3(min_x), r3(min_y), r3(max_x), r3(max_y)],
        "center": [r3(center_x), r3(center_y)],
        "size": [r3(width), r3(height)],
        "axis_aligned": axis_aligned,
        "rotated_or_skewed": not axis_aligned,
        "orb_sized": orb_sized,
        "vertices": draw.decoded,
    }


def analyze_file(path: Path) -> dict[str, object]:
    dump = load_dump(path)
    candidates = []
    for draw in extract_draws(dump):
        item = summarize_draw(draw)
        if item is not None:
            candidates.append(item)
    return {
        "file": path.name,
        "game_id": dump.game_id,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def phase_files(root: Path, phase: str) -> list[Path]:
    return sorted(root.glob(f"{phase}-*.ppdmp"))


def compact_item(item: dict[str, object]) -> dict[str, object]:
    return {
        "file": item["file"],
        "ordinal": item["ordinal"],
        "texture_sha256": item["texture_sha256"],
        "clut_sha256": item["clut_sha256"],
        "vertex_type": item["vertex_type"],
        "primitive": item["primitive"],
        "count": item["count"],
        "bbox": item["bbox"],
        "center": item["center"],
        "size": item["size"],
        "axis_aligned": item["axis_aligned"],
        "rotated_or_skewed": item["rotated_or_skewed"],
        "orb_sized": item["orb_sized"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture_dir", type=Path)
    ap.add_argument("--side", choices=("p1", "p2"), required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    phases: dict[str, list[dict[str, object]]] = {}
    flat: dict[str, list[dict[str, object]]] = {}
    for phase in ("pre", "burst", "next"):
        reports = [analyze_file(p) for p in phase_files(args.capture_dir, phase)]
        phases[phase] = reports
        rows = []
        for report in reports:
            for candidate in report["candidates"]:
                rows.append({"file": report["file"], **candidate})
        flat[phase] = rows

    baseline_ids = {c["identity"] for c in flat["pre"]}
    burst_new = [c for c in flat["burst"] if c["identity"] not in baseline_ids]
    next_new = [c for c in flat["next"] if c["identity"] not in baseline_ids]

    groups: dict[str, dict[str, object]] = {}
    for phase, rows in flat.items():
        for candidate in rows:
            key = candidate["identity"]
            group = groups.setdefault(key, {
                "texture_sha256": candidate["texture_sha256"],
                "clut_sha256": candidate["clut_sha256"],
                "vertex_type": candidate["vertex_type"],
                "primitive": candidate["primitive"],
                "count": candidate["count"],
                "axis_aligned": candidate["axis_aligned"],
                "rotated_or_skewed": candidate["rotated_or_skewed"],
                "orb_sized": candidate["orb_sized"],
                "phases": {"pre": [], "burst": [], "next": []},
            })
            group["phases"][phase].append({
                "file": candidate["file"],
                "ordinal": candidate["ordinal"],
                "center": candidate["center"],
                "bbox": candidate["bbox"],
                "size": candidate["size"],
            })

    interesting = []
    for group in groups.values():
        if not group["phases"]["burst"]:
            continue
        if group["orb_sized"] or group["rotated_or_skewed"] or not group["phases"]["pre"]:
            interesting.append(group)

    payload = {
        "schema": 1,
        "side": args.side,
        "capture_dir": str(args.capture_dir),
        "counts": {phase: len(rows) for phase, rows in flat.items()},
        "burst_new_vs_pre_count": len(burst_new),
        "next_new_vs_pre_count": len(next_new),
        "burst_new_vs_pre": [compact_item(c) for c in burst_new],
        "next_new_vs_pre": [compact_item(c) for c in next_new],
        "interesting_identities": interesting,
        "phases": phases,
    }

    out = args.capture_dir / "analysis.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
        return

    print(f"Side: {args.side.upper()}")
    print(
        "Top-HUD THROUGH candidates: "
        f"pre={len(flat['pre'])}, burst={len(flat['burst'])}, next={len(flat['next'])}"
    )
    print(f"Burst identities not present pre-KO: {len(burst_new)}")
    print(f"Next-round identities not present pre-KO: {len(next_new)}")
    print(f"Interesting burst identities: {len(interesting)}")
    for i, group in enumerate(interesting[:20], 1):
        burst_centers = sorted({tuple(x["center"]) for x in group["phases"]["burst"]})
        next_centers = sorted({tuple(x["center"]) for x in group["phases"]["next"]})
        tag = "orb-sized" if group["orb_sized"] else (
            "rotated" if group["rotated_or_skewed"] else "new"
        )
        texture = (group["texture_sha256"] or "none")[:12]
        print(
            f"  #{i} {tag} tex={texture} "
            f"burst_centers={burst_centers[:8]} next_centers={next_centers[:8]}"
        )
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
