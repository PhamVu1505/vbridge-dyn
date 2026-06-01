"""Tests for initial Midas MCT generation."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from vbridge_dyn.cli.main import app
from vbridge_dyn.core.schemas.properties import FrameSection, Material
from vbridge_dyn.integrations.midas.mct import generate_midas_mct
from vbridge_dyn.integrations.midas.mct.sections import build_polygon_section_lines
from vbridge_dyn.io.project_io import load_project_folder

runner = CliRunner()


def test_generate_midas_mct_from_init_template(tmp_path: Path) -> None:
    project_dir = tmp_path / "test_project"
    init_result = runner.invoke(app, ["init", str(project_dir), "--name", "Test"])
    assert init_result.exit_code == 0, init_result.output

    project = load_project_folder(project_dir)
    result = generate_midas_mct(project, project_dir)

    text = result.mct_path.read_text(encoding="utf-8")
    assert "*NODE" in text
    assert "*ELEMENT" in text
    assert "*MATERIAL" in text
    assert "*SECT-PSCVALUE" in text
    # GEN section luôn phải có OPOLY (kể cả fallback chữ nhật) mới hiển thị trong Midas
    assert "OPOLY=" in text
    assert "*CONSTRAINT" in text
    assert "   1, 111000, " in text
    assert "Bearings" not in text
    assert "*ENDDATA" in text
    assert result.manifest_path.exists()


def test_cli_generate_midas_creates_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "test_project"
    runner.invoke(app, ["init", str(project_dir), "--name", "Test"])

    result = runner.invoke(app, ["generate", str(project_dir), "--target", "midas"])

    assert result.exit_code == 0, result.output
    assert (project_dir / "generated" / "midas" / "model_base.mct").exists()
    assert (project_dir / "generated" / "midas" / "generation_manifest.json").exists()


def test_polygon_section_writer_matches_converter_shape_contract() -> None:
    pytest.importorskip("shapely")
    pytest.importorskip("sectionproperties")

    section = FrameSection(
        id="RECT",
        name="Rectangle",
        material_id="C40",
        A=4.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=[(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)],
        mesh_size=0.2,
    )
    material = Material(id="C40", name="C40", E=3.4e10, rho=2500.0, kind="CONC")

    lines = build_polygon_section_lines(section, material, midas_id=7)

    assert lines[0].startswith("SECT=   7, VALUE")
    assert lines[1].startswith("4.0000,")
    assert len([line for line in lines if line.startswith("OPOLY=")]) == 1


def test_circular_section_emits_dbuser(tmp_path: Path) -> None:
    import math

    from vbridge_dyn.core.schemas.bridge import Bridge
    from vbridge_dyn.core.schemas.geometry import Element, Node
    from vbridge_dyn.core.schemas.project import Project, ProjectMeta
    from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct

    n = 36
    radius = 0.75  # D = 1.5 m (cọc khoan nhồi)
    circle = [
        (round(radius * math.cos(2 * math.pi * k / n), 6), round(radius * math.sin(2 * math.pi * k / n), 6))
        for k in range(n)
    ]
    section = FrameSection(
        id="PILE", name="Coc D1500", material_id="C30", A=1.0, Iy=1.0, Iz=1.0, J=1.0,
        outer_boundary=circle, kind="pier",
    )
    bridge = Bridge(
        nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=0, y=0, z=-10)],
        elements=[Element(id=1, type="BEAM", n1=1, n2=2, material_id="C30", section_id="PILE")],
        materials=[Material(id="C30", name="C30", E=3.0e10, rho=2500.0, kind="CONC")],
        sections=[section],
    )
    project = Project(meta=ProjectMeta(name="pile"), bridge=bridge)

    out = tmp_path / "pile.mct"
    write_base_model_mct(project, out)
    text = out.read_text(encoding="utf-8")

    assert "*SECTION" in text
    assert "DBUSER" in text
    assert "SR ," in text  # solid round, không phải GEN polygon
    assert "*SECT-PSCVALUE" not in text  # chỉ có mặt cắt tròn → không có khối PSC
