#!/usr/bin/env python3
"""Inspect PPSSPP v5/v6 GE frame dumps and compare HUD draw submissions.

This intentionally does not extract images.  It reports serialized GE state,
texture/CLUT hashes, decoded vertex positions, and draw-sequence differences.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

try:
    from compression import zstd  # Python 3.14+
except ImportError:  # pragma: no cover - compatibility path
    import zstandard as zstd  # type: ignore[no-redef]


COMMAND_NAMES = {
    0: "INIT", 1: "REGISTERS", 2: "VERTICES", 3: "INDICES", 4: "CLUT",
    5: "TRANSFERSRC", 6: "MEMSET", 7: "MEMCPYDEST", 8: "MEMCPYDATA",
    9: "DISPLAY", 10: "CLUTADDR", 11: "EDRAMTRANS",
    **{0x10 + i: f"TEXTURE{i}" for i in range(8)},
    **{0x18 + i: f"FRAMEBUF{i}" for i in range(8)},
}
PRIMITIVE_NAMES = {
    0: "points", 1: "lines", 2: "line_strip", 3: "triangles",
    4: "triangle_strip", 5: "triangle_fan", 6: "rectangles", 7: "keep_previous",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ge_float24(arg: int) -> float:
    return struct.unpack("<f", struct.pack("<I", (arg & 0xFFFFFF) << 8))[0]


@dataclass(frozen=True)
class Record:
    index: int
    type: int
    size: int
    ptr: int
    data: bytes

    @property
    def name(self) -> str:
        return COMMAND_NAMES.get(self.type, f"UNKNOWN_{self.type:02X}")


@dataclass
class Dump:
    path: Path
    version: int
    game_id: str
    records: list[Record]
    push_size: int


@dataclass
class VertexLayout:
    stride: int
    through: bool
    tc_type: int
    color_type: int
    position_type: int
    tc_offset: int | None
    color_offset: int | None
    position_offset: int


@dataclass
class Draw:
    ordinal: int
    command_index: int
    vertex_record_index: int
    texture_record_index: int | None
    clut_record_index: int | None
    primitive: int
    count: int
    vertex_type: int
    vertices: bytes
    decoded: list[dict[str, object]]
    texture_address: int | None
    texture_hash: str | None
    clut_address: int | None
    clut_hash: str | None
    world_matrix: list[float]
    authored_x: tuple[float, float] | None
    semantic_vertex_hash: str

    def sequence_key(self) -> tuple[object, ...]:
        return (
            self.primitive, self.count, self.vertex_type,
            self.texture_hash, self.clut_hash, self.semantic_vertex_hash,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "command_index": self.command_index,
            "vertex_record_index": self.vertex_record_index,
            "texture_record_index": self.texture_record_index,
            "clut_record_index": self.clut_record_index,
            "primitive": PRIMITIVE_NAMES.get(self.primitive, self.primitive),
            "vertex_count": self.count,
            "vertex_type": f"0x{self.vertex_type:06X}",
            "through": bool(self.vertex_type & 0x800000),
            "texture_address": f"0x{self.texture_address:08X}" if self.texture_address is not None else None,
            "texture_sha256": self.texture_hash,
            "clut_address": f"0x{self.clut_address:08X}" if self.clut_address is not None else None,
            "clut_sha256": self.clut_hash,
            "authored_x": list(self.authored_x) if self.authored_x else None,
            "vertices": self.decoded,
        }


def decompress_block(raw: bytes, offset: int, expected_size: int) -> tuple[bytes, int]:
    compressed_size, = struct.unpack_from("<I", raw, offset)
    offset += 4
    compressed = raw[offset:offset + compressed_size]
    if len(compressed) != compressed_size:
        raise ValueError("truncated compressed block")
    data = zstd.decompress(compressed)
    if len(data) != expected_size:
        raise ValueError(f"decompressed size {len(data)} != expected {expected_size}")
    return data, offset + compressed_size


def load_dump(path: Path) -> Dump:
    raw = path.read_bytes()
    if len(raw) < 32:
        raise ValueError(f"{path}: truncated header")
    magic, version, game_id_raw, _ = struct.unpack_from("<8sI9s3s", raw)
    if magic != b"PPSSPPGE":
        raise ValueError(f"{path}: not a PPSSPP GE dump")
    if version not in (5, 6):
        raise ValueError(f"{path}: only zstd frame-dump versions 5 and 6 are supported")
    command_count, push_size = struct.unpack_from("<II", raw, 24)
    command_data, offset = decompress_block(raw, 32, command_count * 9)
    push, offset = decompress_block(raw, offset, push_size)
    if offset != len(raw):
        raise ValueError(f"{path}: {len(raw) - offset} unexpected trailing bytes")
    records = []
    for i in range(command_count):
        typ, size, ptr = struct.unpack_from("<BII", command_data, i * 9)
        if ptr + size > len(push):
            raise ValueError(f"{path}: record {i} payload is out of range")
        records.append(Record(i, typ, size, ptr, push[ptr:ptr + size]))
    game_id = game_id_raw.split(b"\0", 1)[0].decode("ascii", "replace")
    return Dump(path, version, game_id, records, push_size)


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def vertex_layout(vtype: int) -> VertexLayout:
    tc = vtype & 3
    color = (vtype >> 2) & 7
    normal = (vtype >> 5) & 3
    position = (vtype >> 7) & 3
    weight = (vtype >> 9) & 3
    weight_count = ((vtype >> 14) & 7) + 1
    morph_count = ((vtype >> 18) & 7) + 1
    tc_size, tc_align = (0, 2, 4, 8), (1, 1, 2, 4)
    color_size, color_align = (0, 0, 0, 0, 2, 2, 2, 4), (1, 1, 1, 1, 2, 2, 2, 4)
    normal_size, normal_align = (0, 3, 6, 12), (1, 1, 2, 4)
    position_size, position_align = (3, 3, 6, 12), (1, 1, 2, 4)
    weight_size, weight_align = (0, 1, 2, 4), (1, 1, 2, 4)
    size, biggest = 0, 1
    if weight:
        size += weight_size[weight] * weight_count
        biggest = max(biggest, weight_align[weight])
    tc_offset = None
    if tc:
        size = align(size, tc_align[tc]); tc_offset = size; size += tc_size[tc]
        biggest = max(biggest, tc_align[tc])
    color_offset = None
    if color:
        size = align(size, color_align[color]); color_offset = size; size += color_size[color]
        biggest = max(biggest, color_align[color])
    if normal:
        size = align(size, normal_align[normal]); size += normal_size[normal]
        biggest = max(biggest, normal_align[normal])
    size = align(size, position_align[position])
    position_offset = size
    size += position_size[position]
    biggest = max(biggest, position_align[position])
    stride = align(size, biggest) * morph_count
    return VertexLayout(stride, bool(vtype & 0x800000), tc, color, position,
                        tc_offset, color_offset, position_offset)


def decode_vertices(data: bytes, vtype: int, count: int) -> tuple[list[dict[str, object]], str]:
    layout = vertex_layout(vtype)
    if len(data) < layout.stride * count:
        raise ValueError("vertex payload is smaller than GE primitive vertex count")
    decoded: list[dict[str, object]] = []
    for i in range(count):
        base = i * layout.stride
        item: dict[str, object] = {}
        if layout.tc_offset is not None:
            off = base + layout.tc_offset
            if layout.tc_type == 1: item["uv"] = list(struct.unpack_from("<BB", data, off))
            elif layout.tc_type == 2: item["uv"] = list(struct.unpack_from("<HH", data, off))
            else: item["uv"] = list(struct.unpack_from("<ff", data, off))
        if layout.color_offset is not None:
            off = base + layout.color_offset
            size = 4 if layout.color_type == 7 else 2
            item["color"] = f"0x{int.from_bytes(data[off:off + size], 'little'):0{size * 2}X}"
        off = base + layout.position_offset
        if layout.position_type == 1:
            raw_pos = struct.unpack_from("<bbb", data, off)
            position = [float(v) if layout.through else v / 127.0 for v in raw_pos]
        elif layout.position_type == 2:
            x, y, z = struct.unpack_from("<hhH", data, off)
            raw_pos = (x, y, z)
            position = [float(x), float(y), float(z)] if layout.through else [x / 32767.0, y / 32767.0, z / 65535.0]
        else:
            raw_pos = struct.unpack_from("<fff", data, off)
            position = list(raw_pos)
        item["raw_position"] = list(raw_pos)
        item["position"] = position
        decoded.append(item)
    semantic_hash = sha256(json.dumps(decoded, sort_keys=True, separators=(",", ":")).encode())
    return decoded, semantic_hash


def texture_address(registers: list[int], level: int = 0) -> int | None:
    low = registers[0xA0 + level] & 0xFFFFFF
    high = (registers[0xA8 + level] & 0xFF0000) << 8
    address = low | high
    return address or None


def clut_address(registers: list[int]) -> int | None:
    address = (registers[0xB0] & 0xFFFFFF) | ((registers[0xB1] & 0xFF0000) << 8)
    return address or None


def extract_draws(dump: Dump) -> list[Draw]:
    registers = [0] * 256
    world = [0.0] * 12
    world_index = 0
    latest_vertices = b""
    latest_vertex_index = -1
    latest_texture_hash: str | None = None
    latest_texture_index: int | None = None
    latest_clut_hash: str | None = None
    latest_clut_index: int | None = None
    draws: list[Draw] = []
    for record in dump.records:
        if record.type == 2:
            latest_vertices = record.data
            latest_vertex_index = record.index
        elif record.type in range(0x10, 0x18):
            if record.type == 0x10:
                latest_texture_hash = sha256(record.data)
                latest_texture_index = record.index
        elif record.type in range(0x18, 0x20):
            if record.type == 0x18:
                latest_texture_hash = sha256(record.data)
                latest_texture_index = record.index
        elif record.type == 4:
            latest_clut_hash = sha256(record.data)
            latest_clut_index = record.index
        elif record.type == 1:
            for op, in struct.iter_unpack("<I", record.data):
                command, arg = op >> 24, op & 0xFFFFFF
                if command == 0x3A:
                    world_index = arg & 0xF
                elif command == 0x3B:
                    if world_index < 12:
                        world[world_index] = ge_float24(arg)
                    world_index = (world_index + 1) & 0xF
                registers[command] = op
                if command != 0x04:
                    continue
                primitive, count = (arg >> 16) & 7, arg & 0xFFFF
                vtype = registers[0x12] & 0xFFFFFF
                decoded, semantic_hash = decode_vertices(latest_vertices, vtype, count)
                xs = []
                for vertex in decoded:
                    x, y, z = vertex["position"]  # type: ignore[misc]
                    if vtype & 0x800000:
                        xs.append(float(x))
                    else:
                        xs.append(x * world[0] + y * world[3] + z * world[6] + world[9])
                draws.append(Draw(
                    len(draws), record.index, latest_vertex_index, latest_texture_index,
                    latest_clut_index, primitive, count, vtype, latest_vertices,
                    decoded, texture_address(registers), latest_texture_hash,
                    clut_address(registers), latest_clut_hash, list(world),
                    (min(xs), max(xs)) if xs else None, semantic_hash,
                ))
    return draws


def print_dump_summary(dump: Dump) -> None:
    counts: dict[str, int] = {}
    for record in dump.records:
        counts[record.name] = counts.get(record.name, 0) + 1
    print(json.dumps({
        "file": dump.path.name, "version": dump.version, "game_id": dump.game_id,
        "record_count": len(dump.records), "push_buffer_size": dump.push_size,
        "records_by_type": counts, "draw_count": len(extract_draws(dump)),
    }, indent=2))


def print_draws(dump: Dump, first: int, last: int) -> None:
    draws = extract_draws(dump)
    selected = [draw.as_dict() for draw in draws if first <= draw.ordinal <= last]
    print(json.dumps(selected, indent=2))


def print_diff(a: Dump, b: Dump) -> None:
    a_draws, b_draws = extract_draws(a), extract_draws(b)
    matcher = difflib.SequenceMatcher(
        None, [d.sequence_key() for d in a_draws], [d.sequence_key() for d in b_draws],
        autojunk=False,
    )
    differences = []
    for tag, a0, a1, b0, b1 in matcher.get_opcodes():
        if tag != "equal":
            differences.append({
                "operation": tag, "a_draw_range": [a0, a1 - 1], "b_draw_range": [b0, b1 - 1],
                "a_command_range": [a_draws[a0].command_index, a_draws[a1 - 1].command_index] if a0 < a1 else None,
                "b_command_range": [b_draws[b0].command_index, b_draws[b1 - 1].command_index] if b0 < b1 else None,
            })
    matrix_changes = []
    if len(a.records) == len(b.records):
        for left, right in zip(a.records, b.records):
            if left.type != right.type or left.type != 1 or left.size != right.size:
                continue
            for word_index, ((x,), (y,)) in enumerate(zip(struct.iter_unpack("<I", left.data), struct.iter_unpack("<I", right.data))):
                if x != y and x >> 24 == y >> 24 == 0x3B:
                    matrix_changes.append({
                        "command_index": left.index, "word_index": word_index,
                        "from": ge_float24(x), "to": ge_float24(y), "delta": ge_float24(y) - ge_float24(x),
                    })
    print(json.dumps({
        "a": a.path.name, "b": b.path.name,
        "draw_counts": [len(a_draws), len(b_draws)],
        "draw_sequence_differences": differences,
        "world_matrix_data_changes": matrix_changes,
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    summary = sub.add_parser("summary")
    summary.add_argument("dump", type=Path)
    draws = sub.add_parser("draws")
    draws.add_argument("dump", type=Path)
    draws.add_argument("--first", type=int, required=True)
    draws.add_argument("--last", type=int, required=True)
    diff = sub.add_parser("diff")
    diff.add_argument("a", type=Path)
    diff.add_argument("b", type=Path)
    args = parser.parse_args()
    if args.command == "summary": print_dump_summary(load_dump(args.dump))
    elif args.command == "draws": print_draws(load_dump(args.dump), args.first, args.last)
    else: print_diff(load_dump(args.a), load_dump(args.b))


if __name__ == "__main__":
    main()
