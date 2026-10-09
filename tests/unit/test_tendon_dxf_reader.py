"""Tests for tendon DXF extraction and Midas tendon export."""

from __future__ import annotations

from pathlib import Path

import pytest

from vbridge_dyn.importers.dxf.tendon_reader import read_tendon_dxf
from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct
from vbridge_dyn.io.project_io import load_project_folder

pytest.importorskip("ezdxf")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _bxd_project_dir() -> Path:
    return _repo_root() / "examples" / "bxd"


def test_bxd_tendon_dxf_reader_mirrors_half_span_profiles() -> None:
    dxf_path = _bxd_project_dir() / "dxf" / "tendon.dxf"
    if not dxf_path.exists():
        pytest.skip("BXD tendon.dxf fixture is not available")

    data = read_tendon_dxf(dxf_path)
    by_layer = {profile.layer: profile for profile in data.profiles}

    assert sorted(by_layer) == [
        "1001",
        "1002",
        "1003",
        "1004",
        "1005",
        "2001",
        "2002",
        "2003",
        "2004",
        "3001",
        "3002",
        "3003",
        "3004",
    ]
    assert data.prototype_element_ids == list(range(101, 109))
    assert data.section_reference == pytest.approx((53.329855807, -0.826371924))
    assert data.mirror_x == pytest.approx(16.3)

    p1002 = by_layer["1002"].points_3d
    assert p1002[0][0] == pytest.approx(0.55)
    assert p1002[-1][0] == pytest.approx(32.05)
    assert {round(point[1], 3) for point in p1002} == {0.5}

    assert min(point[1] for point in by_layer["2001"].points_3d) > 2.0
    assert max(point[1] for point in by_layer["3001"].points_3d) < -2.0


def test_bxd_mct_export_contains_tendon_blocks(tmp_path: Path) -> None:
    project_dir = _bxd_project_dir()
    if not (project_dir / "dxf" / "tendon.dxf").exists():
        pytest.skip("BXD tendon.dxf fixture is not available")
    if not (project_dir / "bridge.xlsx").exists():
        pytest.skip("BXD bridge.xlsx fixture is not available")

    project = load_project_folder(project_dir)
    out = tmp_path / "bxd.mct"

    warnings = write_base_model_mct(project, out, project_folder=project_dir)
    text = out.read_text(encoding="utf-8")

    assert any("Đã sinh 65 tendon profiles" in warning for warning in warnings)
    assert "*TENDON-GROUP" in text
    assert "*TDN-PROPERTY" in text
    assert "*TDN-PROFILE" in text
    assert "*TDN-PRESTRESS" in text
    assert "NAME=G1-T1001, PT_20T15.2_D110, 101to116" in text
    assert "NAME=G5-T3004, PT_20T15.2_D110, 501to516" in text
    assert "G1-T1001, FORCE, BOTH, 3906" in text
