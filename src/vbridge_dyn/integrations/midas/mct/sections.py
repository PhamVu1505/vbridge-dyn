"""Midas `*SECT-PSCVALUE` generation from section polygons.

This ports the validated section creation logic from the local
`refer/Converte_RM_to_Midas` workflow into VBridge-Dyn:

- build a Shapely polygon from outer boundary + holes,
- mesh and calculate properties with `sectionproperties`,
- translate OPOLY/IPOLY to centroid coordinates,
- choose STIFF3 stress points by max Euclidean distance in four quadrants.
"""

from __future__ import annotations

import importlib
import math
from typing import Any

from vbridge_dyn.core.schemas.properties import FrameSection, Material

Point2D = tuple[float, float]


class SectionPolygonUnavailableError(RuntimeError):
    """Raised when optional polygon section dependencies are not installed."""


def build_polygon_section_lines(
    section: FrameSection,
    material: Material,
    midas_id: int,
) -> list[str]:
    """Build a Midas VALUE/GEN section with OPOLY/IPOLY from a polygon section."""
    if not section.outer_boundary:
        msg = f"Section '{section.id}' không có outer_boundary"
        raise ValueError(msg)

    tools = _load_section_tools()
    polygon = tools["Polygon"]
    make_valid = tools["make_valid"]
    geometry_cls = tools["Geometry"]
    sp_material_cls = tools["Material"]
    section_cls = tools["Section"]

    valid_holes = _filter_valid_holes(polygon, section.outer_boundary, section.holes)
    outer_poly = polygon(section.outer_boundary, valid_holes)
    if not bool(outer_poly.is_valid):
        fixed = make_valid(outer_poly)
        geom_type = str(fixed.geom_type)
        if geom_type == "MultiPolygon":
            outer_poly = max(fixed.geoms, key=lambda geom: float(geom.area))
        elif geom_type == "Polygon":
            outer_poly = fixed
        else:
            msg = f"Section '{section.id}' make_valid tạo geometry không hỗ trợ: {geom_type}"
            raise ValueError(msg)

    sp_material = sp_material_cls(
        name=material.name,
        elastic_modulus=material.E,
        poissons_ratio=material.nu,
        yield_strength=250e6,
        density=material.rho,
        color="blue",
    )
    geometry = geometry_cls(geom=outer_poly, material=sp_material)
    geometry.create_mesh(mesh_sizes=section.mesh_size)
    section_model = section_cls(geometry)
    section_model.calculate_geometric_properties()
    section_model.calculate_warping_properties()

    e_eff = float(section_model.get_e_eff()) if bool(section_model.is_composite()) else 1.0
    area = float(section_model.get_area())
    if bool(section_model.is_composite()):
        ea_shear = section_model.get_eas()
        a_sy = float(ea_shear[0]) / e_eff
        a_sz = float(ea_shear[1]) / e_eff
        j = float(section_model.get_ej()) / e_eff
        eic = section_model.get_eic()
        i_yy = float(eic[0]) / e_eff
        i_zz = float(eic[1]) / e_eff
    else:
        shear_areas = section_model.get_as()
        a_sy = float(shear_areas[0])
        a_sz = float(shear_areas[1])
        j = float(section_model.get_j())
        inertia = section_model.get_ic()
        i_yy = float(inertia[0])
        i_zz = float(inertia[1])

    if math.isnan(a_sy) or math.isnan(a_sz):
        a_sy = area * 5.0 / 6.0 if math.isnan(a_sy) else a_sy
        a_sz = area * 5.0 / 6.0 if math.isnan(a_sz) else a_sz
    if math.isnan(j):
        j = i_yy + i_zz

    centroid = section_model.get_c()
    cy = float(centroid[0])
    cz = float(centroid[1])

    translated_outer_raw = _translate_points(section.outer_boundary, cy, cz)
    translated_holes_raw = [_translate_points(hole, cy, cz) for hole in valid_holes]

    simplified_outer_for_stiff3 = _translate_points(
        _simplify_polygon(section.outer_boundary),
        cy,
        cz,
    )
    quad_pts = _find_extreme_points_in_quadrants(simplified_outer_for_stiff3)
    stiff3 = [
        quad_pts[1][0],
        quad_pts[0][0],
        quad_pts[3][0],
        quad_pts[2][0],
        quad_pts[1][1],
        quad_pts[0][1],
        quad_pts[3][1],
        quad_pts[2][1],
    ]

    translated_outer = _adjust_to_counterclockwise(translated_outer_raw, quad_pts[0])
    translated_holes = [_adjust_hole_points(hole) for hole in translated_holes_raw]
    translated_outer = _simplify_polygon(translated_outer)
    translated_holes = [_simplify_polygon(hole) if hole else hole for hole in translated_holes]

    y_values = [point[0] for point in translated_outer]
    z_values = [point[1] for point in translated_outer]
    y_max = max(y_values)
    y_min = min(y_values)
    z_max = max(z_values)
    z_min = min(z_values)
    outer_perimeter = _calculate_perimeter(translated_outer)
    holes_perimeter = sum(_calculate_perimeter(hole) for hole in translated_holes)

    z_orig_values = [point[1] for point in section.outer_boundary]
    prefix = section.midas_offset or _detect_section_prefix(
        cz, min(z_orig_values), max(z_orig_values)
    )

    stiff1 = [area, a_sy, a_sz, j, i_yy, i_zz]
    stiff2 = [
        y_max,
        -y_min,
        z_max,
        -z_min,
        0.0,
        0.0,
        outer_perimeter,
        holes_perimeter,
        -y_min,
        -z_min,
    ]

    lines = [
        (
            f"SECT={midas_id:>4}, VALUE     , {_text(section.name):<18}, {prefix}, 0, 0, "
            "0, 0, 0, 0, YES, NO, GEN, YES, YES"
        ),
        ", ".join(f"{value:.4f}" for value in stiff1),
        ", ".join(f"{value:.6f}" for value in stiff2),
        ", ".join(f"{value:.6f}" for value in stiff3),
        "OPOLY=" + _format_points(translated_outer),
    ]
    for hole in translated_holes:
        if hole:
            lines.append("IPOLY=" + _format_points(hole))
    return lines


