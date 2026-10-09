"""Midas Civil tendon MCT blocks."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from vbridge_dyn.core.schemas.bridge import Bridge
from vbridge_dyn.core.schemas.project import Project
from vbridge_dyn.core.schemas.tendon import PrestressConfig, TendonPropertyConfig
from vbridge_dyn.importers.dxf.tendon_reader import DxfTendonError, read_tendon_dxf


@dataclass(frozen=True)
class _TendonProfileRecord:
    name: str
    property_name: str
    element_ids: list[int]
    group_name: str
    ref_element_id: int
    points: list[tuple[float, float, float]]


def build_tendon_mct_lines(
    project: Project,
    *,
    project_folder: Path | None,
    tendon_material_id: int,
    warnings: list[str],
) -> list[str]:
    """Build Midas tendon blocks for an enabled prestress configuration."""
    config = project.prestress
    if not config.enabled:
        return []
    if config.dxf is None:
        warnings.append("Prestress enabled nhưng chưa khai báo prestress.dxf; bỏ qua tendon.")
        return []
    if config.load is None:
        warnings.append("Prestress enabled nhưng chưa khai báo prestress.load; bỏ qua tendon load.")
        return []
    if not config.properties:
        warnings.append(
            "Prestress enabled nhưng chưa khai báo prestress.properties; bỏ qua tendon."
        )
        return []
    if project_folder is None:
        warnings.append("Prestress DXF dùng path tương đối nhưng writer không biết project_folder.")
        return []

    dxf_path = project_folder / config.dxf.file
    try:
        dxf_data = read_tendon_dxf(
            dxf_path,
            layer_regex=config.dxf.layer_regex,
            mirror_half_span=config.dxf.mirror_half_span,
        )
    except DxfTendonError as exc:
        warnings.append(str(exc))
        return []

    properties_by_name = {item.name: item for item in config.properties}
    if config.dxf.property not in properties_by_name:
        warnings.append(
            f"Prestress DXF property='{config.dxf.property}' không có trong prestress.properties."
        )
        return []

    span_groups = _span_groups(project.bridge, config.dxf.span_group_regex)
    if not span_groups:
        warnings.append(
            f"Không tìm thấy structure group khớp {config.dxf.span_group_regex!r}; bỏ qua tendon."
        )
        return []

    profiles: list[_TendonProfileRecord] = []
    for span_index, (group_name, element_ids) in enumerate(span_groups, start=1):
        for dxf_profile in dxf_data.profiles:
            name = config.dxf.profile_name_template.format(
                span=span_index,
                group=group_name,
                layer=dxf_profile.layer,
            )
            profiles.append(
                _TendonProfileRecord(
                    name=_midas_name(name, limit=32),
                    property_name=config.dxf.property,
                    element_ids=element_ids,
                    group_name=config.dxf.tendon_group,
                    ref_element_id=element_ids[0],
                    points=dxf_profile.points_3d,
                )
            )

    lines: list[str] = []
    lines.extend(_emit_load_group(config.dxf.load_group))
    lines.extend(_emit_tendon_group(config.dxf.tendon_group))
    lines.extend(_emit_tendon_properties(config, tendon_material_id))
    lines.extend(_emit_tendon_profiles(profiles, curve=config.dxf.curve))
    lines.extend(_emit_prestress_loadcase(config, profiles))
    warnings.append(
        f"Đã sinh {len(profiles)} tendon profiles từ {dxf_path.name} "
        f"({len(dxf_data.profiles)} layer CAD × {len(span_groups)} girder groups)."
    )
    return lines


def _span_groups(bridge: Bridge, pattern: str) -> list[tuple[str, list[int]]]:
    regex = re.compile(pattern)
    records: dict[str, set[int]] = {}

    for group in bridge.structure_groups:
        name = group.name or group.id
        if regex.match(name) or regex.match(group.id):
            records.setdefault(name, set()).update(group.element_ids)

    for element in bridge.elements:
        if element.structure_group and regex.match(element.structure_group):
            records.setdefault(element.structure_group, set()).add(element.id)

    out = [(name, sorted(element_ids)) for name, element_ids in records.items() if element_ids]
    return sorted(out, key=lambda item: _natural_group_key(item[0]))


def _emit_load_group(name: str) -> list[str]:
    return ["*LOAD-GROUP    ; Load Group", "; NAME", f" {_text(name)}", ""]


def _emit_tendon_group(name: str) -> list[str]:
    return ["*TENDON-GROUP    ; Tendon Group", "; NAME", f" {_text(name)}", ""]


def _emit_tendon_properties(config: PrestressConfig, material_id: int) -> list[str]:
    lines = [
        "*TDN-PROPERTY    ; Tendon Property",
        "; NAME, TYPE, MATL, AREA, DIA, RM, RC, FF, WF, US, YS, LT, ASB, ASE, bBONDED, ...",
    ]
    for item in config.properties:
        lines.append(_tendon_property_line(item, material_id))
    lines.append("")
    return lines


def _tendon_property_line(item: TendonPropertyConfig, material_id: int) -> str:
    bonded = "YES" if item.bonded else "NO"
    return (
        f"   {_text(item.name)}, INTERNAL, {material_id}, {_num(item.area)}, "
        f"{_num(item.duct_diameter)}, {_num(item.relaxation_method)}, "
        f"{_num(item.relaxation_coefficient)}, {_num(item.friction)}, {_num(item.wobble)}, "
        f"{_num(item.ultimate_strength)}, {_num(item.yield_strength)}, POST, "
        f"{_num(item.anchor_slip_begin)}, {_num(item.anchor_slip_end)}, {bonded}, "
        f"0, , , ,, 0, YES, 0, 0, {_num(item.angle_disp)}"
    )


def _emit_tendon_profiles(profiles: list[_TendonProfileRecord], *, curve: str) -> list[str]:
    lines = [
        f"*TDN-PROFILE   ; Tendon Profile ({curve} 3D)",
        f"; NAME, PROP, ELEMS, 0, 0, {curve}, 3D / GROUP,.. / REFERENCE AXIS",
    ]
    for profile in profiles:
        lines.append(
            f"   NAME={profile.name}, {profile.property_name}, "
            f"{_mct_id_list(profile.element_ids)}, 0, 0, {curve}, 3D"
        )
        lines.append(f"        {profile.group_name}, USER, 0, 0, NO, , 0, 0")
        lines.append(f"        ELEMENT, END-I, {profile.ref_element_id}, I-J")
        lines.append("        0, YES, 0, 0")
        for x, y, z in profile.points:
            lines.append(f"        {_num(x)}, {_num(y)}, {_num(z)}, NO, 0, 0, 0")
    lines.append("")
    return lines


def _emit_prestress_loadcase(
    config: PrestressConfig,
    profiles: list[_TendonProfileRecord],
) -> list[str]:
    assert config.dxf is not None
    assert config.load is not None
    lines = [
        "*STLDCASE    ; Static Load Cases",
        "; LCNAME, LCTYPE, DESC",
        f"   {_text(config.dxf.load_case)}, PS, ",
        "",
        f"*USE-STLD, {_text(config.dxf.load_case)}",
        "",
        "*TDN-PRESTRESS    ; Tendon Prestress Loads",
        "; TDN-NAME, FORCE/STRESS, JACKING, BEGIN, END, iGROUTING, GROUP",
    ]
    for profile in profiles:
        lines.append(
            f" {profile.name}, {config.load.type}, {config.load.jacking}, "
            f"{_num(config.load.begin)}, {_num(config.load.end)}, 1, {_text(config.dxf.load_group)}"
        )
    lines.extend(
        [
            "",
            f"; End of data for load case [{_text(config.dxf.load_case)}] -------------------------",
            "",
        ]
    )
    return lines


def tendon_material_line(project: Project, material_id: int) -> str:
    """Midas `*MATERIAL` line for prestressing strand."""
    material = project.prestress.material
    return (
        f" {material_id:>4}, USER , {_midas_name(material.name, limit=16):<16}, 0, 0, , C, NO, "
        f"{_num(material.damping_ratio)}, 2, {_num(material.elastic_modulus)}, "
        f"{_num(material.poisson)}, {_num(material.thermal)}, {_num(material.unit_weight)}, 0"
    )


def has_tendon_material(project: Project) -> bool:
    return project.prestress.enabled and bool(project.prestress.properties)


def tendon_material_id(project: Project, bridge_material_count: int) -> int | None:
    if not has_tendon_material(project):
        return None
    return bridge_material_count + 1


def _mct_id_list(values: list[int]) -> str:
    if not values:
        return ""
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return str(sorted_values[0])
    step = sorted_values[1] - sorted_values[0]
    if step > 0 and all(
        sorted_values[i] - sorted_values[i - 1] == step for i in range(1, len(sorted_values))
    ):
        if step == 1:
            return f"{sorted_values[0]}to{sorted_values[-1]}"
        return f"{sorted_values[0]}to{sorted_values[-1]}by{step}"
    return " ".join(str(value) for value in sorted_values)


def _num(value: float) -> str:
    return f"{value:.10g}"


def _text(value: str) -> str:
    return value.replace(",", " ").strip()


def _midas_name(value: str, *, limit: int) -> str:
    normalized = unicodedata.normalize("NFKD", _text(value))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = " ".join(ascii_text.split())
    if not cleaned:
        cleaned = "Unnamed"
    return cleaned[:limit]


def _natural_group_key(value: str) -> tuple[str, int, str]:
    match = re.search(r"(\d+)$", value)
    if match:
        return (value[: match.start()], int(match.group(1)), value)
    return (value, 0, value)
