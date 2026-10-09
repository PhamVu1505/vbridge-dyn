"""Dynamic report countercheck MCT generation for the BXD 32.6 m girder."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

from vbridge_dyn.core.schemas.bridge import Bridge
from vbridge_dyn.integrations.midas.mct.static_countercheck import (
    _build_top_only_bridge,
    _countercheck_split_offsets,
    _critical_axle_position,
    _girder_spans,
    _insert_before,
    _midas_token,
    _num,
    _uniform_load_case,
)
from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct
from vbridge_dyn.io.project_io import load_project_folder


@dataclass(frozen=True)
class DynamicCountercheckResult:
    """Output bundle for the BXD dynamic countercheck model."""

    mct_path: Path
    warnings: list[str]
    case_name: str
    train_id: str
    velocity_kmh: float
    include_prestress: bool
    graph_node_id: int
    loaded_node_count: int
    function_count: int
    duration_s: float
    bridge_length_m: float


@dataclass(frozen=True)
class _LoadPathNode:
    node_id: int
    x: float


@dataclass(frozen=True)
class _NodalFunction:
    name: str
    node_id: int
    samples: list[tuple[float, float]]


def generate_bxd_32_6_dynamic_countercheck(
    project_folder: Path,
    *,
    output_path: Path | None = None,
    config_path: Path | None = None,
    velocity_kmh: float | None = None,
    include_prestress: bool = True,
) -> DynamicCountercheckResult:
    """Generate the first BXD HSLM-A1 time-history model for report item 5.7.

    The report's 32.6 m governing row is HSLM-A1 at 330 km/h with
    n0=5.066 Hz, amax=2.30 m/s2, and dynamic displacement=2.97 mm.
    """
    project = load_project_folder(project_folder)
    config_path = config_path or project_folder / "static_countercheck_32_6.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    dyn_cfg = _dynamic_config(config)
    train_id = str(dyn_cfg["train_id"])
    velocity = float(velocity_kmh if velocity_kmh is not None else dyn_cfg["velocity_kmh"])
    velocity_label = round(velocity)
    case_suffix = "" if include_prestress else "_NO_CABLE"
    file_suffix = "" if include_prestress else "_no_cable"
    case_name = f"{_midas_token(train_id)}_{velocity_label}{case_suffix}"

    spans = _girder_spans(project.bridge)
    transport = _critical_axle_position(
        float(config["calculation_span_m"]),
        config["loads"]["transport"],
    )
    split_offsets = _countercheck_split_offsets(config, transport)
    top_bridge = _build_top_only_bridge(project.bridge, spans, split_offsets, config)
    project_update: dict[str, Any] = {"bridge": top_bridge}
    if not include_prestress:
        project_update["prestress"] = project.prestress.model_copy(
            update={"enabled": False},
            deep=True,
        )
    top_project = project.model_copy(update=project_update, deep=True)

    output_path = output_path or (
        project_folder
        / "generated"
        / "midas"
        / f"model_dynamic_countercheck_32_6_{train_id}_{velocity_label}{file_suffix}.mct"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    warnings = write_base_model_mct(top_project, output_path, project_folder=project_folder)

    target_span_index = int(dyn_cfg.get("span_index", 1))
    span_indices = _dynamic_span_indices(dyn_cfg, top_bridge)
    load_nodes = _load_path_nodes(top_bridge, span_indices)
    if len(load_nodes) < 2:
        msg = f"Không tìm thấy đủ node {_span_chain_label(span_indices)} để gán HSLM dynamic load."
        raise ValueError(msg)
    bridge_length = load_nodes[-1].x - load_nodes[0].x
    if bridge_length <= 0:
        msg = f"Chuỗi {_span_chain_label(span_indices)} có chiều dài không hợp lệ."
        raise ValueError(msg)

    train_cfg = dict(dyn_cfg["hslm_a1"])
    axles = _hslm_a1_axle_positions(train_cfg)
    speed_mps = velocity / 3.6
    duration = (axles[-1] + bridge_length) / speed_mps + float(dyn_cfg["duration_padding_s"])
    graph_nodes = _load_path_nodes(top_bridge, target_span_index)
    if len(graph_nodes) < 2:
        msg = f"Không tìm thấy đủ node Girder{target_span_index} để xuất TH-Graph."
        raise ValueError(msg)
    graph_node = _nearest_node(graph_nodes, (graph_nodes[-1].x - graph_nodes[0].x) / 2.0)
    functions = _nodal_functions(
        load_nodes,
        axles=axles,
        axle_load_kn=float(train_cfg["axle_load_kn"]),
        speed_mps=speed_mps,
        duration_s=duration,
        prefix=f"{train_id}_{velocity_label}kmh",
    )

    dynamic_lines = _dynamic_mass_lines(top_bridge, spans, config) + _dynamic_mct_lines(
        case_name=case_name,
        train_id=train_id,
        velocity_kmh=velocity,
        include_prestress=include_prestress,
        functions=functions,
        duration_s=duration,
        time_step_s=float(dyn_cfg["time_step_s"]),
        damping_ratio=float(dyn_cfg["damping_ratio"]),
        graph_node=graph_node,
    )
    text = output_path.read_text(encoding="utf-8")
    output_path.write_text(_insert_before(text, "*EIGEN-CTRL", dynamic_lines), encoding="utf-8")
    warnings.append(
        f"Dynamic countercheck: {train_id} at {velocity:g} km/h, "
        f"damping={float(dyn_cfg['damping_ratio']):g}, "
        f"dt={float(dyn_cfg['time_step_s']):g}s, "
        f"load path={_span_chain_label(span_indices)} "
        f"(L={bridge_length:.3f} m, end time={duration:.3f} s), "
        "self-weight converted by Structure Type and G2_REPORT converted by *LOADTOMASS, "
        f"prestress/tendon={'included' if include_prestress else 'excluded'}, "
        f"graph span=Girder{target_span_index}, graph node={graph_node.node_id}; "
        "chạy MIDAS rồi export TH-Graph để so báo cáo 5.7."
    )
    return DynamicCountercheckResult(
        mct_path=output_path,
        warnings=warnings,
        case_name=case_name,
        train_id=train_id,
        velocity_kmh=velocity,
        include_prestress=include_prestress,
        graph_node_id=graph_node.node_id,
        loaded_node_count=len(load_nodes),
        function_count=len(functions),
        duration_s=duration,
        bridge_length_m=bridge_length,
    )


def _dynamic_config(config: dict[str, Any]) -> dict[str, Any]:
    default: dict[str, Any] = {
        "span_index": 1,
        "span_indices": None,
        "train_id": "HSLM-A1",
        "velocity_kmh": 330.0,
        "time_step_s": 0.001,
        "damping_ratio": 0.015,
        "duration_padding_s": 3.0,
        "hslm_a1": {
            "coach_count": 18,
            "coach_spacing_m": 18.0,
            "axle_spacing_m": 2.0,
            "axle_load_kn": 170.0,
        },
    }
    raw_user = config.get("dynamic_countercheck")
    user: dict[str, Any] = dict(raw_user) if isinstance(raw_user, dict) else {}
    nested = dict(default["hslm_a1"])
    raw_hslm = user.get("hslm_a1")
    if isinstance(raw_hslm, dict):
        nested.update(raw_hslm)
    default.update(user)
    default["hslm_a1"] = nested
    return default


def _dynamic_span_indices(dyn_cfg: dict[str, Any], bridge: Bridge) -> list[int]:
    raw = dyn_cfg.get("span_indices")
    if raw is None:
        raw = dyn_cfg.get("span_chain")
    if raw is None:
        return [int(dyn_cfg.get("span_index", 1))]
    if isinstance(raw, str):
        value = raw.strip()
        if value.lower() in {"all", "*"}:
            return _all_girder_indices(bridge)
        if ".." in value:
            start, end = value.split("..", maxsplit=1)
            return list(range(int(start), int(end) + 1))
        raw = [item.strip() for item in value.split(",") if item.strip()]
    indices = [int(item) for item in raw]
    if not indices:
        msg = "dynamic_countercheck.span_indices không được rỗng."
        raise ValueError(msg)
    return indices


def _all_girder_indices(bridge: Bridge) -> list[int]:
    indices: list[int] = []
    for group in bridge.structure_groups:
        name = group.name or group.id
        if not name.startswith("Girder"):
            continue
        suffix = name.removeprefix("Girder")
        if suffix.isdigit():
            indices.append(int(suffix))
    return sorted(indices)


def _span_chain_label(span_indices: Iterable[int]) -> str:
    values = list(span_indices)
    if not values:
        return "Girder[]"
    if values == list(range(values[0], values[-1] + 1)):
        return f"Girder{values[0]}..Girder{values[-1]}"
    return ", ".join(f"Girder{index}" for index in values)


def _dynamic_mass_lines(bridge: Bridge, spans: list[Any], config: dict[str, Any]) -> list[str]:
    loads = config["loads"]
    stage_cfg = config.get("construction_stages", {})
    g2_case = "G2_REPORT"
    g2_group = str(stage_cfg.get("g2_load_group", "G2-BXD"))
    g2_load = -float(loads["g2_superimposed_dead_kn_per_m"])
    span_length = float(config["calculation_span_m"])
    lines = [
        "",
        "; Dynamic mass source for BXD 5.7",
        "; Self-weight is converted by *STRUCTYPE bSELFWEIGHT=YES; G2 is converted here.",
        "*STLDCASE    ; Static Load Cases",
        "; LCNAME, LCTYPE, DESC",
        f"   {g2_case}, D , Report superimposed dead load included in dynamic mass",
        "",
        "*LOADTOMASS    ; Load to Mass",
        "; DIR, bNodal, bBeam, bPressure, bFloor, GRAV",
        "   XYZ, YES, YES, YES, YES, 9.806",
        f"   {g2_case}, 1",
        "",
    ]
    lines.extend(
        _uniform_load_case(
            bridge,
            g2_case,
            "GZ",
            g2_load,
            spans,
            [(0.0, span_length)],
            group=g2_group,
        )
    )
    return lines


def _load_path_nodes(bridge: Bridge, span_indices: int | Iterable[int]) -> list[_LoadPathNode]:
    if isinstance(span_indices, int):
        span_indices = [span_indices]
    elements = {element.id: element for element in bridge.elements}
    nodes = {node.id: node for node in bridge.nodes}
    node_ids: set[int] = set()
    for span_index in span_indices:
        group_name = f"Girder{span_index}"
        group = next(
            (item for item in bridge.structure_groups if (item.name or item.id) == group_name),
            None,
        )
        if group is None:
            return []
        node_ids.update(
            node_id
            for element_id in group.element_ids
            if (element := elements.get(element_id)) is not None
            for node_id in (element.n1, element.n2)
        )
    ordered = sorted((nodes[node_id] for node_id in node_ids), key=lambda node: (node.x, node.id))
    if len(ordered) < 2:
        return []
    origin_x = ordered[0].x
    return [
        _LoadPathNode(node_id=node.id, x=node.x - origin_x)
        for node in ordered
    ]


def _hslm_a1_axle_positions(train_cfg: dict[str, Any]) -> list[float]:
    """Return the simplified HSLM-A1 axle layout used by the BXD report method."""
    coach_count = int(train_cfg["coach_count"])
    coach_spacing = float(train_cfg["coach_spacing_m"])
    axle_spacing = float(train_cfg["axle_spacing_m"])
    axles: list[float] = []
    for i in range(coach_count):
        base = i * coach_spacing
        axles.extend([base, base + axle_spacing])
    return sorted(axles)


def _nearest_node(nodes: list[_LoadPathNode], x: float) -> _LoadPathNode:
    return min(nodes, key=lambda node: abs(node.x - x))


def _nodal_functions(
    nodes: list[_LoadPathNode],
    *,
    axles: list[float],
    axle_load_kn: float,
    speed_mps: float,
    duration_s: float,
    prefix: str,
) -> list[_NodalFunction]:
    x_values = [node.x for node in nodes]
    functions: list[_NodalFunction] = []
    for i, node in enumerate(nodes):
        event_times = {0.0, duration_s}
        for axle in axles:
            for x in _influence_breakpoints(x_values, i):
                t = (x + axle) / speed_mps
                if -1e-9 <= t <= duration_s + 1e-9:
                    event_times.add(_clean_time(t))
        samples = [
            (t, _nodal_force_at(x_values, i, axles, axle_load_kn, speed_mps, t))
            for t in sorted(event_times)
        ]
        functions.append(
            _NodalFunction(
                name=f"{prefix}_n{node.node_id}",
                node_id=node.node_id,
                samples=_trim_zero_runs(samples),
            )
        )
    return functions


def _influence_breakpoints(x_values: list[float], index: int) -> list[float]:
    values = [x_values[index]]
    if index > 0:
        values.append(x_values[index - 1])
    if index < len(x_values) - 1:
        values.append(x_values[index + 1])
    return values


def _nodal_force_at(
    x_values: list[float],
    node_index: int,
    axles: list[float],
    axle_load_kn: float,
    speed_mps: float,
    time_s: float,
) -> float:
    total = 0.0
    start = x_values[0]
    end = x_values[-1]
    for axle in axles:
        x = speed_mps * time_s - axle
        if x < start - 1e-8 or x > end + 1e-8:
            continue
        total += axle_load_kn * _linear_shape_weight(x_values, node_index, x)
    return 0.0 if abs(total) < 1e-9 else total


def _linear_shape_weight(x_values: list[float], node_index: int, x: float) -> float:
    if len(x_values) == 1:
        return 1.0
    if x <= x_values[0] + 1e-8:
        return 1.0 if node_index == 0 else 0.0
    if x >= x_values[-1] - 1e-8:
        return 1.0 if node_index == len(x_values) - 1 else 0.0
    right = bisect_right(x_values, x)
    left = right - 1
    x_left = x_values[left]
    x_right = x_values[right]
    if x_right - x_left <= 1e-12:
        return 0.0
    if node_index == left:
        return (x_right - x) / (x_right - x_left)
    if node_index == right:
        return (x - x_left) / (x_right - x_left)
    return 0.0


def _trim_zero_runs(samples: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(samples) <= 2:
        return samples
    keep: list[tuple[float, float]] = []
    for i, sample in enumerate(samples):
        prev_value = samples[i - 1][1] if i else None
        next_value = samples[i + 1][1] if i < len(samples) - 1 else None
        value = sample[1]
        if (
            i in {0, len(samples) - 1}
            or abs(value) > 1e-9
            or (prev_value is not None and abs(prev_value) > 1e-9)
            or (next_value is not None and abs(next_value) > 1e-9)
        ):
            keep.append(sample)
    return keep


def _dynamic_mct_lines(
    *,
    case_name: str,
    train_id: str,
    velocity_kmh: float,
    include_prestress: bool,
    functions: list[_NodalFunction],
    duration_s: float,
    time_step_s: float,
    damping_ratio: float,
    graph_node: _LoadPathNode,
) -> list[str]:
    lines = [
        "",
        f"; BXD 32.6 m dynamic countercheck: {train_id} at {velocity_kmh:g} km/h",
        f"; Prestress/tendon model: {'included' if include_prestress else 'excluded'}",
        "; Report targets: n0=5.066 Hz, amax=2.30 m/s2, dynamic displacement=2.97 mm.",
        "*TFUNCTION    ; Time History Function",
        "; FUNC=NAME, 1, iTYPE, iMETHOD, SCALE/MAX, GRAV, DESC  ; line 1 (TIME)",
        ";      TIME1, VALUE1, TIME2, VALUE2, ...               ; from line 2 (TIME)",
    ]
    for function in functions:
        lines.append(f"   FUNC={function.name}, 1, 3, 0, 1, 9.806, ")
        formatted = [f"{time:10.6f}, {_num(value):>13}" for time, value in function.samples]
        for i in range(0, len(formatted), 2):
            lines.append("        " + ",   ".join(formatted[i : i + 2]))
    lines.extend(
        [
            "",
            "*THLDCASE   ; Time History Load Cases",
            "; NAME=NAME, DESC",
            ";      iATYPE, iAMETHOD, iTHTYPE, iGEOM, ETIME/iISTEP, INC, iOUT, bP-DELTA, INITLOAD, INITMETHOD [SEQ LOAD]",
            ";      iMDTYPE, [DR-DC], [TIP], [NACP]",
            f"   NAME={case_name}, ",
            f"        1, 1, 1, 0, {_num(duration_s)}, {_num(time_step_s)}, 1, NO, NO, ORDER, NO",
            f"        1, {_num(damping_ratio)}, , , , , , , , , , , , , , , , ",
            "",
            "*DYN-NLOAD    ; Dynamic Nodal Loads",
            "; NODE_LIST, THIS, FUNC, DIR, ARTIME, SCALE",
        ]
    )
    for function in functions:
        lines.append(f"   {function.node_id}, {case_name}, {function.name}, Z, 0, -1")
    lines.extend(
        [
            "",
            "*TH-GRAPH",
            "; iFUNC, iGFTYPE, NAME, LCNAME, [DATA1]",
            f"  0, 2, deck acc 32.6, {case_name}, {graph_node.node_id}, 3, 2, 0, 3, YES, 0",
            f"  0, 2, deck dz 32.6, {case_name}, {graph_node.node_id}, 1, 2, 0, 3, YES, 0",
            "",
            "*LC-COLOR    ; Diagram Color for Load Case",
            "; ANAL, LCNAME, iR1(ALL), iG1(ALL), iB1(ALL), iR2(MIN), iG2(MIN), iB2(MIN), iR3(MAX), iG2(MAX), iB2(MAX)",
            f" TH, {case_name}, 0, 128, 128, 78, 0, 255, 85, 0, 192",
            "",
        ]
    )
    return lines


def _clean_time(value: float) -> float:
    return round(max(value, 0.0), 6)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[5]
    for include_prestress in (True, False):
        result = generate_bxd_32_6_dynamic_countercheck(
            root / "examples" / "bxd",
            include_prestress=include_prestress,
        )
        print(result.mct_path)
        print(
            f"{result.train_id} @ {result.velocity_kmh:g} km/h "
            f"({'with cables' if result.include_prestress else 'no cables'}) -> "
            f"{result.function_count} functions, graph node {result.graph_node_id}, "
            f"duration {result.duration_s:.3f} s"
        )
        for warning in result.warnings:
            print("WARN", warning)
