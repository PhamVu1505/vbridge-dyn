"""Trích polygon mặt cắt từ file DXF (auto-chain toàn modelspace).

Chiến lược (đã chốt với owner):

1. Gom mọi entity hình học trong modelspace thành các đoạn thẳng — `LINE` trực
   tiếp; `ARC`/`CIRCLE`/`ELLIPSE`/`SPLINE` flatten thành đoạn; `LWPOLYLINE`/
   `POLYLINE`/`INSERT` nổ ra qua `virtual_entities()`.
2. Quy đổi mọi tọa độ về **mét** theo header `$INSUNITS`.
3. Nối đoạn thành đồ thị rồi **prune nhánh hở** (đỉnh bậc ≤ 1) — tự loại đường
   kích thước, leader, text, mốc.
4. Phần còn lại là các vòng kín: vòng diện tích lớn nhất = **đường bao ngoài**,
   các vòng còn lại = **lỗ rỗng**.
5. Map `DXF(x, y) → tọa độ local mặt cắt (y, z)` (giữ nguyên thứ tự cặp — đúng
   convention OPOLY của Midas).

Phụ thuộc `ezdxf` (optional extra ``vbridge-dyn[sections]``).
"""

from __future__ import annotations

import importlib
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Point2D = tuple[float, float]
_Segment = tuple[Point2D, Point2D]


class DxfUnavailableError(RuntimeError):
    """`ezdxf` chưa được cài (cần extra ``vbridge-dyn[sections]``)."""


class DxfSectionError(ValueError):
    """Không trích được polygon mặt cắt hợp lệ từ DXF."""


@dataclass(frozen=True)
class SectionPolygon:
    """Kết quả trích từ DXF: đường bao ngoài + danh sách lỗ (tọa độ y-z, mét)."""

    outer_boundary: list[Point2D]
    holes: list[list[Point2D]] = field(default_factory=list)
    source: str = ""
    units: str = "m"


# $INSUNITS → hệ số quy đổi sang mét (0 = unitless → coi như mét).
_INSUNITS_TO_M: dict[int, float] = {
    0: 1.0,
    1: 0.0254,  # inch
    2: 0.3048,  # foot
    4: 0.001,  # mm
    5: 0.01,  # cm
    6: 1.0,  # m
    8: 2.54e-5,  # microinch
    13: 1e-9,  # nanometre
    14: 0.1,  # decimetre
}


def read_section_polygon(
    dxf_path: Path,
    *,
    layer: str | None = None,
    snap_tol: float = 1e-4,
    arc_angle_deg: float = 10.0,
    arc_sagitta_m: float = 0.005,
) -> SectionPolygon:
    """Đọc 1 file DXF → `SectionPolygon` (bao ngoài + lỗ, đơn vị mét).

    `layer` None = lấy mọi layer (auto-chain). `snap_tol` (mét) = dung sai gộp
    điểm trùng. `arc_angle_deg` = góc mỗi đoạn khi chia `ARC`/`CIRCLE` (mặc định
    10°, khớp Midas SPC). `arc_sagitta_m` = sai số dây cung khi flatten
    `ELLIPSE`/`SPLINE`.
    """
    ezdxf = _load_ezdxf()
    if not dxf_path.exists():
        msg = f"Không tìm thấy file DXF: {dxf_path}"
        raise DxfSectionError(msg)
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except (OSError, ezdxf.DXFError) as exc:
        msg = f"Không đọc được DXF '{dxf_path}': {exc}"
        raise DxfSectionError(msg) from exc

    scale = _unit_scale(doc)
    sagitta_dxf = arc_sagitta_m / scale if scale > 0 else arc_sagitta_m

    segments: list[_Segment] = []
    for entity in doc.modelspace():
        if layer is not None and getattr(entity.dxf, "layer", None) != layer:
            continue
        segments.extend(_entity_segments(entity, scale, sagitta_dxf, arc_angle_deg))

    if not segments:
        where = f"layer '{layer}'" if layer else "modelspace"
        msg = f"DXF '{dxf_path}': không có đoạn thẳng hình học nào trong {where}"
        raise DxfSectionError(msg)

    ndig = max(0, round(-math.log10(snap_tol))) if snap_tol > 0 else 6
    loops = _extract_closed_loops(segments, ndig)
    if not loops:
        msg = (
            f"DXF '{dxf_path}': không tìm thấy vòng kín nào sau khi prune nhánh hở. "
            "Kiểm tra mặt cắt có khép kín không, hoặc chỉ định layer."
        )
        raise DxfSectionError(msg)

    loops.sort(key=lambda loop: abs(_polygon_area(loop)), reverse=True)
    outer = loops[0]
    holes = loops[1:]
    return SectionPolygon(
        outer_boundary=outer,
        holes=holes,
        source=str(dxf_path),
    )


def _load_ezdxf() -> Any:
    try:
        return importlib.import_module("ezdxf")
    except ModuleNotFoundError as exc:
        msg = (
            "Cần cài optional dependency `vbridge-dyn[sections]` (ezdxf) "
            "để đọc mặt cắt từ DXF"
        )
        raise DxfUnavailableError(msg) from exc


