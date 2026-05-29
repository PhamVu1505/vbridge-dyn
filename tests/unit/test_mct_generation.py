"""Tests for initial Midas MCT generation."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from vbridge_dyn.cli.main import app
from vbridge_dyn.integrations.midas.mct import generate_midas_mct
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
