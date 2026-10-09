"""Read tendon profiles from a Midas-style DXF drawing.

The BXD convention is intentionally CAD-friendly:

- each tendon has one numeric layer, for example ``1001``;
- each layer contains one elevation curve and one plan curve;
- the drawing stores half of one girder, mirrored at the span mid-point;
- text on layer ``elem`` records the prototype beam numbering.

Coordinates are converted to metres from ``$INSUNITS`` and returned as Midas
local profile points ``(x, y, z)``.
"""

from __future__ import annotations

import importlib
import math
import re
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any

from vbridge_dyn.importers.dxf.section_reader import DxfSectionError, DxfUnavailableError

Point2D = tuple[float, float]
Point3D = tuple[float, float, float]

_INSUNITS_TO_M: dict[int, float] = {
    0: 1.0,
    1: 0.0254,
    2: 0.3048,
    4: 0.001,
    5: 0.01,
    6: 1.0,
    8: 2.54e-5,
    13: 1e-9,
    14: 0.1,
}


class DxfTendonError(DxfSectionError):
    """Cannot extract valid tendon profiles from DXF."""


@dataclass(frozen=True)
class TendonLayerProfile:
    """One tendon layer converted to Midas local coordinates."""

    layer: str
    points_3d: list[Point3D]
    elevation_points: list[Point2D]
    plan_points: list[Point2D]
    source: str = ""


@dataclass(frozen=True)
class TendonDxfData:
    """All tendon profiles found in a DXF file."""

    profiles: list[TendonLayerProfile]
    prototype_element_ids: list[int] = field(default_factory=list)
    section_reference: Point2D | None = None
    mirror_x: float = 0.0
    plan_center_y: float = 0.0
    elevation_top_y: float = 0.0
    source: str = ""
    units: str = "m"


@dataclass(frozen=True)
class _LayerEntity:
    layer: str
    points: list[Point2D]
    entity_type: str

    @property
    def centroid_y(self) -> float:
        return sum(point[1] for point in self.points) / len(self.points)

    @property
    def min_x(self) -> float:
        return min(point[0] for point in self.points)

    @property
    def max_x(self) -> float:
        return max(point[0] for point in self.points)

    @property
    def span_x(self) -> float:
        return self.max_x - self.min_x


