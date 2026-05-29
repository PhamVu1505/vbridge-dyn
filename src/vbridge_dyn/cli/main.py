"""Typer CLI app cho VBridge-Dyn."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from vbridge_dyn import __version__
from vbridge_dyn.cli.commands.generate import generate_project
from vbridge_dyn.cli.commands.init import init_project
from vbridge_dyn.cli.commands.validate import validate_project

console = Console()

app = typer.Typer(
    name="vbdyn",
    help="VBridge-Dyn — phân tích động cầu đường sắt tốc độ cao (TCVN 13594).",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Hiển thị phiên bản rồi thoát.",
        is_eager=True,
    ),
) -> None:
    if version:
        console.print(f"vbdyn {__version__}")
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        # Không có flag và không có subcommand → in help
        console.print(ctx.get_help())
        raise typer.Exit(0)


@app.command(name="init", help="Khởi tạo project folder mới.")
def cmd_init(
    folder: Path = typer.Argument(..., help="Tên / đường dẫn folder project mới."),
    name: str = typer.Option("", "--name", "-n", help="Tên dự án (mặc định = tên folder)."),
    author: str = typer.Option("", "--author", help="Tên tác giả."),
    design_speed_kmh: float = typer.Option(
        350.0,
        "--design-speed",
        help="Vận tốc thiết kế V_tk (km/h).",
    ),
    track_type: str = typer.Option(
        "ballasted",
        "--track-type",
        help="ballasted | ballastless.",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Ghi đè nếu folder tồn tại."),
) -> None:
    init_project(
        folder=folder,
        name=name or folder.name,
        author=author,
        design_speed_kmh=design_speed_kmh,
        track_type=track_type,
        force=force,
        console=console,
    )


@app.command(name="validate", help="Kiểm tra project.yaml + workbook + tham chiếu.")
def cmd_validate(
    folder: Path = typer.Argument(..., help="Đường dẫn folder project."),
) -> None:
    ok, report = validate_project(folder)
    table = Table(title=f"Validate: {folder}", show_lines=False)
    table.add_column("Mục", style="bold")
    table.add_column("Trạng thái")
    table.add_column("Chi tiết")
    for row in report:
        status_style = "green" if row.status == "PASS" else "red"
        table.add_row(row.name, f"[{status_style}]{row.status}[/{status_style}]", row.detail)
    console.print(table)
    if not ok:
        raise typer.Exit(1)


@app.command(name="generate", help="Sinh input files cho solver (Midas/RM).")
def cmd_generate(
    folder: Path = typer.Argument(..., help="Đường dẫn folder project."),
    target: str = typer.Option("midas", "--target", "-t", help="midas | rm_bridge."),
) -> None:
    generate_project(folder=folder, target=target, console=console)


@app.command(name="info", help="Thông tin về VBridge-Dyn (version, paths).")
def cmd_info() -> None:
    console.print(f"[bold]VBridge-Dyn[/bold] v{__version__}")
    console.print("• Tài liệu: AGENTS.md, CLAUDE.md, PROJECT_STATUS.md, TASK_LOG.md")
    console.print("• Plan đầy đủ: docs/PLAN_REV9.md")
    console.print("• Repo: https://github.com/PhamVu1505/vbridge-dyn")


if __name__ == "__main__":  # pragma: no cover
    app()
