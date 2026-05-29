"""Sinh bridge.xlsx template với schemas + dòng hướng dẫn.

Sheets:
- Nodes        : id, x, y, z
- Elements     : id, type, n1, n2, material_id, section_id, structure_group
- Materials    : id, name, kind, grade, E, nu, rho, alpha_T, damping_ratio
- Sections     : id, name, material_id, A, Iy, Iz, J, Asy, Asz, kind,
                 outer_boundary, holes, mesh_size, midas_offset
- Supports     : node_id, Ux, Uy, Uz, Rx, Ry, Rz, boundary_group
- ElasticLinks : id, n1, n2, kx, ky, kz, krx, kry, krz, boundary_group
- RigidLinks   : id, master, slaves, dof_mask, boundary_group
- NodalMasses  : node_id, m, Ixx, Iyy, Izz
- DistributedMasses : target_group, mass_per_length, note
- StructureGroups : id, name, element_ids, node_ids
- Tracks       : id, name, centerline_y, rail_height_above_deck,
                 ballast_type, rail_spacing_trans, sleeper_spacing_long

Đơn vị nội bộ: SI (m, N, kg, s, °C, Pa).
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

_HEADER_FONT = Font(bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill("solid", fgColor="2E5C8A")
_NOTE_FONT = Font(italic=True, color="666666")


def _set_header(ws: Worksheet, headers: list[str]) -> None:
    for i, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=i, value=h)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.freeze_panes = "A2"
    for i in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 16


def _add_note(ws: Worksheet, row: int, text: str) -> None:
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = _NOTE_FONT


def write_bridge_template(path: Path) -> None:
    """Ghi bridge.xlsx template với 11 sheets + sample rows + hướng dẫn."""
    wb = Workbook()
    ws0 = wb.active
    assert ws0 is not None
    ws0.title = "_README"
    ws0.cell(row=1, column=1, value="bridge.xlsx — template VBridge-Dyn").font = Font(
        bold=True,
        size=14,
    )
    notes = [
        "",
        "Đơn vị nội bộ: SI (m, N, kg, s, °C, Pa). Exporter sẽ tự đổi sang đơn vị Midas/RM.",
        "Mỗi sheet một bảng — KHÔNG đổi tên sheet (workbook_reader đọc theo tên).",
        "Dòng 1 là header, dòng 2+ là dữ liệu. Không để dòng trống ở giữa.",
        "",
        "Trình tự đề xuất nhập:",
        "  1. Materials → 2. Sections → 3. Nodes → 4. Elements → 5. Supports",
        "  6. (tuỳ chọn) ElasticLinks/RigidLinks/NodalMasses/DistributedMasses",
        "  7. StructureGroups (Main Girder vs Sub Girder cho dynamic investigation)",
        "  8. Tracks",
        "",
        "Tham khảo bản tính HSR HCM-CG để biết quy ước Main Girder + Sub Girder.",
    ]
    for i, n in enumerate(notes, start=2):
        ws0.cell(row=i, column=1, value=n)
    ws0.column_dimensions["A"].width = 100

    # Nodes — 2 sample nodes để element 1 reference được
    ws = wb.create_sheet("Nodes")
    _set_header(ws, ["id", "x", "y", "z", "csys_id"])
    for i, (nid, x) in enumerate(((1, 0.0), (2, 10.0)), start=2):
        ws.cell(row=i, column=1, value=nid)
        ws.cell(row=i, column=2, value=x)
        ws.cell(row=i, column=3, value=0.0)
        ws.cell(row=i, column=4, value=0.0)
        ws.cell(row=i, column=5, value="global")

    # Elements
    ws = wb.create_sheet("Elements")
    _set_header(
        ws,
        [
            "id",
            "type",
            "n1",
            "n2",
            "material_id",
            "section_id",
            "structure_group",
            "local_axis_csys_id",
        ],
    )
    ws.cell(row=2, column=1, value=1)
    ws.cell(row=2, column=2, value="BEAM")
    ws.cell(row=2, column=3, value=1)
    ws.cell(row=2, column=4, value=2)
    ws.cell(row=2, column=5, value="C40")
    ws.cell(row=2, column=6, value="MainGirder")
    ws.cell(row=2, column=7, value="Main Girder")

    # Materials
    ws = wb.create_sheet("Materials")
    _set_header(
        ws,
        ["id", "name", "kind", "grade", "E", "nu", "rho", "alpha_T", "damping_ratio"],
    )
    samples = [
        ("C40", "Bê tông C40", "CONC", "C40", 3.4e10, 0.2, 2500.0, 1.0e-5, 0.013),
        ("C50", "Bê tông C50", "CONC", "C50", 3.65e10, 0.2, 2500.0, 1.0e-5, 0.013),
        ("S355", "Thép S355", "STEEL", "S355", 2.1e11, 0.3, 7850.0, 1.17e-5, 0.005),
    ]
    for i, row in enumerate(samples, start=2):
        for j, v in enumerate(row, start=1):
            ws.cell(row=i, column=j, value=v)

    # Sections
    ws = wb.create_sheet("Sections")
    _set_header(
        ws,
        [
            "id",
            "name",
            "material_id",
            "A",
            "Iy",
            "Iz",
            "J",
            "Asy",
            "Asz",
            "kind",
            "outer_boundary",
            "holes",
            "mesh_size",
            "midas_offset",
        ],
    )
    _add_note(
        ws,
        3,
        "Note: outer_boundary JSON dạng [[y,z],...]; holes JSON dạng [[[y,z],...],...].",
    )
    ws.cell(row=2, column=1, value="MainGirder")
    ws.cell(row=2, column=2, value="Dầm chính hộp BTCT")
    ws.cell(row=2, column=3, value="C40")
    ws.cell(row=2, column=4, value=8.97)
    ws.cell(row=2, column=5, value=10.09)
    ws.cell(row=2, column=6, value=18.5)
    ws.cell(row=2, column=7, value=12.3)
    ws.cell(row=2, column=10, value="girder")
    ws.cell(row=2, column=13, value=0.05)

    # Supports — pin tại node 1, roller tại node 2
    ws = wb.create_sheet("Supports")
    _set_header(
        ws,
        ["node_id", "Ux", "Uy", "Uz", "Rx", "Ry", "Rz", "boundary_group"],
    )
    ws.cell(row=2, column=1, value=1)
    for c in range(2, 5):
        ws.cell(row=2, column=c, value=1)
    for c in range(5, 8):
        ws.cell(row=2, column=c, value=0)
    ws.cell(row=2, column=8, value="Bearings")

    ws.cell(row=3, column=1, value=2)
    ws.cell(row=3, column=2, value=0)
    ws.cell(row=3, column=3, value=1)
    ws.cell(row=3, column=4, value=1)
    for c in range(5, 8):
        ws.cell(row=3, column=c, value=0)
    ws.cell(row=3, column=8, value="Bearings")

    # ElasticLinks
    ws = wb.create_sheet("ElasticLinks")
    _set_header(ws, ["id", "n1", "n2", "kx", "ky", "kz", "krx", "kry", "krz", "boundary_group"])

    # RigidLinks
    ws = wb.create_sheet("RigidLinks")
    _set_header(ws, ["id", "master", "slaves", "dof_mask", "boundary_group"])
    _add_note(ws, 3, "Note: slaves là chuỗi node_id cách nhau dấu phẩy, vd '12,13,14'")

    # NodalMasses
    ws = wb.create_sheet("NodalMasses")
    _set_header(ws, ["node_id", "m", "Ixx", "Iyy", "Izz"])

    # DistributedMasses
    ws = wb.create_sheet("DistributedMasses")
    _set_header(ws, ["target_group", "mass_per_length", "note"])
    ws.cell(row=2, column=1, value="Track 1 Ballast")
    ws.cell(row=2, column=2, value=600.0)
    ws.cell(row=2, column=3, value="Ballast 0.3m bão hoà, đoạn ballasted")

    # StructureGroups
    ws = wb.create_sheet("StructureGroups")
    _set_header(ws, ["id", "name", "element_ids", "node_ids"])
    _add_note(ws, 4, "Note: element_ids/node_ids dạng chuỗi cách nhau dấu phẩy, vd '101,102,103'")
    ws.cell(row=2, column=1, value="MainGirder")
    ws.cell(row=2, column=2, value="Main Girder")
    ws.cell(row=3, column=1, value="SubGirder")
    ws.cell(row=3, column=2, value="Sub Girder (dynamic investigation)")

    # Tracks
    ws = wb.create_sheet("Tracks")
    _set_header(
        ws,
        [
            "id",
            "name",
            "centerline_y",
            "rail_height_above_deck",
            "ballast_type",
            "rail_spacing_trans",
            "sleeper_spacing_long",
        ],
    )
    ws.cell(row=2, column=1, value="T1")
    ws.cell(row=2, column=2, value="Track 1")
    ws.cell(row=2, column=3, value=-2.5)
    ws.cell(row=2, column=4, value=0.7)
    ws.cell(row=2, column=5, value="ballastless")
    ws.cell(row=2, column=6, value=1.435)
    ws.cell(row=2, column=7, value=0.6)
    ws.cell(row=3, column=1, value="T2")
    ws.cell(row=3, column=2, value="Track 2")
    ws.cell(row=3, column=3, value=2.5)
    ws.cell(row=3, column=4, value=0.7)
    ws.cell(row=3, column=5, value="ballastless")
    ws.cell(row=3, column=6, value=1.435)
    ws.cell(row=3, column=7, value=0.6)

    wb.save(path)