def read_tendon_dxf(
    dxf_path: Path,
    *,
    layer_regex: str = r"^\d{4}$",
    mirror_half_span: bool = True,
    arc_angle_deg: float = 5.0,
) -> TendonDxfData:
    """Read tendon geometry from ``dxf_path``.

    The returned points are sorted by local ``x`` and have already been mirrored
    to full span when ``mirror_half_span=True``.
    """
    ezdxf = _load_ezdxf()
    if not dxf_path.exists():
        msg = f"Không tìm thấy file DXF cáp: {dxf_path}"
        raise DxfTendonError(msg)
    try:
        doc = ezdxf.readfile(str(dxf_path))
    except (OSError, ezdxf.DXFError) as exc:
        msg = f"Không đọc được DXF cáp '{dxf_path}': {exc}"
        raise DxfTendonError(msg) from exc

    scale = _unit_scale(doc)
    layer_pattern = re.compile(layer_regex)
    numeric_entities = _numeric_layer_entities(doc, layer_pattern, scale, arc_angle_deg)
    if not numeric_entities:
        msg = f"DXF '{dxf_path}': không có layer cáp khớp regex {layer_regex!r}"
        raise DxfTendonError(msg)

    split_y = _cluster_split_y(numeric_entities)
    elevation_entities = [entity for entity in numeric_entities if entity.centroid_y >= split_y]
    plan_entities = [entity for entity in numeric_entities if entity.centroid_y < split_y]
    if not elevation_entities:
        msg = f"DXF '{dxf_path}': không tách được đường mặt đứng cáp"
        raise DxfTendonError(msg)

    elevation_top_y = _elevation_top_y(doc, elevation_entities, scale)
    plan_center_y = _plan_center_y(doc, plan_entities, split_y, scale)
    mirror_x = max(entity.max_x for entity in elevation_entities)

    profiles: list[TendonLayerProfile] = []
    for layer in sorted({entity.layer for entity in numeric_entities}, key=_natural_key):
        elevation = _select_entity(elevation_entities, layer)
        if elevation is None:
            continue
        plan = _select_entity(plan_entities, layer)
        elevation_points = _normalise_series(
            [(x, y - elevation_top_y) for x, y in elevation.points],
        )
        if plan is None:
            plan_points = [(x, 0.0) for x, _ in elevation_points]
        else:
            plan_points = _normalise_series([(x, y - plan_center_y) for x, y in plan.points])

        if mirror_half_span:
            elevation_points = _mirror_series(elevation_points, mirror_x)
            plan_points = _mirror_series(plan_points, mirror_x)

        points_3d = _combine_plan_elevation(plan_points, elevation_points)
        if len(points_3d) >= 2:
            profiles.append(
                TendonLayerProfile(
                    layer=layer,
                    points_3d=points_3d,
                    elevation_points=elevation_points,
                    plan_points=plan_points,
                    source=str(dxf_path),
                )
            )

    if not profiles:
        msg = f"DXF '{dxf_path}': không tạo được profile cáp hợp lệ"
        raise DxfTendonError(msg)

    return TendonDxfData(
        profiles=profiles,
        prototype_element_ids=_prototype_element_ids(doc),
        section_reference=_section_reference(doc, scale),
        mirror_x=_clean(mirror_x),
        plan_center_y=_clean(plan_center_y),
        elevation_top_y=_clean(elevation_top_y),
        source=str(dxf_path),
    )


def _load_ezdxf() -> Any:
    try:
        return importlib.import_module("ezdxf")
    except ModuleNotFoundError as exc:
        msg = "Cần cài optional dependency `vbridge-dyn[sections]` (ezdxf) để đọc tendon DXF"
        raise DxfUnavailableError(msg) from exc


def _unit_scale(doc: Any) -> float:
    insunits = int(doc.header.get("$INSUNITS", 0) or 0)
    return _INSUNITS_TO_M.get(insunits, 1.0)


def _numeric_layer_entities(
    doc: Any,
    layer_pattern: re.Pattern[str],
    scale: float,
    arc_angle_deg: float,
) -> list[_LayerEntity]:
    entities: list[_LayerEntity] = []
    for entity in doc.modelspace():
        layer = str(getattr(entity.dxf, "layer", ""))
        if not layer_pattern.match(layer):
            continue
        points = _entity_points(entity, scale, arc_angle_deg)
        if len(points) >= 2:
            entities.append(_LayerEntity(layer=layer, points=points, entity_type=entity.dxftype()))
    return entities


def _entity_points(entity: Any, scale: float, arc_angle_deg: float) -> list[Point2D]:
    etype = entity.dxftype()
    try:
        if etype == "LINE":
            return [_pt(entity.dxf.start, scale), _pt(entity.dxf.end, scale)]
        if etype == "ARC":
            return _arc_points(
                entity.dxf.center,
                entity.dxf.radius,
                entity.dxf.start_angle,
                entity.dxf.end_angle,
                arc_angle_deg,
                scale,
            )
        if etype == "LWPOLYLINE":
            return _lwpolyline_points(entity, scale, arc_angle_deg)
        if etype in {"POLYLINE", "SPLINE", "ELLIPSE"}:
            return [_pt(point, scale) for point in entity.flattening(0.005 / scale)]
        if etype == "INSERT":
            points: list[Point2D] = []
            for sub in entity.virtual_entities():
                points.extend(_entity_points(sub, scale, arc_angle_deg))
            return points
    except Exception:
        return []
    return []