def _load_section_tools() -> dict[str, Any]:
    try:
        shapely_geometry = importlib.import_module("shapely.geometry")
        shapely_validation = importlib.import_module("shapely.validation")
        section_geometry = importlib.import_module("sectionproperties.pre.geometry")
        section_pre = importlib.import_module("sectionproperties.pre")
        section_analysis = importlib.import_module("sectionproperties.analysis.section")
    except ModuleNotFoundError as exc:
        msg = (
            "Cần cài optional dependencies `vbridge-dyn[sections]` "
            "để sinh section polygon OPOLY/IPOLY"
        )
        raise SectionPolygonUnavailableError(msg) from exc

    return {
        "Polygon": shapely_geometry.Polygon,
        "make_valid": shapely_validation.make_valid,
        "Geometry": section_geometry.Geometry,
        "Material": section_pre.Material,
        "Section": section_analysis.Section,
    }


def _filter_valid_holes(
    polygon_cls: Any,
    outer_boundary: list[Point2D],
    holes: list[list[Point2D]],
) -> list[list[Point2D]]:
    outer_shape = polygon_cls(outer_boundary)
    valid_holes: list[list[Point2D]] = []
    seen_bounds: set[tuple[float, float, float, float]] = set()
    for hole in holes:
        hole_shape = polygon_cls(hole)
        if len(hole) < 3 or abs(float(hole_shape.area)) < 1e-6:
            continue
        if not bool(hole_shape.is_valid):
            continue
        bounds = tuple(round(float(value), 4) for value in hole_shape.bounds)
        if len(bounds) != 4:
            continue
        if bounds in seen_bounds:
            continue
        seen_bounds.add((bounds[0], bounds[1], bounds[2], bounds[3]))
        if bool(outer_shape.contains(hole_shape)) or bool(outer_shape.intersects(hole_shape)):
            valid_holes.append(hole)
    return valid_holes


