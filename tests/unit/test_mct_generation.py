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
