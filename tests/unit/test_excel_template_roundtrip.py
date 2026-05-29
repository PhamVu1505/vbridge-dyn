"""Roundtrip: sinh bridge.xlsx template → đọc lại → check schema."""

from __future__ import annotations

import json
from pathlib import Path

import openpyxl

from vbridge_dyn.importers.excel.bridge_template_writer import write_bridge_template
from vbridge_dyn.importers.excel.workbook_reader import read_bridge_workbook


def test_template_roundtrip(tmp_path: Path) -> None:
    xlsx = tmp_path / "bridge.xlsx"
    write_bridge_template(xlsx)

    bridge, tracks = read_bridge_workbook(xlsx)

    # Template có 2 nodes + 1 element + 3 materials + 1 section + 2 supports
    assert len(bridge.nodes) == 2
    assert len(bridge.elements) == 1
    assert len(bridge.materials) == 3
    assert len(bridge.sections) == 1
    assert len(bridge.supports) == 2

    # Materials đầy đủ thông tin C40/C50/S355
    mat_ids = {m.id for m in bridge.materials}
    assert mat_ids == {"C40", "C50", "S355"}

    # 2 tracks T1/T2 ballastless
    assert len(tracks) == 2
    assert all(t.ballast_type == "ballastless" for t in tracks)
    assert tracks[0].accel_limit == 5.0


def test_section_polygon_columns_roundtrip(tmp_path: Path) -> None:
    xlsx = tmp_path / "bridge.xlsx"
    write_bridge_template(xlsx)

    wb = openpyxl.load_workbook(xlsx)
    ws = wb["Sections"]
    headers = {str(cell.value): cell.column for cell in ws[1]}
    ws.cell(
        row=2,
        column=headers["outer_boundary"],
        value=json.dumps([[-2.0, -1.0], [2.0, -1.0], [2.0, 1.0], [-2.0, 1.0]]),
    )
    ws.cell(
        row=2,
        column=headers["holes"],
        value=json.dumps([[[-1.0, -0.4], [1.0, -0.4], [1.0, 0.4], [-1.0, 0.4]]]),
    )
    ws.cell(row=2, column=headers["mesh_size"], value=0.2)
    ws.cell(row=2, column=headers["midas_offset"], value="CT")
    wb.save(xlsx)

    bridge, _ = read_bridge_workbook(xlsx)
    section = bridge.sections[0]

    assert section.outer_boundary == [(-2.0, -1.0), (2.0, -1.0), (2.0, 1.0), (-2.0, 1.0)]
    assert section.holes == [[(-1.0, -0.4), (1.0, -0.4), (1.0, 0.4), (-1.0, 0.4)]]
    assert section.mesh_size == 0.2
    assert section.midas_offset == "CT"
