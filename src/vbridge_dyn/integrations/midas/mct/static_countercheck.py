"""Static report countercheck MCT generation."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

from vbridge_dyn.core.schemas.boundary import Support
from vbridge_dyn.core.schemas.bridge import Bridge
from vbridge_dyn.core.schemas.geometry import Element, Node
from vbridge_dyn.core.schemas.groups import BoundaryGroup, LoadGroup, StructureGroup
from vbridge_dyn.core.schemas.project import Project
from vbridge_dyn.core.schemas.track import Track
from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct
from vbridge_dyn.io.project_io import load_project_folder


@dataclass(frozen=True)
class StaticCountercheckResult:
    mct_path: Path
    warnings: list[str]
    lm71_start_m: float | None
    transport_start_m: float


@dataclass(frozen=True)
class _Span:
    name: str
    index: int
    source_elements: list[Element]
    support_i_x: float
    support_j_x: float
    start_x: float
    end_x: float
    y: float
    z: float

    @property
    def span_length(self) -> float:
        return self.support_j_x - self.support_i_x


@dataclass(frozen=True)
class _TrainPosition:
    start: float
    axles: list[float]
    udl_intervals: list[tuple[float, float]]


def generate_bxd_32_6_static_countercheck(
    project_folder: Path,
    *,
    output_path: Path | None = None,
    config_path: Path | None = None,
) -> StaticCountercheckResult:
    """Generate a girder-only static MCT for the BXD 32.6 m report countercheck."""
    project = load_project_folder(project_folder)
    config_path = config_path or project_folder / "static_countercheck_32_6.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    spans = _girder_spans(project.bridge)
    span_length = float(config["calculation_span_m"])
    transport = _critical_axle_position(span_length, config["loads"]["transport"])
    split_offsets = _countercheck_split_offsets(config, transport)

    top_bridge = _build_top_only_bridge(project.bridge, spans, split_offsets, config)
    top_project = project.model_copy(update={"bridge": top_bridge}, deep=True)

    output_path = (
        output_path or project_folder / "generated" / "midas" / "model_static_countercheck_32_6.mct"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    warnings = write_base_model_mct(top_project, output_path, project_folder=project_folder)

    report_lines = _report_static_load_lines(top_project.bridge, spans, config, transport)
    report_lines.extend(_construction_stage_lines(top_project.bridge, top_project, config))
    report_lines.extend(_lm71_moving_load_lines(top_project.bridge, top_project.tracks, config))
    report_lines.extend(_load_combination_lines(config))
    text = output_path.read_text(encoding="utf-8")
    output_path.write_text(_insert_before(text, "*EIGEN-CTRL", report_lines), encoding="utf-8")
    warnings.append(
        "Static countercheck: dầm-only model, gối tại node thứ 2/áp chót của mỗi Girder, "
        "khóa thêm RX tại gối để ổn định mô hình beam 3D độc lập, "
        "G1 dùng MIDAS *SELFWEIGHT/SelfWeight, LM71 dùng static moving load EUROCODE; "
        "Phi trong LM71_2T_PHI là hệ số động tĩnh, không phải time-history dynamic; "
        "CS lưu các mốc 3 ngày, 36 ngày và 100 năm để đối chiếu độ vồng/võng; "
        "split node chỉ phục vụ tải trục xe vận chuyển từ báo cáo."
    )
    return StaticCountercheckResult(
        mct_path=output_path,
        warnings=warnings,
        lm71_start_m=None,
        transport_start_m=transport.start,
    )


def _girder_spans(bridge: Bridge) -> list[_Span]:
    nodes_by_id = {node.id: node for node in bridge.nodes}
    elements_by_id = {element.id: element for element in bridge.elements}
    spans: list[_Span] = []
    for group in bridge.structure_groups:
        name = group.name or group.id
        if not name.startswith("Girder"):
            continue
        source_elements = [
            elements_by_id[eid] for eid in group.element_ids if eid in elements_by_id
        ]
        if not source_elements:
            continue
        node_ids = sorted(
            {element.n1 for element in source_elements}
            | {element.n2 for element in source_elements},
            key=lambda node_id: nodes_by_id[node_id].x,
        )
        if len(node_ids) < 4:
            continue
        start_node = nodes_by_id[node_ids[0]]
        support_i = nodes_by_id[node_ids[1]]
        support_j = nodes_by_id[node_ids[-2]]
        end_node = nodes_by_id[node_ids[-1]]
        spans.append(
            _Span(
                name=name,
                index=len(spans) + 1,
                source_elements=sorted(
                    source_elements,
                    key=lambda element: min(nodes_by_id[element.n1].x, nodes_by_id[element.n2].x),
                ),
                support_i_x=support_i.x,
                support_j_x=support_j.x,
                start_x=start_node.x,
                end_x=end_node.x,
                y=support_i.y,
                z=support_i.z,
            )
        )
    return spans


def _countercheck_split_offsets(
    config: dict[str, Any],
    transport: _TrainPosition,
) -> list[float]:
    span_length = float(config["calculation_span_m"])
    offsets = {0.0, span_length}
    offsets.update(x for x in transport.axles if 0.0 <= x <= span_length)
    return sorted(offsets)


def _build_top_only_bridge(
    source: Bridge,
    spans: list[_Span],
    split_offsets: list[float],
    config: dict[str, Any],
) -> Bridge:
    source_nodes = {node.id: node for node in source.nodes}
    report_e = float(config["concrete"]["elastic_modulus_mpa"]) * 1e6
    report_rho = float(config["concrete"]["unit_weight_kn_m3"]) * 1000.0 / 9.806

    used_section_ids: set[str] = set()
    new_nodes: list[Node] = []
    new_elements: list[Element] = []
    groups: list[StructureGroup] = []
    supports: list[Support] = []
    support_group = str(
        config.get("construction_stages", {}).get("support_boundary_group", "Support")
    )

    for span in spans:
        span_positions = {span.start_x, span.support_i_x, span.support_j_x, span.end_x}
        span_positions.update(span.support_i_x + offset for offset in split_offsets)
        for element in span.source_elements:
            span_positions.add(source_nodes[element.n1].x)
            span_positions.add(source_nodes[element.n2].x)
        ordered = sorted(
            {_clean_x(x) for x in span_positions if span.start_x - 1e-8 <= x <= span.end_x + 1e-8}
        )

        node_id_by_x: dict[float, int] = {}
        for idx, x in enumerate(ordered, start=1):
            node_id = span.index * 100000 + idx
            node_id_by_x[x] = node_id
            new_nodes.append(Node(id=node_id, x=x, y=span.y, z=span.z))

        element_ids: list[int] = []
        for idx, (x1, x2) in enumerate(pairwise(ordered), start=1):
            if x2 - x1 <= 1e-8:
                continue
            section_id = _section_at_x(span, source_nodes, (x1 + x2) / 2.0)
            used_section_ids.add(section_id)
            element_id = span.index * 100000 + idx
            element_ids.append(element_id)
            new_elements.append(
                Element(
                    id=element_id,
                    type="BEAM",
                    n1=node_id_by_x[x1],
                    n2=node_id_by_x[x2],
                    material_id="C50",
                    section_id=section_id,
                    structure_group=span.name,
                )
            )

        groups.append(StructureGroup(id=span.name, name=span.name, element_ids=element_ids))
        supports.append(
            Support(
                node_id=node_id_by_x[_clean_x(span.support_i_x)],
                constraint=[1, 1, 1, 1, 0, 0],
                boundary_group=support_group,
            )
        )
        supports.append(
            Support(
                node_id=node_id_by_x[_clean_x(span.support_j_x)],
                constraint=[0, 1, 1, 1, 0, 0],
                boundary_group=support_group,
            )
        )

    sections_by_id = {section.id: section for section in source.sections}
    expanded_section_ids = set(used_section_ids)
    for section_id in list(used_section_ids):
        section = sections_by_id[section_id]
        if section.taper_start_section_id:
            expanded_section_ids.add(section.taper_start_section_id)
        if section.taper_end_section_id:
            expanded_section_ids.add(section.taper_end_section_id)
    new_sections = [
        sections_by_id[section.id]
        for section in source.sections
        if section.id in expanded_section_ids
    ]
    c50 = next(material for material in source.materials if material.id == "C50")
    new_materials = [
        c50.model_copy(
            update={
                "E": report_e,
                "rho": report_rho,
                "name": "Concrete C50/60",
                "grade": "C50",
            }
        )
    ]
    g2_group = str(config.get("construction_stages", {}).get("g2_load_group", "G2-BXD"))
    return Bridge(
        units=source.units,
        nodes=new_nodes,
        elements=new_elements,
        materials=new_materials,
        sections=new_sections,
        supports=supports,
        structure_groups=groups,
        boundary_groups=[BoundaryGroup(id=support_group, name=support_group)],
        load_groups=[
            LoadGroup(id=g2_group, name=g2_group),
        ],
    )


def _section_at_x(span: _Span, nodes_by_id: dict[int, Node], x: float) -> str:
    for element in span.source_elements:
        x1 = nodes_by_id[element.n1].x
        x2 = nodes_by_id[element.n2].x
        if min(x1, x2) - 1e-8 <= x <= max(x1, x2) + 1e-8:
            return element.section_id
    return span.source_elements[-1].section_id


def _critical_lm71_position(span_length: float, config: dict[str, Any]) -> _TrainPosition:
    axle_count = int(config["axle_count"])
    spacing = float(config["axle_spacing_m"])
    exclusion = float(config["udl_exclusion_each_side_m"])
    axle_load = float(config["axle_load_kn"]) * float(config["alpha"]) * int(config["lane_count"])
    udl_load = float(config["udl_kn_per_m"]) * float(config["alpha"]) * int(config["lane_count"])
    best_start = 0.0
    best_value = -1.0
    search_start = -spacing * (axle_count - 1) - exclusion
    search_end = span_length + exclusion
    step = 0.01
    n = int((search_end - search_start) / step) + 1
    for i in range(n + 1):
        start = search_start + i * step
        axles = [start + k * spacing for k in range(axle_count)]
        blocked = (axles[0] - exclusion, axles[-1] + exclusion)
        udl_intervals = _remaining_intervals(span_length, blocked)
        value = axle_load * sum(
            _midspan_influence(span_length, x) for x in axles if 0.0 <= x <= span_length
        )
        value += udl_load * sum(_midspan_udl_integral(span_length, a, b) for a, b in udl_intervals)
        if value > best_value:
            best_value = value
            best_start = start
    best_axles = [best_start + k * spacing for k in range(axle_count)]
    return _TrainPosition(
        start=best_start,
        axles=best_axles,
        udl_intervals=_remaining_intervals(
            span_length, (best_axles[0] - exclusion, best_axles[-1] + exclusion)
        ),
    )


def _critical_axle_position(span_length: float, config: dict[str, Any]) -> _TrainPosition:
    axle_count = int(config["axle_count"])
    spacing = float(config["axle_spacing_m"])
    train_length = spacing * (axle_count - 1)
    best_start = 0.0
    best_value = -1.0
    step = 0.01
    search_start = -train_length
    search_end = span_length
    n = int((search_end - search_start) / step) + 1
    for i in range(n + 1):
        start = search_start + i * step
        axles = [start + k * spacing for k in range(axle_count)]
        value = sum(_midspan_influence(span_length, x) for x in axles if 0.0 <= x <= span_length)
        if value > best_value:
            best_value = value
            best_start = start
    return _TrainPosition(
        start=best_start,
        axles=[best_start + k * spacing for k in range(axle_count)],
        udl_intervals=[],
    )


def _remaining_intervals(
    span_length: float, blocked: tuple[float, float]
) -> list[tuple[float, float]]:
    left = max(0.0, blocked[0])
    right = min(span_length, blocked[1])
    intervals: list[tuple[float, float]] = []
    if left > 0.0:
        intervals.append((0.0, left))
    if right < span_length:
        intervals.append((right, span_length))
    return intervals


def _midspan_influence(span_length: float, x: float) -> float:
    if x < 0.0 or x > span_length:
        return 0.0
    mid = span_length / 2.0
    return (
        x * (span_length - mid) / span_length if x <= mid else mid * (span_length - x) / span_length
    )


def _midspan_udl_integral(span_length: float, a: float, b: float) -> float:
    a = max(0.0, min(span_length, a))
    b = max(0.0, min(span_length, b))
    if b <= a:
        return 0.0
    mid = span_length / 2.0

    def left_int(x: float) -> float:
        return x * x / 4.0

    def right_int(x: float) -> float:
        return mid * x - mid * x * x / (2.0 * span_length)

    total = 0.0
    if a < mid:
        total += left_int(min(b, mid)) - left_int(a)
    if b > mid:
        total += right_int(b) - right_int(max(a, mid))
    return total


def _report_static_load_lines(
    bridge: Bridge,
    spans: list[_Span],
    config: dict[str, Any],
    transport: _TrainPosition,
) -> list[str]:
    loads = config["loads"]
    transport_cfg = loads["transport"]
    wind_cfg = loads["wind"]
    transport_axle = float(transport_cfg["axle_load_kn"])
    transport_phi = float(transport_cfg["dynamic_factor"])
    wind_q = float(wind_cfg["total_transverse_kn"]) / float(config["calculation_span_m"])

    cases = [
        ("G2_REPORT", "D", "Report superimposed dead load 106.75 kN/m"),
        ("TRANSPORT", "D", "18 axles x 611 kN critical for midspan moment"),
        ("TRANSPORT_DYN", "D", "TRANSPORT with construction dynamic factor 1.10"),
        ("WIND_Y_REPORT", "D", "Report transverse wind total 634 kN"),
    ]
    lines = [
        "",
        "; Static countercheck load cases from BXD report",
        "; G1/self weight is the base SW case generated from MIDAS geometry/material unit weight.",
        "*STLDCASE    ; Static Load Cases",
        "; LCNAME, LCTYPE, DESC",
    ]
    lines.extend(f"   {name}, {kind} , {desc}" for name, kind, desc in cases)
    lines.append("")
    stage_cfg = config.get("construction_stages", {})
    g2_group = str(stage_cfg.get("g2_load_group", "G2-BXD"))
    lines.extend(
        _uniform_load_case(
            bridge,
            "G2_REPORT",
            "GZ",
            -float(loads["g2_superimposed_dead_kn_per_m"]),
            spans,
            [(0.0, float(config["calculation_span_m"]))],
            group=g2_group,
        )
    )
    lines.extend(_axle_case(bridge, "TRANSPORT", spans, transport, -transport_axle))
    lines.extend(
        _axle_case(bridge, "TRANSPORT_DYN", spans, transport, -transport_axle * transport_phi)
    )
    lines.extend(
        _uniform_load_case(
            bridge,
            "WIND_Y_REPORT",
            "GY",
            wind_q,
            spans,
            [(0.0, float(config["calculation_span_m"]))],
        )
    )
    return lines


def _lm71_moving_load_lines(
    bridge: Bridge, tracks: list[Track], config: dict[str, Any]
) -> list[str]:
    lm71_cfg = config["loads"]["lm71"]
    lane_count = int(lm71_cfg["lane_count"])
    lane_tracks = tracks[:lane_count]
    if len(lane_tracks) < lane_count:
        lane_tracks = [
            Track(id=f"T{i}", name=f"Track {i}", centerline_y=offset)
            for i, offset in enumerate(lm71_cfg.get("lane_offsets_m", [0.0] * lane_count), start=1)
        ]

    lane_names = [track.id for track in lane_tracks]
    lane_width = float(lm71_cfg.get("lane_width_m", 1.435))
    alpha = float(lm71_cfg["alpha"])
    phi = float(lm71_cfg["dynamic_factor_phi"])
    fatigue_alpha = float(lm71_cfg.get("fatigue_alpha", 1.0))
    fatigue_phi = phi if bool(lm71_cfg.get("fatigue_include_dynamic_factor", True)) else 1.0
    element_ids = sorted(element.id for element in bridge.elements)
    lines = [
        "",
        "; MIDAS built-in Eurocode railway static moving load for report LM71 countercheck",
        "; Note: LM71_2T_PHI uses a static dynamic factor Phi, not time-history analysis.",
        "; EN fatigue uses a separate LM71 vehicle with alpha=1.0; lambda is applied in LOADCOMB.",
        "*MVLDCODE    ; Moving Load Code",
        "; CODE=CODE",
        "   CODE=EUROCODE",
        "",
        "*LINELANE    ; Traffic Line Lanes",
        "; NAME=NAME, LDIST, GROUP, SKEWS, SKEWE, MOVING, LW, WS, bLANEOPT, ALLOWWIDTH",
        ";      iELEM1, ECC1, FACT1, bSPAN1, ECCVL, CENTF",
    ]
    for track in lane_tracks:
        lines.append(
            f"   NAME={_midas_token(track.id)}, LANE, , 0, 0, BOTH, {_num(lane_width)}, 0, NO, 0"
        )
        entries = [
            f"{element_id}, {_num(track.centerline_y)}, 0, NO, 0, 0.5" for element_id in element_ids
        ]
        for chunk in _chunks(entries, 2):
            lines.append("        " + ",   ".join(chunk))
    lines.extend(
        [
            "",
            "*VEHICLE    ; Vehicles",
            "; Eurocode railway DB vehicle name must match MIDAS built-in naming.",
            "; The value after the LM71 load data is the EN 1991-2 adjustment factor alpha.",
            f"   NAME=Load Model 71, 1, 5, Load Model 71, 80, 0, 0.8, 80, 0, 0.8, {_num(alpha)}, NO, 0.75, NO, 0",
            f"   NAME=Load Model 71 Fatigue, 1, 5, Load Model 71, 80, 0, 0.8, 80, 0, 0.8, {_num(fatigue_alpha)}, NO, 0.75, NO, 0",
            "",
            "*MVLDCASE(EURO)   ; Moving Load Cases",
            "; NAME=NAME, bOPTIM, iTYPE, DESC, iOPT, SF1, SF2, SF3, bPSI1, MULF1, MULF2, MULF3, SERIAL",
            "   NAME=LM71_2T, NO, 5, , 1, 0.8, 0.7, 0.6, YES, 1, 1, 0.75, 0",
            f"        Load Model 71, 1, 0, {len(lane_names)}, {', '.join(_midas_token(name) for name in lane_names)}",
            "   NAME=LM71_2T_PHI, NO, 5, , 1, 0.8, 0.7, 0.6, YES, 1, 1, 0.75, 0",
            f"        Load Model 71, {_num(phi)}, 0, {len(lane_names)}, {', '.join(_midas_token(name) for name in lane_names)}",
            "   NAME=LM71_FAT_2T, NO, 5, , 1, 0.8, 0.7, 0.6, YES, 1, 1, 0.75, 0",
            f"        Load Model 71 Fatigue, 1, 0, {len(lane_names)}, {', '.join(_midas_token(name) for name in lane_names)}",
            "   NAME=LM71_FAT_2T_PHI, NO, 5, , 1, 0.8, 0.7, 0.6, YES, 1, 1, 0.75, 0",
            f"        Load Model 71 Fatigue, {_num(fatigue_phi)}, 0, {len(lane_names)}, {', '.join(_midas_token(name) for name in lane_names)}",
            "",
        ]
    )
    return lines


def _construction_stage_lines(
    bridge: Bridge,
    project: Project,
    config: dict[str, Any],
) -> list[str]:
    stage_cfg = config.get("construction_stages", {})
    if not stage_cfg.get("enabled", True):
        return []

    girder_groups = [
        group.name or group.id
        for group in sorted(bridge.structure_groups, key=lambda item: item.name or item.id)
        if (group.name or group.id).startswith("Girder")
    ]
    if not girder_groups:
        return []

    tdm_cfg = project.targets.midas_civil.time_dependent_concrete
    prestress_age = float(
        stage_cfg.get(
            "prestress_age_days",
            stage_cfg.get("girder_age_days_at_activation", tdm_cfg.age_days),
        )
    )
    g2_age = float(stage_cfg.get("g2_application_age_days", 36))
    long_term_age = float(stage_cfg.get("long_term_age_days", 36500))
    stage_to_g2_duration = max(g2_age - prestress_age, 0)
    long_term_duration = max(long_term_age - g2_age, 0)
    long_term_steps = stage_cfg.get("long_term_steps_after_g2_days", [365, 3650, 10000])
    support_group = str(stage_cfg.get("support_boundary_group", "Support"))
    self_weight_group = str(stage_cfg.get("self_weight_load_group", "SelfWeight"))
    g2_group = str(stage_cfg.get("g2_load_group", "G2-BXD"))
    prestress_group = str(project.prestress.dxf.load_group if project.prestress.dxf else "PS-BXD")

    lines = [
        "",
        "; BXD girder construction stages for report camber milestones: 3d, 36d, 100y",
        "*STAGE    ; Define Construction Stage",
        "; NAME=NAME, DURATION, bSAVESTAGE, bSAVESTEP, bINCRESTEP, INCRESTEP",
        "; STEP / AELEM=grp,age,.. / ABNDR=bgrp,pos,.. / ALOAD=grp,day,..",
        "  NAME=CS1_Prestress_3d, 0, YES, YES, NO, 5",
    ]
    lines.append(
        "  AELEM="
        + ", ".join(f"{_midas_token(group)}, {_num(prestress_age)}" for group in girder_groups)
    )
    lines.append(f"  ABNDR={_midas_token(support_group)}, ORIGINAL")
    lines.append(
        "  ALOAD="
        + ", ".join(
            [
                f"{_midas_token(self_weight_group)}, FIRST",
                f"{_midas_token(prestress_group)}, FIRST",
            ]
        )
    )
    lines.append(f"  NAME=CS2_G2_36d, {_num(stage_to_g2_duration)}, YES, YES, NO, 5")
    lines.append(f"  ALOAD={_midas_token(g2_group)}, LAST")
    lines.append(f"  NAME=CS3_LongTerm_100y, {_num(long_term_duration)}, YES, YES, NO, 5")
    valid_long_term_steps = [
        float(value) for value in long_term_steps if 0 < float(value) < long_term_duration
    ]
    if valid_long_term_steps:
        lines.append("  STEP=" + ", ".join(_num(value) for value in valid_long_term_steps))
    lines.extend(
        [
            "",
            "*STAGE-CTRL    ; Construction Stage Analysis Control Data",
            "; Values follow local Modeling_auto_Midas FCM stage-control template.",
            "  YES, , INTERNAL, NO, NO, YES, NO, NO, NO, NO, NO, , , YES, NO, , NO, NO, NO",
            "  0",
            "  NO",
            "  YES, YES, BOTH, 5, 0.01, YES, NO, YES, YES, 0, NO",
            "  NO, NO, 2, YES, 2, 5, 7, 10, 20",
            "  NO, , , 1, NO",
            "",
        ]
    )
    return lines


def _load_combination_lines(config: dict[str, Any]) -> list[str]:
    combinations = config.get("load_combinations") or []
    if not combinations:
        return []
    fatigue_lambda = float(
        config.get("loads", {}).get("lm71", {}).get("fatigue_damage_lambda", 1.04)
    )
    lines = [
        "",
        "; Load combinations from BXD report factors",
        "*LOADCOMB    ; Combinations",
        "; NAME=NAME, KIND, ACTIVE, bES, iTYPE, DESC, iSERV-TYPE, nLCOMTYPE, nSEISTYPE",
        "; ANAL, LCNAME, FACT, ...",
    ]
    for combo in combinations:
        raw_name = str(combo["name"])
        name = _midas_token(str(combo["name"]))
        desc = _midas_token(str(combo.get("desc", "")))
        lines.append(f"   NAME={name}, GEN, ACTIVE, 0, 0, {desc}, 0, 0, 0")
        terms = combo.get("terms", [])
        for i in range(0, len(terms), 3):
            chunk = terms[i : i + 3]
            lines.append(
                "        "
                + ", ".join(
                    f"{_midas_token(str(analysis))}, {_midas_token(str(case))}, "
                    f"{_num(fatigue_lambda if raw_name == 'FATIGUE_LM71_EN' and case == 'LM71_FAT_2T_PHI' else float(factor))}"
                    for analysis, case, factor in chunk
                )
            )
    lines.append("")
    return lines


def _uniform_load_case(
    bridge: Bridge,
    name: str,
    direction: str,
    load_value: float,
    spans: list[_Span],
    intervals: list[tuple[float, float]],
    *,
    group: str = "",
) -> list[str]:
    lines = [
        f"*USE-STLD, {name}",
        "",
        "*BEAMLOAD    ; Element Beam Loads",
        "; ELEM_LIST, CMD, TYPE, DIR, bPROJ, [ECCEN], [VALUE], GROUP",
    ]
    element_by_id = {element.id: element for element in bridge.elements}
    node_by_id = {node.id: node for node in bridge.nodes}
    for span in spans:
        element_ids = next(
            group.element_ids for group in bridge.structure_groups if group.name == span.name
        )
        for element_id in element_ids:
            element = element_by_id[element_id]
            x1 = node_by_id[element.n1].x
            x2 = node_by_id[element.n2].x
            length = x2 - x1
            for a, b in intervals:
                start = span.support_i_x + a
                end = span.support_i_x + b
                overlap_start = max(x1, start)
                overlap_end = min(x2, end)
                if overlap_end - overlap_start <= 1e-8:
                    continue
                d1 = (overlap_start - x1) / length
                d2 = (overlap_end - x1) / length
                lines.append(_beamload_line(element_id, direction, load_value, d1, d2, group))
    lines.extend(["", f"; End of data for load case [{name}] -------------------------", ""])
    return lines


def _lm71_case(
    bridge: Bridge,
    name: str,
    spans: list[_Span],
    position: _TrainPosition,
    axle_load: float,
    udl_load: float,
) -> list[str]:
    lines = _uniform_load_case(bridge, name, "GZ", udl_load, spans, position.udl_intervals)
    conload = _axle_conload_lines(bridge, spans, position.axles, axle_load)
    insert_at = lines.index("") + 1
    return lines[:insert_at] + conload + lines[insert_at:]


def _axle_case(
    bridge: Bridge,
    name: str,
    spans: list[_Span],
    position: _TrainPosition,
    axle_load: float,
) -> list[str]:
    lines = [f"*USE-STLD, {name}", ""]
    lines.extend(_axle_conload_lines(bridge, spans, position.axles, axle_load))
    lines.extend(["", f"; End of data for load case [{name}] -------------------------", ""])
    return lines


def _axle_conload_lines(
    bridge: Bridge,
    spans: list[_Span],
    axle_offsets: list[float],
    axle_load: float,
) -> list[str]:
    node_by_x = {
        (round(node.x, 6), round(node.y, 6), round(node.z, 6)): node.id for node in bridge.nodes
    }
    lines = ["*CONLOAD    ; Nodal Loads", "; NODE_LIST, FX, FY, FZ, MX, MY, MZ, GROUP"]
    for span in spans:
        for offset in axle_offsets:
            if offset < -1e-8 or offset > span.span_length + 1e-8:
                continue
            key = (round(span.support_i_x + offset, 6), round(span.y, 6), round(span.z, 6))
            node_id = node_by_x.get(key)
            if node_id is not None:
                lines.append(f"   {node_id}, 0, 0, {_num(axle_load)}, 0, 0, 0, ")
    lines.append("")
    return lines


def _beamload_line(
    element_id: int,
    direction: str,
    load: float,
    d1: float,
    d2: float,
    group: str = "",
) -> str:
    return (
        f"   {element_id}, BEAM   , UNILOAD, {direction}, NO , NO, aDir[1], , , , "
        f"{_num(d1)}, {_num(load)}, {_num(d2)}, {_num(load)}, 0, 0, 0, 0, "
        f"{_midas_token(group)}, NO, 0, 0, NO, "
    )


def _insert_before(text: str, marker: str, lines: list[str]) -> str:
    block = "\n".join(lines).rstrip() + "\n\n"
    idx = text.find(marker)
    if idx < 0:
        return text.rstrip() + "\n\n" + block
    return text[:idx] + block + text[idx:]


def _clean_x(value: float) -> float:
    return round(value, 6)


def _num(value: float) -> str:
    return f"{value:.10g}"


def _midas_token(value: str) -> str:
    return value.replace(",", " ").strip()


def _chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[5]
    result = generate_bxd_32_6_static_countercheck(root / "examples" / "bxd")
    print(result.mct_path)
    print("LM71 = MIDAS EUROCODE moving load")
    print(f"Transport start = {result.transport_start_m:.3f} m")
    for warning in result.warnings:
        print("WARN", warning)
