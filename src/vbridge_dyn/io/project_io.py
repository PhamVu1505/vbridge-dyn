"""Load và save project.yaml (Pydantic ↔ YAML)."""

from pathlib import Path
from typing import Any

import yaml

from vbridge_dyn.core.schemas.project import Project
from vbridge_dyn.importers.excel.workbook_reader import read_bridge_workbook


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"{path} không phải YAML mapping hợp lệ"
        raise ValueError(msg)
    return data


def load_project_yaml(path: Path) -> Project:
    """Load `project.yaml` và return validated Project.

    `bridge` section thường được load từ Excel workbook riêng (xem
    importers/excel/workbook_reader.py). Nếu project.yaml chỉ có
    `bridge.workbook: <path>`, caller phải bổ sung Bridge sau khi đọc Excel.
    """
    data = _load_yaml_dict(path)
    return Project.model_validate(data)


def load_project_folder(folder: Path) -> Project:
    """Load project folder, tự merge `bridge.xlsx` khi `project.yaml.bridge` rỗng."""
    yaml_path = folder / "project.yaml"
    data = _load_yaml_dict(yaml_path)

    bridge_raw = data.get("bridge") or {}
    if not isinstance(bridge_raw, dict):
        msg = "project.yaml bridge phải là mapping"
        raise ValueError(msg)

    bridge_is_empty = not (bridge_raw.get("nodes") or bridge_raw.get("elements"))
    xlsx_path = folder / "bridge.xlsx"
    if bridge_is_empty and xlsx_path.exists():
        bridge, tracks = read_bridge_workbook(xlsx_path)
        data["bridge"] = bridge.model_dump(mode="json")
        if not data.get("tracks") and tracks:
            data["tracks"] = [track.model_dump(mode="json") for track in tracks]

    return Project.model_validate(data)


def save_project_yaml(project: Project, path: Path) -> None:
    """Lưu Project ra YAML (UTF-8, allow Unicode tiếng Việt)."""
    data: dict[str, Any] = project.model_dump(mode="json", exclude_none=True)
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=120,
        ),
        encoding="utf-8",
    )