def _lwpolyline_points(entity: Any, scale: float, arc_angle_deg: float) -> list[Point2D]:
    try:
        raw = [(float(x), float(y), float(bulge)) for x, y, bulge in entity.get_points("xyb")]
    except Exception:
        return []
    if len(raw) < 2:
        return []

    is_closed = bool(getattr(entity, "closed", False)) or bool(getattr(entity, "is_closed", False))
    pairs = [(raw[i], raw[i + 1]) for i in range(len(raw) - 1)]
    if is_closed:
        pairs.append((raw[-1], raw[0]))

    points: list[Point2D] = []
    for start, end in pairs:
        if not points:
            points.append(_pt_xy((start[0], start[1]), scale))
        if abs(start[2]) < 1e-12:
            points.append(_pt_xy((end[0], end[1]), scale))
        else:
            arc_points = _bulge_points(
                (start[0], start[1]),
                (end[0], end[1]),
                start[2],
                arc_angle_deg,
                scale,
            )
            points.extend(arc_points[1:])
    return points


def _bulge_points(
    start: tuple[float, float],
    end: tuple[float, float],
    bulge: float,
    arc_angle_deg: float,
    scale: float,
) -> list[Point2D]:
    try:
        ezdxf_math = importlib.import_module("ezdxf.math")
        center, start_angle, end_angle, radius = ezdxf_math.bulge_to_arc(start, end, bulge)
    except Exception:
        return [_pt_xy(start, scale), _pt_xy(end, scale)]
    return _arc_points(
        center, radius, math.degrees(start_angle), math.degrees(end_angle), arc_angle_deg, scale
    )


def _arc_points(
    center: Any,
    radius: float,
    start_deg: float,
    end_deg: float,
    angle_deg: float,
    scale: float,
) -> list[Point2D]:
    cx, cy, r = float(center.x), float(center.y), float(radius)
    sweep = (float(end_deg) - float(start_deg)) % 360.0
    if sweep <= 1e-9:
        sweep = 360.0
    n = max(1, math.ceil(sweep / angle_deg))
    return [
        (
            _clean((cx + r * math.cos(math.radians(start_deg + sweep * k / n))) * scale),
            _clean((cy + r * math.sin(math.radians(start_deg + sweep * k / n))) * scale),
        )
        for k in range(n + 1)
    ]


def _pt(vec: Any, scale: float) -> Point2D:
    return (_clean(float(vec.x) * scale), _clean(float(vec.y) * scale))


def _pt_xy(point: tuple[float, float], scale: float) -> Point2D:
    return (_clean(point[0] * scale), _clean(point[1] * scale))


def _cluster_split_y(entities: list[_LayerEntity]) -> float:
    centroids = sorted(entity.centroid_y for entity in entities)
    gaps = [(centroids[i + 1] - centroids[i], i) for i in range(len(centroids) - 1)]
    if not gaps:
        return centroids[0]
    gap, idx = max(gaps, key=lambda item: item[0])
    if gap <= 1.0:
        return sum(centroids) / len(centroids)
    return (centroids[idx] + centroids[idx + 1]) / 2.0


def _elevation_top_y(doc: Any, elevation_entities: list[_LayerEntity], scale: float) -> float:
    x_min = min(entity.min_x for entity in elevation_entities)
    x_max = max(entity.max_x for entity in elevation_entities)
    y_min = min(min(y for _, y in entity.points) for entity in elevation_entities)
    y_max = max(max(y for _, y in entity.points) for entity in elevation_entities)
    candidates: list[float] = []
    for entity in doc.modelspace():
        if entity.dxftype() != "LINE":
            continue
        layer = str(getattr(entity.dxf, "layer", "")).lower()
        if layer not in {"center", "horizontal", "vertical", "0"}:
            continue
        p1 = _pt(entity.dxf.start, scale)
        p2 = _pt(entity.dxf.end, scale)
        if max(p1[0], p2[0]) < x_min - 0.5 or min(p1[0], p2[0]) > x_max + 0.5:
            continue
        for _, y in (p1, p2):
            if y_min - 1.0 <= y <= y_max + 2.0:
                candidates.append(y)
    if candidates:
        return max(candidates)
    return max(max(y for _, y in entity.points) for entity in elevation_entities)