def _calculate_perimeter(points: list[Point2D]) -> float:
    if not points:
        return 0.0
    total = 0.0
    for i, point in enumerate(points):
        previous = points[i - 1]
        total += math.hypot(point[0] - previous[0], point[1] - previous[1])
    return total


def _translate_points(points: list[Point2D], cy: float, cz: float) -> list[Point2D]:
    return [(round(y - cy, 6), round(z - cz, 6)) for y, z in points]


def _is_clockwise(points: list[Point2D]) -> bool:
    if len(points) < 3:
        return False
    total = 0.0
    for i, point in enumerate(points):
        nxt = points[(i + 1) % len(points)]
        total += point[0] * nxt[1] - nxt[0] * point[1]
    return total > 0


def _reorder_points_with_start(points: list[Point2D], start_point: Point2D) -> list[Point2D]:
    if not points:
        return []
    distances = [
        math.hypot(point[0] - start_point[0], point[1] - start_point[1]) for point in points
    ]
    closest_idx = min(range(len(points)), key=lambda idx: distances[idx])
    if distances[closest_idx] < 1e-6:
        return points[closest_idx:] + points[:closest_idx]
    return points


def _adjust_to_counterclockwise(points: list[Point2D], start_point: Point2D) -> list[Point2D]:
    ordered = _reorder_points_with_start(points, start_point)
    if _is_clockwise(ordered):
        ordered = list(reversed(ordered))
        ordered = _reorder_points_with_start(ordered, start_point)
    return ordered


def _adjust_to_clockwise(points: list[Point2D], start_point: Point2D) -> list[Point2D]:
    ordered = _reorder_points_with_start(points, start_point)
    if not _is_clockwise(ordered):
        ordered = list(reversed(ordered))
        ordered = _reorder_points_with_start(ordered, start_point)
    return ordered


def _adjust_hole_points(hole: list[Point2D]) -> list[Point2D]:
    if len(hole) < 3:
        return hole
    start_point = min(hole, key=lambda point: (point[1], point[0]))
    return _adjust_to_clockwise(hole, start_point)


def _find_extreme_points_in_quadrants(points: list[Point2D]) -> list[Point2D]:
    quadrants = [
        [point for point in points if point[0] >= 0 and point[1] >= 0],
        [point for point in points if point[0] < 0 and point[1] >= 0],
        [point for point in points if point[0] < 0 and point[1] < 0],
        [point for point in points if point[0] >= 0 and point[1] < 0],
    ]
    result: list[Point2D] = []
    for quadrant in quadrants:
        if quadrant:
            result.append(max(quadrant, key=lambda point: math.hypot(point[0], point[1])))
        else:
            result.append((0.0, 0.0))
    return result


def _simplify_polygon(points: list[Point2D], tolerance: float = 1e-4) -> list[Point2D]:
    if len(points) < 4:
        return list(points)
    keep: list[Point2D] = []
    n_points = len(points)
    for i, point in enumerate(points):
        previous = points[(i - 1) % n_points]
        nxt = points[(i + 1) % n_points]
        if not _is_point_on_line(previous, point, nxt, tolerance):
            keep.append(point)
    return keep if len(keep) >= 3 else list(points)


def _is_point_on_line(p1: Point2D, p_mid: Point2D, p2: Point2D, tolerance: float) -> bool:
    v12 = (p2[0] - p1[0], p2[1] - p1[1])
    v1m = (p_mid[0] - p1[0], p_mid[1] - p1[1])
    cross = v12[0] * v1m[1] - v12[1] * v1m[0]
    length = math.hypot(v12[0], v12[1])
    if length < 1e-10:
        return True
    return abs(cross) / length < tolerance


def _detect_section_prefix(cz: float, z_min_orig: float, z_max_orig: float) -> str:
    section_height = z_max_orig - z_min_orig
    if section_height < 1e-10:
        return "CC"
    if abs(cz) / section_height < 0.10:
        return "CC"
    if cz < 0:
        return "CT"
    return "CB"


def _format_points(points: list[Point2D]) -> str:
    return ", ".join(f"{point[0]:.6f}, {point[1]:.6f}" for point in points)


def _text(value: str) -> str:
    return value.replace(",", " ").strip()
