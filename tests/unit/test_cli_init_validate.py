"""Integration test cho CLI: vbdyn init → vbdyn validate."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from vbridge_dyn.cli.main import app

runner = CliRunner()


def test_init_creates_folder_structure(tmp_path: Path) -> None:
    project_dir = tmp_path / "test_project"
    result = runner.invoke(
        app,
        ["init", str(project_dir), "--name", "Test", "--design-speed", "350"],
    )
    assert result.exit_code == 0, result.output

    assert (project_dir / "project.yaml").exists()
    assert (project_dir / "bridge.xlsx").exists()
    for sub in ("trains", "generated/midas", "solver_outputs/midas", "storage", "reports"):
        assert (project_dir / sub).exists(), f"Missing {sub}"


def test_validate_empty_bridge_reports_failures(tmp_path: Path) -> None:
    project_dir = tmp_path / "test_project"
    runner.invoke(app, ["init", str(project_dir), "--name", "Test"])

    result = runner.invoke(app, ["validate", str(project_dir)])
    # Bridge rỗng (chưa có node/element/material/section/support) → schema fail
    assert result.exit_code == 1


def test_info_command() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "VBridge-Dyn" in result.output


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "vbdyn" in result.output