def _plan_center_y(
    doc: Any,
    plan_entities: list[_LayerEntity],
    split_y: float,
    scale: float,
) -> float:
    best_length = -1.0
    best_y: float | None = None
    for entity in doc.modelspace():
        if entity.dxftype() != "LINE":
            continue
        layer = str(getattr(entity.dxf, "layer", "")).lower()
        if layer != "center":
            continue
        p1 = _pt(entity.dxf.start, scale)
        p2 = _pt(entity.dxf.end, scale)
        if abs(p1[1] - p2[1]) > 1e-6 or (p1[1] + p2[1]) / 2.0 >= split_y:
            continue
        length = abs(p2[0] - p1[0])
        if length > best_length:
            best_length = length
            best_y = (p1[1] + p2[1]) / 2.0
    if best_y is not None:
        return best_y
    if plan_entities:
        ys = sorted(point[1] for entity in plan_entities for point in entity.points)
        return ys[len(ys) // 2]
    return 0.0


def _select_entity(entities: list[_LayerEntity], layer: str) -> _LayerEntity | None:
    matches = [entity for entity in entities if entity.layer == layer]
    if not matches:
        return None
    return max(matches, key=lambda entity: (entity.span_x, len(entity.points)))


def _normalise_series(points: list[Point2D]) -> list[Point2D]:
    by_x: dict[float, list[float]] = {}
    for x, value in points:
        by_x.setdefault(round(x, 9), []).append(value)
    return [
        (_clean(x), _clean(sum(values) / len(values)))
        for x, values in sorted(by_x.items(), key=lambda item: item[0])
    ]


def _mirror_series(points: list[Point2D], mirror_x: float) -> list[Point2D]:
    mirrored = [(2.0 * mirror_x - x, value) for x, value in points if abs(x - mirror_x) > 1e-8]
    return _normalise_series(points + mirrored)


def _combine_plan_elevation(plan: list[Point2D], elevation: list[Point2D]) -> list[Point3D]:
    xs = sorted({round(x, 9) for x, _ in plan} | {round(x, 9) for x, _ in elevation})
    return [(_clean(x), _clean(_interp(plan, x)), _clean(_interp(elevation, x))) for x in xs]


def _interp(points: list[Point2D], x: float) -> float:
    if not points:
        return 0.0
    ordered = sorted(points)
    if x <= ordered[0][0]:
        return ordered[0][1]
    if x >= ordered[-1][0]:
        return ordered[-1][1]
    for (x1, y1), (x2, y2) in pairwise(ordered):
        if x1 <= x <= x2:
            span = x2 - x1
            if abs(span) <= 1e-12:
                return y1
            t = (x - x1) / span
            return y1 + (y2 - y1) * t
    return ordered[-1][1]


def _prototype_element_ids(doc: Any) -> list[int]:
    ids: set[int] = set()
    for entity in doc.modelspace():
        layer = str(getattr(entity.dxf, "layer", "")).lower()
        if layer != "elem" or entity.dxftype() not in {"TEXT", "MTEXT"}:
            continue
        raw = entity.dxf.text if entity.dxftype() == "TEXT" else entity.plain_text()
        text = str(raw).strip()
        if re.fullmatch(r"\d+", text):
            ids.add(int(text))
    return sorted(ids)


def _section_reference(doc: Any, scale: float) -> Point2D | None:
    for entity in doc.modelspace():
        if entity.dxftype() != "INSERT":
            continue
        name = str(getattr(entity.dxf, "name", "")).lower()
        if name == "ref":
            return _pt(entity.dxf.insert, scale)
    return None


def _natural_key(value: str) -> tuple[int, str]:
    return (int(value), value) if value.isdigit() else (10**9, value)


def _clean(value: float) -> float:
    if abs(value) < 5e-10:
        return 0.0
    return round(float(value), 9)
