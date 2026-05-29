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


def test_validate_template_only_reports_missing_trains(tmp_path: Path) -> None:
    """Sau init, bridge.xlsx có sample tối thiểu (2 nodes + 1 element + supports)
    nên Bridge schema PASS; nhưng project.yaml `trains: []` rỗng → validate exit 1
    vì user chưa import HSLM/LM71 từ Excel. Đây là behavior mong muốn cho v0.1.
    """
    project_dir = tmp_path / "test_project"
    runner.invoke(app, ["init", str(project_dir), "--name", "Test"])

    result = runner.invoke(app, ["validate", str(project_dir)])
    assert result.exit_code == 1
    assert "Trains" in result.output
    # Bridge schema phải PASS (sample template hợp lệ)
    assert "Bridge tổng quan" in result.output


def test_validate_missing_supports_fails_bridge_check(tmp_path: Path) -> None:
    """Nếu user xóa Supports khỏi bridge.xlsx, validate fail ngay ở bridge level."""
    import openpyxl

    project_dir = tmp_path / "test_project"
    runner.invoke(app, ["init", str(project_dir), "--name", "Test"])

    xlsx = project_dir / "bridge.xlsx"
    wb = openpyxl.load_workbook(xlsx)
    sup = wb["Supports"]
    # Xóa hết data rows (giữ header)
    sup.delete_rows(2, sup.max_row)
    wb.save(xlsx)

    result = runner.invoke(app, ["validate", str(project_dir)])
    assert result.exit_code == 1
    assert "Supports" in result.output and "Không có support" in result.output


def test_info_command() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "VBridge-Dyn" in result.output


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "vbdyn" in result.output
