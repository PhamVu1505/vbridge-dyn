"""Đọc bridge.xlsx → `Bridge` schema.

Trả về `Bridge` validated. Skipping sheets rỗng (chỉ header) là OK — chỉ
materials/sections/nodes/elements là bắt buộc.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from vbridge_dyn.core.schemas.boundary import ElasticLink, RigidLink, Support
from vbridge_dyn.core.schemas.bridge import Bridge
from vbridge_dyn.core.schemas.geometry import Element, Node
from vbridge_dyn.core.schemas.groups import BoundaryGroup, StructureGroup
from vbridge_dyn.core.schemas.mass import ElementDistributedMass, NodalMass
from vbridge_dyn.core.schemas.properties import FrameSection, Material
from vbridge_dyn.core.schemas.track import Track
from vbridge_dyn.importers.dxf import read_section_polygon


def _read_rows(ws: Worksheet) -> list[dict[str, Any]]:
    """Đọc sheet → list[dict] theo header dòng 1."""
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h) if h is not None else "" for h in rows[0]]
    out: list[dict[str, Any]] = []
    for r in rows[1:]:
        # bỏ qua dòng comment bắt đầu bằng "Note:"
        if r and r[0] and isinstance(r[0], str) and r[0].lstrip().startswith("Note:"):
            continue
        if all(c is None or c == "" for c in r):
            continue
        record = {h: v for h, v in zip(headers, r, strict=False) if h}
        out.append(record)
    return out


def _split_ids(value: Any) -> list[int]:
    if value is None or value == "":
        return []
    s = str(value).replace(";", ",")
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def _parse_point_pairs(value: Any) -> list[tuple[float, float]] | None:
    if value is None or value == "":
        return None
    raw = json.loads(str(value))
    return _coerce_point_pairs(raw)


def _parse_holes(value: Any) -> list[list[tuple[float, float]]]:
    if value is None or value == "":
        return []
    raw = json.loads(str(value))
    if not isinstance(raw, list):
        msg = "holes phải là JSON array các polygon"
        raise ValueError(msg)
    return [_coerce_point_pairs(hole) for hole in raw]


def _coerce_point_pairs(raw: Any) -> list[tuple[float, float]]:
    if not isinstance(raw, list):
        msg = "polygon phải là JSON array các điểm [y,z]"
        raise ValueError(msg)
    points: list[tuple[float, float]] = []
    for item in raw:
        if not isinstance(item, list | tuple) or len(item) != 2:
            msg = f"điểm polygon không hợp lệ: {item!r}"
            raise ValueError(msg)
        points.append((float(item[0]), float(item[1])))
    return points


def _resolve_path(base_dir: Path, raw: str) -> Path:
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else (base_dir / candidate)


def _apply_dxf_axis_order(
    outer: list[tuple[float, float]],
    holes: list[list[tuple[float, float]]],
    axis_order: str | None,
) -> tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]:
    if axis_order in (None, "", "xy"):
        return outer, holes
    if axis_order in {"yx", "swap"}:
        return (
            [(z, y) for y, z in outer],
            [[(z, y) for y, z in hole] for hole in holes],
        )
    msg = "dxf_axis_order chỉ hỗ trợ 'xy' hoặc 'yx'"
    raise ValueError(msg)


def _geom_value(value: Any, has_geometry: bool) -> float:
    """A/Iy/Iz/J: bắt buộc khi không có polygon; placeholder khi có (writer tự tính lại)."""
    if value not in (None, ""):
        return float(value)
    if has_geometry:
        return 1.0  # placeholder — build_polygon_section_lines tính lại từ polygon/DXF
    msg = "Section thiếu A/Iy/Iz/J và không có polygon hoặc dxf_file để tính"
    raise ValueError(msg)


def _section_from_row(r: dict[str, Any], base_dir: Path) -> FrameSection:
    outer = _parse_point_pairs(r.get("outer_boundary"))
    holes = _parse_holes(r.get("holes"))
    dxf_file = r.get("dxf_file")
    dxf_layer = str(r["dxf_layer"]) if r.get("dxf_layer") else None
    dxf_axis_order = str(r["dxf_axis_order"]).lower() if r.get("dxf_axis_order") else None
    taper_start = str(r["taper_start_section_id"]) if r.get("taper_start_section_id") else None
    taper_end = str(r["taper_end_section_id"]) if r.get("taper_end_section_id") else None
    if dxf_file:
        polygon = read_section_polygon(_resolve_path(base_dir, str(dxf_file)), layer=dxf_layer)
        outer, holes = _apply_dxf_axis_order(
            polygon.outer_boundary,
            polygon.holes,
            dxf_axis_order,
        )
    has_geometry = outer is not None
    has_taper = taper_start is not None and taper_end is not None
    return FrameSection(
        id=str(r["id"]),
        name=str(r.get("name") or r["id"]),
        material_id=str(r["material_id"]),
        A=_geom_value(r.get("A"), has_geometry or has_taper),
        Iy=_geom_value(r.get("Iy"), has_geometry or has_taper),
        Iz=_geom_value(r.get("Iz"), has_geometry or has_taper),
        J=_geom_value(r.get("J"), has_geometry or has_taper),
        Asy=float(r["Asy"]) if r.get("Asy") not in (None, "") else None,
        Asz=float(r["Asz"]) if r.get("Asz") not in (None, "") else None,
        kind=str(r.get("kind") or "girder"),
        outer_boundary=outer,
        holes=holes,
        mesh_size=float(r.get("mesh_size") or 0.05),
        midas_offset=str(r["midas_offset"]) if r.get("midas_offset") else None,
        taper_start_section_id=taper_start,
        taper_end_section_id=taper_end,
    )


def read_bridge_workbook(path: Path, base_dir: Path | None = None) -> tuple[Bridge, list[Track]]:
    """Load bridge.xlsx → `(Bridge, list[Track])` (validate qua pydantic).

    `base_dir` để resolve đường dẫn DXF tương đối trong cột `dxf_file` (mặc định
    = thư mục chứa workbook).
    """
    base = base_dir if base_dir is not None else path.parent
    wb = load_workbook(path, data_only=True, read_only=True)

    def _rows(name: str) -> list[dict[str, Any]]:
        if name not in wb.sheetnames:
            return []
        return _read_rows(wb[name])

    nodes = [
        Node(
            id=int(r["id"]),
            x=float(r["x"]),
            y=float(r["y"]),
            z=float(r["z"]),
            csys_id=str(r.get("csys_id") or "global"),
        )
        for r in _rows("Nodes")
    ]

    elements = [
        Element(
            id=int(r["id"]),
            type=str(r.get("type") or "BEAM").upper(),
            n1=int(r["n1"]),
            n2=int(r["n2"]),
            material_id=str(r["material_id"]),
            section_id=str(r["section_id"]),
            structure_group=str(r.get("structure_group") or ""),
            local_axis_csys_id=str(r["local_axis_csys_id"])
            if r.get("local_axis_csys_id")
            else None,
        )
        for r in _rows("Elements")
    ]

    materials = [
        Material(
            id=str(r["id"]),
            name=str(r.get("name") or r["id"]),
            kind=str(r.get("kind") or "CONC").upper(),
            grade=str(r["grade"]) if r.get("grade") else None,
            E=float(r["E"]),
            nu=float(r.get("nu") or 0.2),
            rho=float(r["rho"]),
            alpha_T=float(r.get("alpha_T") or 1.0e-5),
            damping_ratio=float(r.get("damping_ratio") or 0.0),
        )
        for r in _rows("Materials")
    ]

    sections = [_section_from_row(r, base) for r in _rows("Sections")]

    supports = [
        Support(
            node_id=int(r["node_id"]),
            constraint=[
                int(r["Ux"]),
                int(r["Uy"]),
                int(r["Uz"]),
                int(r["Rx"]),
                int(r["Ry"]),
                int(r["Rz"]),
            ],
            boundary_group=str(r.get("boundary_group") or ""),
        )
        for r in _rows("Supports")
    ]

    elastic_links = [
        ElasticLink(
            id=int(r["id"]),
            n1=int(r["n1"]),
            n2=int(r["n2"]),
            kx=float(r["kx"]),
            ky=float(r["ky"]),
            kz=float(r["kz"]),
            krx=float(r["krx"]),
            kry=float(r["kry"]),
            krz=float(r["krz"]),
            boundary_group=str(r.get("boundary_group") or ""),
            dof_mask=str(r.get("dof_mask") or "111111"),
            angle=float(r.get("angle") or 0.0),
            sd_i=float(r.get("sd_i") or 0.5),
            sd_j=float(r.get("sd_j") or 0.5),
        )
        for r in _rows("ElasticLinks")
    ]

    rigid_links = [
        RigidLink(
            id=int(r["id"]),
            master=int(r["master"]),
            slaves=_split_ids(r.get("slaves")),
            dof_mask=str(r.get("dof_mask") or "111111"),
            boundary_group=str(r.get("boundary_group") or ""),
        )
        for r in _rows("RigidLinks")
    ]

    nodal_masses = [
        NodalMass(
            node_id=int(r["node_id"]),
            m=float(r["m"]),
            Ixx=float(r.get("Ixx") or 0.0),
            Iyy=float(r.get("Iyy") or 0.0),
            Izz=float(r.get("Izz") or 0.0),
        )
        for r in _rows("NodalMasses")
    ]

    distributed_masses = [
        ElementDistributedMass(
            target_group=str(r["target_group"]),
            mass_per_length=float(r["mass_per_length"]),
            note=str(r.get("note") or ""),
        )
        for r in _rows("DistributedMasses")
    ]

    structure_groups = [
        StructureGroup(
            id=str(r["id"]),
            name=str(r.get("name") or r["id"]),
            element_ids=_split_ids(r.get("element_ids")),
            node_ids=_split_ids(r.get("node_ids")),
        )
        for r in _rows("StructureGroups")
    ]

    boundary_groups = [
        BoundaryGroup(
            id=str(r["id"]),
            name=str(r.get("name") or r["id"]),
        )
        for r in _rows("BoundaryGroups")
    ]

    bridge = Bridge(
        nodes=nodes,
        elements=elements,
        materials=materials,
        sections=sections,
        supports=supports,
        elastic_links=elastic_links,
        rigid_links=rigid_links,
        nodal_masses=nodal_masses,
        distributed_masses=distributed_masses,
        structure_groups=structure_groups,
        boundary_groups=boundary_groups,
    )
    tracks = _read_tracks(wb)
    return bridge, tracks


def _read_tracks(wb: Workbook) -> list[Track]:
    if "Tracks" not in wb.sheetnames:
        return []
    rows = _read_rows(wb["Tracks"])
    out: list[Track] = []
    for r in rows:
        track = Track(
            id=str(r["id"]),
            name=str(r.get("name") or r["id"]),
            centerline_y=float(r.get("centerline_y") or 0.0),
            rail_height_above_deck=float(r.get("rail_height_above_deck") or 0.0),
            ballast_type=str(r.get("ballast_type") or "ballasted"),
        )
        # khoảng cách ray/sleeper override nếu user nhập
        if r.get("rail_spacing_trans"):
            track.distribution.rail_spacing_trans = float(r["rail_spacing_trans"])
        if r.get("sleeper_spacing_long"):
            track.distribution.sleeper_spacing_long = float(r["sleeper_spacing_long"])
        out.append(track)
    return out