def _unit_scale(doc: Any) -> float:
    insunits = int(doc.header.get("$INSUNITS", 0) or 0)
    return _INSUNITS_TO_M.get(insunits, 1.0)


def _entity_segments(
    entity: Any,
    scale: float,
    sagitta_dxf: float,
    arc_angle_deg: float,
) -> list[_Segment]:
    """Quy 1 entity DXF về list đoạn thẳng (tọa độ đã đổi sang mét)."""
    etype = entity.dxftype()
    try:
        if etype == "LINE":
            return [(_pt(entity.dxf.start, scale), _pt(entity.dxf.end, scale))]
        if etype == "ARC":
            return _chain(
                _arc_points(
                    entity.dxf.center,
                    entity.dxf.radius,
                    entity.dxf.start_angle,
                    entity.dxf.end_angle,
                    arc_angle_deg,
                    scale,
                )
            )
        if etype == "CIRCLE":
            return _chain(
                _arc_points(entity.dxf.center, entity.dxf.radius, 0.0, 360.0, arc_angle_deg, scale)
            )
        if etype in {"ELLIPSE", "SPLINE"}:
            return _chain([_pt(p, scale) for p in entity.flattening(sagitta_dxf)])
        if etype in {"LWPOLYLINE", "POLYLINE", "INSERT"}:
            segments: list[_Segment] = []
            for sub in entity.virtual_entities():
                segments.extend(_entity_segments(sub, scale, sagitta_dxf, arc_angle_deg))
            return segments
    except Exception:  # entity lỗi/không hỗ trợ → bỏ qua, không chặn cả file
        return []
    return []  # TEXT, MTEXT, DIMENSION, POINT, SOLID, HATCH, ... → bỏ qua


def _arc_points(
    center: Any,
    radius: float,
    start_deg: float,
    end_deg: float,
    angle_deg: float,
    scale: float,
) -> list[Point2D]:
    """Chia cung tròn thành đỉnh theo bước góc `angle_deg` (DXF: cung quay CCW)."""
    cx, cy, r = float(center.x), float(center.y), float(radius)
    sweep = (float(end_deg) - float(start_deg)) % 360.0
    if sweep <= 1e-9:
        sweep = 360.0
    n = max(1, math.ceil(sweep / angle_deg))
    points: list[Point2D] = []
    for k in range(n + 1):
        ang = math.radians(start_deg + sweep * k / n)
        points.append(
            (
                round((cx + r * math.cos(ang)) * scale, 9),
                round((cy + r * math.sin(ang)) * scale, 9),
            )
        )
    return points


def _pt(vec: Any, scale: float) -> Point2D:
    return (round(float(vec.x) * scale, 9), round(float(vec.y) * scale, 9))


def _chain(points: list[Point2D]) -> list[_Segment]:
    return [(points[i], points[i + 1]) for i in range(len(points) - 1)]


def _extract_closed_loops(segments: list[_Segment], ndig: int) -> list[list[Point2D]]:
    """Nối đoạn → prune nhánh hở → trả về danh sách vòng kín (ring mở, không lặp đỉnh đầu)."""
    adj: dict[Point2D, list[Point2D]] = defaultdict(list)
    for a, b in segments:
        pa = (round(a[0], ndig), round(a[1], ndig))
        pb = (round(b[0], ndig), round(b[1], ndig))
        if pa == pb:
            continue
        adj[pa].append(pb)
        adj[pb].append(pa)

    # Prune lặp: bỏ đỉnh bậc ≤ 1 (đầu tự do của dimension/leader/text).
    changed = True
    while changed:
        changed = False
        for vertex in [v for v, ns in adj.items() if 0 < len(ns) <= 1]:
            for neighbour in adj[vertex]:
                adj[neighbour] = [x for x in adj[neighbour] if x != vertex]
            adj[vertex] = []
            changed = True

    visited: set[frozenset[Point2D]] = set()
    loops: list[list[Point2D]] = []
    for start, neighbours in adj.items():
        for first in neighbours:
            edge = frozenset((start, first))
            if edge in visited or not adj[first]:
                continue
            loop = _walk_cycle(adj, visited, start, first)
            if loop is not None and len(loop) >= 3 and abs(_polygon_area(loop)) > 1e-9:
                loops.append(loop)
    return loops


def _walk_cycle(
    adj: dict[Point2D, list[Point2D]],
    visited: set[frozenset[Point2D]],
    start: Point2D,
    first: Point2D,
) -> list[Point2D] | None:
    visited.add(frozenset((start, first)))
    loop = [start]
    cur = first
    while cur != start:
        loop.append(cur)
        nxt = [w for w in adj[cur] if frozenset((cur, w)) not in visited]
        if not nxt:
            return None  # chuỗi cụt — không khép thành vòng
        chosen = nxt[0]
        visited.add(frozenset((cur, chosen)))
        cur = chosen
    return loop


def _polygon_area(points: list[Point2D]) -> float:
    total = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return total / 2.0
