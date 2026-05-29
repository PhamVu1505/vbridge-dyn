"""Load và save project.yaml (Pydantic ↔ YAML)."""

from pathlib import Path
from typing import Any

import yaml

from vbridge_dyn.core.schemas.project import Project


def load_project_yaml(path: Path) -> Project:
    """Load `project.yaml` và return validated Project.

    `bridge` section thường được load từ Excel workbook riêng (xem
    importers/excel/workbook_reader.py). Nếu project.yaml chỉ có
    `bridge.workbook: <path>`, caller phải bổ sung Bridge sau khi đọc Excel.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
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
