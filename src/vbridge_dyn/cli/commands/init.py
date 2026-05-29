"""`vbdyn init <folder>` — tạo folder workspace mới."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from vbridge_dyn.io.project_templates import write_project_template


def init_project(
    *,
    folder: Path,
    name: str,
    author: str,
    design_speed_kmh: float,
    track_type: str,
    force: bool,
    console: Console,
) -> None:
    if folder.exists() and any(folder.iterdir()) and not force:
        console.print(
            f"[red]Folder {folder} đã tồn tại và không rỗng.[/red] Dùng --force để ghi đè."
        )
        raise typer.Exit(1)

    folder.mkdir(parents=True, exist_ok=True)
    for sub in (
        "trains",
        "generated/midas",
        "generated/rm_bridge",
        "solver_outputs/midas",
        "solver_outputs/rm_bridge",
        "storage",
        "figures",
        "reports",
    ):
        (folder / sub).mkdir(parents=True, exist_ok=True)

    yaml_path = folder / "project.yaml"
    write_project_template(
        yaml_path,
        name=name,
        author=author,
        design_speed_kmh=design_speed_kmh,
        track_type=track_type,
    )

    bridge_xlsx = folder / "bridge.xlsx"
    if bridge_xlsx.exists() and not force:
        console.print(f"[yellow]Đã tồn tại {bridge_xlsx}, giữ nguyên.[/yellow]")
    else:
        from vbridge_dyn.importers.excel.bridge_template_writer import write_bridge_template

        write_bridge_template(bridge_xlsx)

    console.print(f"[green]✓[/green] Khởi tạo project [bold]{name}[/bold] tại {folder}")
    console.print(f"  • {yaml_path}")
    console.print(f"  • {bridge_xlsx} (template — vui lòng nhập dữ liệu)")
    console.print("  • Folders: trains/, generated/, solver_outputs/, storage/, figures/, reports/")
    console.print("")
    console.print("Tiếp theo:")
    console.print(f"  1. Mở [bold]{bridge_xlsx}[/bold] và nhập node/element/section/material.")
    console.print(f"  2. Chạy [cyan]vbdyn validate {folder}[/cyan] để kiểm tra.")
