"""`vbdyn validate <folder>` — kiểm tra project.yaml + Excel + tham chiếu."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from vbridge_dyn.core.schemas.project import Project
from vbridge_dyn.importers.excel.workbook_reader import read_bridge_workbook


@dataclass
class CheckRow:
    name: str
    status: str  # 'PASS' | 'FAIL'
    detail: str = ""


def validate_project(folder: Path) -> tuple[bool, list[CheckRow]]:
    """Trả về (ok, rows) — rows hiển thị bằng rich.Table ở CLI layer.

    Nếu project.yaml có `bridge` rỗng và folder có `bridge.xlsx`, sẽ load
    Excel để compose Bridge schema.
    """
    rows: list[CheckRow] = []

    if not folder.exists():
        rows.append(CheckRow("Folder tồn tại", "FAIL", f"{folder} không tồn tại"))
        return False, rows
    rows.append(CheckRow("Folder tồn tại", "PASS", str(folder)))

    yaml_path = folder / "project.yaml"
    if not yaml_path.exists():
        rows.append(CheckRow("project.yaml", "FAIL", f"Thiếu {yaml_path}"))
        return False, rows

    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    bridge_raw = raw.get("bridge") or {}
    bridge_is_empty = not (bridge_raw.get("nodes") or bridge_raw.get("elements"))

    xlsx_path = folder / "bridge.xlsx"
    tracks_from_excel: list = []
    if bridge_is_empty and xlsx_path.exists():
        try:
            bridge_obj, tracks_from_excel = read_bridge_workbook(xlsx_path)
        except Exception as e:
            rows.append(CheckRow("bridge.xlsx → Bridge", "FAIL", f"{type(e).__name__}: {e}"))
            return False, rows
        rows.append(
            CheckRow(
                "bridge.xlsx → Bridge",
                "PASS",
                f"Load từ {xlsx_path.name}",
            ),
        )
        raw["bridge"] = bridge_obj.model_dump(mode="json")
        if not raw.get("tracks") and tracks_from_excel:
            raw["tracks"] = [t.model_dump(mode="json") for t in tracks_from_excel]

    try:
        project = Project.model_validate(raw)
    except ValidationError as e:
        rows.append(CheckRow("project.yaml schema", "FAIL", str(e)))
        return False, rows
    rows.append(CheckRow("project.yaml schema", "PASS", "validate OK"))

    # standards_profile
    rows.append(
        CheckRow(
            "standards_profile",
            "PASS",
            f"{project.standards_profile}, parts: 3={project.tcvn13594_versions.part_3}, "
            f"4={project.tcvn13594_versions.part_4}",
        ),
    )

    # design speed
    v_max = project.design.design_speed_kmh * project.design.max_analysis_speed_factor
    rows.append(
        CheckRow(
            "Velocity range",
            "PASS",
            f"V_tk={project.design.design_speed_kmh:g}, V_max={v_max:g} km/h, "
            f"step={project.velocity_range.step_kmh:g}",
        ),
    )

    # bridge
    bridge_ok = _check_bridge(project, folder, rows)
    if not bridge_ok:
        return False, rows

    # trains
    n_trains = len(project.trains)
    rows.append(
        CheckRow(
            "Trains",
            "PASS" if n_trains > 0 else "FAIL",
            f"{n_trains} đoàn tàu đã chọn"
            + ("" if n_trains else " — vui lòng import HSLM/LM71/real từ Excel"),
        ),
    )

    # result stations
    n_stations = len(project.result_stations)
    rows.append(
        CheckRow(
            "Result stations",
            "PASS" if n_stations > 0 else "FAIL",
            f"{n_stations} vị trí xuất kết quả",
        ),
    )

    ok = all(r.status == "PASS" for r in rows)
    return ok, rows


def _check_bridge(project: Project, folder: Path, rows: list[CheckRow]) -> bool:
    bridge = project.bridge
    n_nodes = len(bridge.nodes)
    n_elem = len(bridge.elements)
    n_mat = len(bridge.materials)
    n_sect = len(bridge.sections)
    rows.append(
        CheckRow(
            "Bridge tổng quan",
            "PASS",
            f"{n_nodes} nodes, {n_elem} elements, {n_mat} materials, {n_sect} sections",
        ),
    )

    # supports
    if not bridge.supports:
        rows.append(CheckRow("Supports", "FAIL", "Không có support — model không ổn định"))
        return False
    rows.append(CheckRow("Supports", "PASS", f"{len(bridge.supports)} gối tựa"))
    return True
