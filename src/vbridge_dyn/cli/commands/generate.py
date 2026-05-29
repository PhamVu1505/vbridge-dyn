"""`vbdyn generate` — sinh input files cho solver."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from vbridge_dyn.integrations.midas.mct import generate_midas_mct
from vbridge_dyn.io.project_io import load_project_folder


def generate_project(*, folder: Path, target: str, console: Console) -> None:
    if target != "midas":
        msg = "v0.2-alpha mới hỗ trợ --target midas"
        raise typer.BadParameter(msg)

    project = load_project_folder(folder)
    result = generate_midas_mct(project, folder)

    console.print(f"[green]✓[/green] Đã sinh Midas MCT: [bold]{result.mct_path}[/bold]")
    console.print(f"[green]✓[/green] Manifest: [bold]{result.manifest_path}[/bold]")
    for warning in result.warnings:
        console.print(f"[yellow]WARN[/yellow] {warning}")
