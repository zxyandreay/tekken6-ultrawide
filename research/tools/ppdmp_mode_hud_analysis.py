#!/usr/bin/env python3
"""Inventory stable Practice and Gold Rush HUD draws for mode-specific ultrawide fixes."""

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
    if max_y < -40 or min_y > 300 or max_x < -160 or min_x > 640:
        return None

    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0 or width > 680 or height > 340:
        return None

    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    if center_x < 210:
        side = "left"
    elif center_x > 270:
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


def key(item: dict[str, object]) -> tuple[object, ...]:
    return (
        item["primitive"], item["count"], item["vertex_type"],
        item["texture_sha256"], item["clut_sha256"],
        tuple(item["bbox"]), item["side"],
    )


def loose_key(item: dict[str, object]) -> tuple[object, ...]:
    return (
        item["primitive"], item["count"], item["vertex_type"],
        item["texture_sha256"], item["clut_sha256"], tuple(item["size"]),
    )


def load_phase(root: Path, phase: str) -> list[dict[str, object]]:
    reports: list[list[dict[str, object]]] = []
    for path in sorted(root.glob(f"{phase}-*.ppdmp")):
        rows = []
        for draw in extract_draws(load_dump(path)):
            item = summarize(draw)
            if item is not None:
                rows.append(item)
        reports.append(rows)

    if not reports:
        return []

    common = set(map(key, reports[0]))
    for rows in reports[1:]:
        common &= set(map(key, rows))

    first_by_key = {key(item): item for item in reports[0]}
    stable = [first_by_key[k] for k in common]
    stable.sort(key=lambda x: (x["side"], x["center"][1], x["center"][0], x["ordinal"]))
    return stable


def existing_baseline_keys(root: Path) -> set[tuple[object, ...]]:
    side_report = root.parent / "side-labels" / "analysis.json"
    if not side_report.exists():
        return set()
    try:
        payload = json.loads(side_report.read_text(encoding="utf-8"))
    except Exception:
        return set()
    result: set[tuple[object, ...]] = set()
    for rows in payload.get("modes", {}).values():
        for item in rows:
            result.add(loose_key(item))
    return result


def candidate_tags(phase: str, row: dict[str, object]) -> list[str]:
    x0, y0, x1, y1 = map(float, row["bbox"])
    cx, cy = map(float, row["center"])
    tags: list[str] = []

    if phase.startswith("practice"):
        if 150 <= cx <= 330 and -10 <= y0 <= 90:
            tags.append("practice-center")
        if cx < 220 and 20 <= cy <= 210:
            tags.append("practice-left")
        if phase == "practice-hit" and cy >= 30:
            tags.append("practice-hit-state")
    elif phase == "goldrush":
        if cx > 260 and -10 <= y0 <= 230:
            tags.append("goldrush-right")

    return tags


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture_dir", type=Path)
    args = ap.parse_args()

    phases = ("practice-idle", "practice-hit", "goldrush")
    baseline = existing_baseline_keys(args.capture_dir)
    result: dict[str, list[dict[str, object]]] = {}

    for phase in phases:
        rows = load_phase(args.capture_dir, phase)
        for row in rows:
            row["seen_in_normal_baseline"] = loose_key(row) in baseline
            row["candidate_tags"] = candidate_tags(phase, row)
        result[phase] = rows

    # Highlight geometry/resource records that appear or change only when the
    # Practice hit state is populated.
    idle_keys = {loose_key(row) for row in result["practice-idle"]}
    hit_keys = {loose_key(row) for row in result["practice-hit"]}
    practice_hit_only = [row for row in result["practice-hit"] if loose_key(row) not in idle_keys]
    practice_idle_only = [row for row in result["practice-idle"] if loose_key(row) not in hit_keys]

    payload = {
        "schema": 1,
        "capture_dir": str(args.capture_dir),
        "phases": result,
        "practice_hit_only": practice_hit_only,
        "practice_idle_only": practice_idle_only,
    }
    out = args.capture_dir / "analysis.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    for phase in phases:
        rows = result[phase]
        print(f"{phase.upper()}: {len(rows)} stable THROUGH draws")
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            grouped[str(row["side"])].append(row)
        for side in ("left", "center", "right"):
            candidates = [r for r in grouped[side] if r["candidate_tags"]]
            print(f"  {side}: {len(grouped[side])} stable, {len(candidates)} candidate")
            for row in candidates[:40]:
                tex = (row["texture_sha256"] or "none")[:12]
                baseline_mark = " normal" if row["seen_in_normal_baseline"] else " mode-only"
                tags = ",".join(row["candidate_tags"])
                print(
                    f"    #{row['ordinal']} bbox={row['bbox']} size={row['size']} "
                    f"vtype={row['vertex_type']} tex={tex} [{tags};{baseline_mark.strip()}]"
                )

    print(f"PRACTICE hit-only identities: {len(practice_hit_only)}")
    for row in practice_hit_only[:40]:
        tex = (row["texture_sha256"] or "none")[:12]
        print(
            f"  #{row['ordinal']} bbox={row['bbox']} size={row['size']} "
            f"side={row['side']} vtype={row['vertex_type']} tex={tex}"
        )
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
