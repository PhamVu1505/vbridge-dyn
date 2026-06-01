"""Tests cho DXF section reader (auto-chain + prune + đổi đơn vị)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vbridge_dyn.importers.dxf import DxfSectionError, read_section_polygon

ezdxf = pytest.importorskip("ezdxf")


def _add_closed(msp: object, pts: list[tuple[float, float]]) -> None:
    n = len(pts)
    for i in range(n):
        msp.add_line(pts[i], pts[(i + 1) % n])  # type: ignore[attr-defined]


def test_outer_and_hole_extracted(tmp_path: Path) -> None:
    path = tmp_path / "sec.dxf"
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 6  # mét
    msp = doc.modelspace()
    _add_closed(msp, [(-2, -1), (2, -1), (2, 1), (-2, 1)])  # bao ngoài 4×2
    _add_closed(msp, [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)])  # lỗ 1×1
    # nhánh hở giống dimension/leader → phải bị prune
    msp.add_line((-5, 5), (5, 5))
    msp.add_line((5, 5), (5, 6))
    doc.saveas(str(path))

    poly = read_section_polygon(path)

    assert len(poly.outer_boundary) == 4
    assert len(poly.holes) == 1
    assert len(poly.holes[0]) == 4
    xs = [p[0] for p in poly.outer_boundary]
    ys = [p[1] for p in poly.outer_boundary]
    assert max(xs) == pytest.approx(2.0)
    assert min(xs) == pytest.approx(-2.0)
    assert max(ys) == pytest.approx(1.0)
    assert min(ys) == pytest.approx(-1.0)


def test_mm_units_scaled_to_meters(tmp_path: Path) -> None:
    path = tmp_path / "sec_mm.dxf"
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # mm
    msp = doc.modelspace()
    _add_closed(msp, [(-2000, -1000), (2000, -1000), (2000, 1000), (-2000, 1000)])
    doc.saveas(str(path))

    poly = read_section_polygon(path)

    xs = [p[0] for p in poly.outer_boundary]
    assert max(xs) == pytest.approx(2.0)  # 2000 mm → 2 m
    assert min(xs) == pytest.approx(-2.0)


def test_open_chain_only_raises(tmp_path: Path) -> None:
    path = tmp_path / "open.dxf"
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_line((0, 0), (1, 0))
    msp.add_line((1, 0), (2, 0))  # chuỗi hở, không vòng kín
    doc.saveas(str(path))

    with pytest.raises(DxfSectionError):
        read_section_polygon(path)


def test_circle_entity_tessellated_by_angle(tmp_path: Path) -> None:
    path = tmp_path / "circle.dxf"
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    msp.add_circle((0, 0), radius=0.75)  # D = 1.5 m
    doc.saveas(str(path))

    poly = read_section_polygon(path)  # arc_angle_deg mặc định 10° → 36 đoạn

    assert len(poly.outer_boundary) == 36
    radii = [(x * x + y * y) ** 0.5 for x, y in poly.outer_boundary]
    assert max(radii) == pytest.approx(0.75, abs=1e-3)
    assert min(radii) == pytest.approx(0.75, abs=1e-3)


def test_arc_angle_override_changes_segment_count(tmp_path: Path) -> None:
    path = tmp_path / "circle2.dxf"
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 6
    doc.modelspace().add_circle((0, 0), radius=1.0)
    doc.saveas(str(path))

    poly = read_section_polygon(path, arc_angle_deg=30.0)  # 360/30 = 12 đoạn

    assert len(poly.outer_boundary) == 12


def test_largest_loop_is_outer(tmp_path: Path) -> None:
    path = tmp_path / "two.dxf"
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 6
    msp = doc.modelspace()
    _add_closed(msp, [(0, 0), (10, 0), (10, 6), (0, 6)])  # lớn (60)
    _add_closed(msp, [(2, 2), (4, 2), (4, 4), (2, 4)])  # nhỏ trong (4)
    doc.saveas(str(path))

    poly = read_section_polygon(path)

    outer_w = max(p[0] for p in poly.outer_boundary) - min(p[0] for p in poly.outer_boundary)
    assert outer_w == pytest.approx(10.0)
    assert len(poly.holes) == 1
