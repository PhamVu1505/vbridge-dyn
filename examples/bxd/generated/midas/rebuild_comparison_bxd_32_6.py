"""Rebuild bang doi chieu MIDAS <-> bao cao BXD cho dam 32,6 m.

Input MIDAS export dat trong cung thu muc:
  - Beam Force.xls
  - Reaction(Global).xls
  - Displacements(Global).xls
  - Displacements(Global)_construction.xls
  - Beam Stress.xls
  - Beam Stress_construction.xls

Output:
  - comparison_bxd_32_6.xlsx
  - comparison_bxd_32_6.md
  - comparison_checklist_bxd_32_6.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

BASE = Path(__file__).resolve().parent
SUPPORT_LOCAL = (2, 30)
END_LOCAL = (1, 31)
MIDSPAN_LOCAL = 16

STRESS_COLUMNS = [
    "Cb(min/max)",
    "Cb1(-y+z)",
    "Cb2(+y+z)",
    "Cb3(+y-z)",
    "Cb4(-y-z)",
]
STRESS_TOP = ["Cb1(-y+z)", "Cb2(+y+z)"]
STRESS_BOT = ["Cb3(+y-z)", "Cb4(-y-z)"]


def load_midas_xls(path: Path) -> pd.DataFrame:
    """Read a MIDAS Excel export and detect its header row."""
    raw = pd.read_excel(path, header=None)
    header_row = 0
    for idx in range(min(8, len(raw))):
        row = raw.iloc[idx].astype(str)
        if row.str.contains("Load", na=False).any():
            header_row = idx
            break
    columns = [str(col).split("\n")[0].strip() for col in raw.iloc[header_row].tolist()]
    df = raw.iloc[header_row + 1 :].copy()
    df.columns = columns
    return df


def num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def absmax_signed(series: pd.Series) -> float:
    series = series.dropna()
    if series.empty:
        return 0.0
    return float(series.loc[series.abs().idxmax()])


def build_beam_summary() -> pd.DataFrame:
    beam_raw = load_midas_xls(BASE / "Beam Force.xls")
    for col in ["Moment-y", "Shear-z"]:
        beam_raw[col] = num(beam_raw[col])

    rows = []
    for load, group in beam_raw.groupby("Load"):
        my = group["Moment-y"]
        vz = group["Shear-z"]
        rows.append(
            [load, my.min(), my.max(), absmax_signed(my), vz.min(), vz.max(), absmax_signed(vz)]
        )
    return (
        pd.DataFrame(
            rows,
            columns=[
                "Load",
                "My_min_kNm",
                "My_max_kNm",
                "My_absmax_signed_kNm",
                "Vz_min_kN",
                "Vz_max_kN",
                "Vz_absmax_signed_kN",
            ],
        )
        .round(3)
        .set_index("Load")
    )


def build_reaction_summary() -> pd.DataFrame:
    reaction_raw = load_midas_xls(BASE / "Reaction(Global).xls")
    for col in ["Node", "FZ", "FY"]:
        reaction_raw[col] = num(reaction_raw[col])
    reaction_raw = reaction_raw.dropna(subset=["Node"]).copy()
    reaction_raw["Node"] = reaction_raw["Node"].astype(int)
    reaction_raw["girder"] = reaction_raw["Node"] // 100000
    reaction_raw["local"] = reaction_raw["Node"] % 100000

    rows = []
    for load, group in reaction_raw.groupby("Load"):
        support = group[group["local"].isin(SUPPORT_LOCAL)]
        rows.append(
            [
                load,
                support["FZ"].abs().max(),
                support.groupby("girder")["FY"].sum().abs().max(),
                support.groupby("girder")["FZ"].sum().abs().max(),
            ]
        )
    return (
        pd.DataFrame(
            rows,
            columns=[
                "Load",
                "support_FZ_absmax_kN",
                "span_sum_FY_absmax_kN",
                "span_sum_FZ_absmax_kN",
            ],
        )
        .round(3)
        .set_index("Load")
    )


def build_displacement_summary() -> pd.DataFrame:
    disp_raw = load_midas_xls(BASE / "Displacements(Global).xls")
    for col in ["Node", "DZ", "RY"]:
        disp_raw[col] = num(disp_raw[col])
    disp_raw = disp_raw.dropna(subset=["Node"]).copy()
    disp_raw["Node"] = disp_raw["Node"].astype(int)
    disp_raw["local"] = disp_raw["Node"] % 100000

    rows = []
    for load, group in disp_raw.groupby("Load"):
        dz = group["DZ"] * 1000.0
        ry_support = group[group["local"].isin(SUPPORT_LOCAL)]["RY"].abs().max() * 1000.0
        ry_end = group[group["local"].isin(END_LOCAL)]["RY"].abs().max() * 1000.0
        rows.append([load, dz.min(), dz.max(), dz.abs().max(), ry_support, ry_end])
    return (
        pd.DataFrame(
            rows,
            columns=[
                "Load",
                "DZ_min_mm",
                "DZ_max_mm",
                "DZ_absmax_mm",
                "RY_support_absmax_mrad",
                "RY_end_absmax_mrad",
            ],
        )
        .round(3)
        .set_index("Load")
    )


def build_construction_disp_summary() -> pd.DataFrame:
    path = BASE / "Displacements(Global)_construction.xls"
    if not path.exists():
        return pd.DataFrame()
    disp_raw = load_midas_xls(path)
    for col in ["Node", "DZ", "RY"]:
        disp_raw[col] = num(disp_raw[col])
    disp_raw = disp_raw.dropna(subset=["Node"]).copy()
    disp_raw["Node"] = disp_raw["Node"].astype(int)
    disp_raw["local"] = disp_raw["Node"] % 100000

    rows = []
    for (load, stage, step), group in disp_raw.groupby(["Load", "Stage", "Step"], dropna=False):
        midspan = group[group["local"].eq(MIDSPAN_LOCAL)]["DZ"] * 1000.0
        dz = group["DZ"] * 1000.0
        rows.append(
            [
                load,
                stage,
                step,
                len(group),
                None if midspan.empty else float(midspan.mean()),
                float(dz.min()),
                float(dz.max()),
                float(dz.abs().max()),
            ]
        )
    return pd.DataFrame(
        rows,
        columns=[
            "Load",
            "Stage",
            "Step",
            "n_rows",
            "DZ_midspan_mean_mm",
            "DZ_min_mm",
            "DZ_max_mm",
            "DZ_absmax_mm",
        ],
    ).round(3)


def build_stress_summary(path: Path, *, construction: bool) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    stress_raw = load_midas_xls(path)
    stress_raw["Elem"] = num(stress_raw["Elem"])
    for col in STRESS_COLUMNS:
        stress_raw[col] = num(stress_raw[col]) / 1000.0
    stress_raw = stress_raw.dropna(subset=["Elem"]).copy()
    stress_raw["part_node"] = num(
        stress_raw["Part"].astype(str).str.extract(r"\[(\d+)\]", expand=False)
    )
    stress_raw["part_local"] = stress_raw["part_node"] % 100000

    group_cols = ["Load", "Stage", "Step"] if construction else ["Load"]
    rows = []
    for key, group in stress_raw.groupby(group_cols, dropna=False):
        if not isinstance(key, tuple):
            key = (key,)
        row: dict[str, Any] = dict(zip(group_cols, key, strict=True))
        row["n_rows"] = len(group)
        midspan = group[group["part_local"].eq(MIDSPAN_LOCAL)]
        for col in STRESS_COLUMNS:
            row[f"{col}_min_MPa"] = float(group[col].min())
            row[f"{col}_max_MPa"] = float(group[col].max())
            row[f"{col}_range_MPa"] = float(group[col].max() - group[col].min())
            if midspan.empty:
                row[f"{col}_midspan_min_MPa"] = None
                row[f"{col}_midspan_max_MPa"] = None
                row[f"{col}_midspan_range_MPa"] = None
            else:
                row[f"{col}_midspan_min_MPa"] = float(midspan[col].min())
                row[f"{col}_midspan_max_MPa"] = float(midspan[col].max())
                row[f"{col}_midspan_range_MPa"] = float(midspan[col].max() - midspan[col].min())
        rows.append(row)
    return pd.DataFrame(rows).round(3)


def build_eigen_summary() -> pd.DataFrame:
    path = BASE / "Eigenvalue Mode.xls"
    if not path.exists():
        return pd.DataFrame()
    raw = pd.read_excel(path, header=None)

    header_row = None
    for idx in range(min(20, len(raw))):
        row = raw.iloc[idx].astype(str)
        if (
            row.str.contains("Mode", na=False).any()
            and row.str.contains("Frequency", na=False).any()
        ):
            header_row = idx
            break
    if header_row is None:
        return pd.DataFrame()

    rows = []
    for _, row in raw.iloc[header_row + 2 :].iterrows():
        mode = pd.to_numeric(row.iloc[3], errors="coerce")
        if pd.isna(mode):
            if rows:
                break
            continue
        rows.append(
            [
                int(mode),
                float(pd.to_numeric(row.iloc[4], errors="coerce")),
                float(pd.to_numeric(row.iloc[6], errors="coerce")),
                float(pd.to_numeric(row.iloc[8], errors="coerce")),
            ]
        )
    return pd.DataFrame(
        rows, columns=["Mode", "Frequency_rad_s", "Frequency_Hz", "Period_s"]
    ).round(6)


def build_dynamic_response_summary() -> pd.DataFrame:
    exports = [
        ("displacement", BASE / "Displacement_dynamic.xls", 1000.0, "mm"),
        ("absolute_accel", BASE / "Absolute Accel._dynamic.xls", 1.0, "m/s²"),
        ("relative_accel", BASE / "Relative Accel._dynamic.xls", 1.0, "m/s²"),
        ("velocity", BASE / "Velocity_dynamic.xls", 1.0, "m/s"),
    ]
    rows = []
    for result, path, scale, unit in exports:
        if not path.exists():
            continue
        raw = pd.read_excel(path, header=None)
        headers = [str(value).split("\n")[0].strip() for value in raw.iloc[1].tolist()]
        data = raw.iloc[3:].copy()
        data["node"] = num(data.iloc[:, 2])
        data["load"] = data.iloc[:, 3].astype(str)
        data = data.dropna(subset=["node"]).copy()
        data["node"] = data["node"].astype(int)

        for component in ["DX", "DY", "DZ", "RX", "RY", "RZ"]:
            if component not in headers:
                continue
            value_col = headers.index(component)
            time_col = value_col + 1
            values = num(data.iloc[:, value_col]) * scale
            times = num(data.iloc[:, time_col])
            for scope, selector in [
                ("global_absmax", data.index),
                (
                    "node_100016_all",
                    data[data["node"].eq(100016) & data["load"].str.endswith("(all)")].index,
                ),
                (
                    "node_100016_max",
                    data[data["node"].eq(100016) & data["load"].str.endswith("(max)")].index,
                ),
                (
                    "node_100016_min",
                    data[data["node"].eq(100016) & data["load"].str.endswith("(min)")].index,
                ),
            ]:
                scoped_values = values.loc[selector].dropna()
                if scoped_values.empty:
                    continue
                idx = scoped_values.abs().idxmax()
                rows.append(
                    {
                        "Result": result,
                        "Component": component,
                        "Scope": scope,
                        "Node": int(data.loc[idx, "node"]),
                        "Load": data.loc[idx, "load"],
                        "Value": float(values.loc[idx]),
                        "Abs_value": float(abs(values.loc[idx])),
                        "Time_s": float(times.loc[idx]) if not pd.isna(times.loc[idx]) else None,
                        "Unit": unit,
                    }
                )
    return pd.DataFrame(rows).round(6)


def build_summaries() -> dict[str, pd.DataFrame]:
    return {
        "beam": build_beam_summary(),
        "reaction": build_reaction_summary(),
        "disp": build_displacement_summary(),
        "construction_disp": build_construction_disp_summary(),
        "stress_static": build_stress_summary(BASE / "Beam Stress.xls", construction=False),
        "stress_construction": build_stress_summary(
            BASE / "Beam Stress_construction.xls", construction=True
        ),
        "eigen": build_eigen_summary(),
        "dynamic": build_dynamic_response_summary(),
    }


REPORT = {
    "M_G1_report_kNm": 26554.0,
    "M_G2_report_kNm": 13240.0,
    "M_prestress_effective_report_kNm": -64546.0,
    "M_LM71_2T_report_kNm": 24108.0,
    "M_LM71_2T_phi_report_kNm": 27220.0,
    "M_transport_report_kNm": 37889.0,
    "M_transport_dyn_report_kNm": 41678.0,
    "M_service_no_prestress_report_kNm": 67014.0,
    "M_ULS_LM71_report_kNm": 93191.0,
    "M_ULS_transport_report_kNm": 98364.0,
    "V_ULS_service_report_kN": 7536.0,
    "deflection_LM71_report_mm": 8.40,
    "camber_after_g2_36d_report_mm": 18.92,
    "camber_long_100y_report_mm": 17.36,
    "camber_delta_report_mm": 1.56,
    "rotation_LM71_report_mrad": 0.267,
    "rotation_transport_report_mrad": 0.408,
    "stress_transfer_report_mpa": -15.65,
    "stress_service_report_mpa": -4.41,
    "stress_transport_report_mpa": -4.16,
    "stress_long_report_mpa": -2.87,
    "fatigue_moment_report_kNm": 25072.0,
    "fatigue_cable_stress_report_mpa": 21.1,
    "fatigue_stirrup_stress_report_mpa": 21.2,
    "fatigue_concrete_stress_report_mpa": 5.2,
    "frequency_report_Hz": 5.066,
    "dynamic_acc_report_mps2": 2.30,
    "dynamic_disp_report_mm": 2.97,
}


REPORT_SOURCE = {
    "G1 trọng lượng bản thân giữa nhịp": "Mục 4.2, bảng Nội lực, hàng G1, cột 32,6 m.",
    "G2 tĩnh tải giai đoạn 2 giữa nhịp": "Mục 4.2, bảng Nội lực, hàng G2, cột 32,6 m.",
    "Mô men âm lớn nhất do dự ứng lực": "Mục 4.2, bảng Nội lực, hàng DUL hữu hiệu dài hạn; bảng lực dự ứng lực, cột 32,6 m.",
    "LM71 hai làn": "Mục 4.2, bảng Nội lực, hàng LM71 hai làn, cột 32,6 m.",
    "LM71 hai làn x phi": "Mục 4.2, bảng Nội lực, hàng LM71 x phi, cột 32,6 m.",
    "Xe vận chuyển": "Mục 4.2, bảng Nội lực, hàng vận chuyển, cột 32,6 m.",
    "Xe vận chuyển x hệ số động": "Mục 4.2, bảng Nội lực, hàng vận chuyển x hệ số động, cột 32,6 m.",
    "Khai thác không kể DUL: G1+G2+LM71*phi": "Mục 4.2, bảng tổ hợp nội lực, hàng khai thác chưa kể DUL, cột 32,6 m.",
    "ULS khai thác LM71": "Mục 4.2, bảng tổ hợp nội lực, hàng khai thác, cột 32,6 m.",
    "ULS vận chuyển": "Mục 4.2, bảng tổ hợp nội lực, hàng thi công - vận chuyển, cột 32,6 m.",
    "Phản lực gối do trọng lượng bản thân": "Suy từ mục 4.2: q_G1 = 214,1 kN/m và nhịp tính toán 31,5 m.",
    "Lực cắt ULS khai thác có DUL": "Mục 4.2, bảng tổ hợp nội lực, hàng khai thác tại gối, cột 32,6 m.",
    "Ứng suất căng kéo 3 ngày": "Mục 5.1, bảng kiểm toán ứng suất, hàng Căng kéo, cột 32,6 m.",
    "Ứng suất khai thác SLS": "Mục 5.1, bảng kiểm toán ứng suất, hàng Khai thác, cột 32,6 m.",
    "Ứng suất thi công - vận chuyển SLS": "Mục 5.1, bảng kiểm toán ứng suất, hàng Thi công, cột 32,6 m.",
    "Ứng suất dài hạn 100 năm": "Mục 5.1, bảng kiểm toán ứng suất, hàng Dài hạn, cột 32,6 m.",
    "Độ võng do LM71": "Mục 5.2, bảng kiểm toán độ võng, độ vồng và góc xoay, hàng đầu tiên, cột 32,6 m.",
    "Độ vồng sau lắp tĩnh tải GĐ2": "Mục 5.2, hàng Độ vồng sau lắp tĩnh tải GĐ2, cột 32,6 m.",
    "Độ vồng dài hạn 100 năm": "Mục 5.2, hàng Độ vồng dài hạn 100 năm, cột 32,6 m.",
    "Chênh lệch độ vồng": "Mục 5.2, hàng Chênh lệch độ vồng, cột 32,6 m.",
    "Góc xoay tại đầu dầm do LM71": "Mục 5.2, hàng Góc xoay do LM71, cột 32,6 m; báo cáo ghi góc xoay tại đầu dầm.",
    "Góc xoay tại đầu dầm do vận chuyển": "Mục 5.2, hàng Góc xoay do vận chuyển, cột 32,6 m; báo cáo ghi góc xoay tại đầu dầm.",
    "Mỏi - mô men kiểm toán": "Mục 5.8, bảng kiểm toán mỏi, hàng mỏi tại, cột 32,6 m.",
    "Mỏi - ứng suất bê tông": "Mục 5.8, bảng kiểm toán mỏi, hàng bê tông, cột 32,6 m.",
    "Mỏi - ứng suất cáp dự ứng lực": "Mục 5.8, bảng kiểm toán mỏi, hàng ứng suất cáp, cột 32,6 m.",
    "Mỏi - ứng suất cốt đai": "Mục 5.8, bảng kiểm toán mỏi, hàng cốt đai, cột 32,6 m.",
    "Tần số dao động riêng n0": "Mục 5.7.1, bảng tần số dao động riêng, cột 32,6 m.",
    "Gia tốc động lớn nhất HSLM-A": "Mục 5.7.3, bảng kết quả phân tích động HSLM-A, cột 32,6 m.",
    "Độ võng động lớn nhất HSLM-A": "Mục 5.7.3, bảng kết quả phân tích động HSLM-A, cột 32,6 m.",
}


def scalar(df: pd.DataFrame, index: str, column: str) -> float | None:
    if df.empty or index not in df.index or column not in df:
        return None
    value = df.loc[index, column]
    return None if pd.isna(value) else float(value)


def construction_midspan(summary: pd.DataFrame, stage: str, step: str) -> float | None:
    if summary.empty:
        return None
    hit = summary[
        summary["Load"].eq("Summation") & summary["Stage"].eq(stage) & summary["Step"].eq(step)
    ]
    if hit.empty:
        return None
    return float(hit.iloc[0]["DZ_midspan_mean_mm"])


def stress_value(
    summary: pd.DataFrame,
    *,
    load: str,
    component: str,
    metric: str,
    scope: str = "",
    stage: str | None = None,
    step: str | None = None,
) -> float | None:
    if summary.empty:
        return None
    hit = summary[summary["Load"].eq(load)]
    if stage is not None:
        hit = hit[hit["Stage"].eq(stage)]
    if step is not None:
        hit = hit[hit["Step"].eq(step)]
    scope_part = f"{scope}_" if scope else ""
    column = f"{component}_{scope_part}{metric}_MPa"
    if hit.empty or column not in hit:
        return None
    value = hit.iloc[0][column]
    return None if pd.isna(value) else float(value)


def stress_pair_value(
    summary: pd.DataFrame,
    *,
    load: str,
    components: list[str],
    metric: str,
    scope: str = "",
    stage: str | None = None,
    step: str | None = None,
) -> float | None:
    values = [
        value
        for component in components
        if (
            value := stress_value(
                summary,
                load=load,
                component=component,
                metric=metric,
                scope=scope,
                stage=stage,
                step=step,
            )
        )
        is not None
    ]
    if not values:
        return None
    if metric == "min":
        return min(values)
    if metric == "max":
        return max(values)
    return max(values)


def first_scalar(df: pd.DataFrame, indexes: list[str], column: str) -> tuple[float | None, str]:
    for index in indexes:
        value = scalar(df, index, column)
        if value is not None:
            return value, index
    return None, ""


def first_stress_value(
    summary: pd.DataFrame,
    *,
    loads: list[str],
    component: str,
    metric: str,
) -> tuple[float | None, str]:
    for load in loads:
        value = stress_value(summary, load=load, component=component, metric=metric)
        if value is not None:
            return value, load
    return None, ""


def first_eigen_frequency(summary: pd.DataFrame) -> float | None:
    if summary.empty:
        return None
    hit = summary[summary["Mode"].eq(1)]
    if hit.empty:
        return None
    return float(hit.iloc[0]["Frequency_Hz"])


def dynamic_response_value(
    summary: pd.DataFrame,
    *,
    result: str,
    component: str,
    scope: str = "node_100016_all",
    column: str = "Abs_value",
) -> float | None:
    if summary.empty:
        return None
    hit = summary[
        summary["Result"].eq(result)
        & summary["Component"].eq(component)
        & summary["Scope"].eq(scope)
    ]
    if hit.empty or column not in hit:
        return None
    value = hit.iloc[0][column]
    return None if pd.isna(value) else float(value)


def stress_pair_range_between_loads(
    summary: pd.DataFrame,
    *,
    max_load: str,
    min_load: str,
    components: list[str],
    scope: str = "",
) -> float | None:
    ranges = []
    for component in components:
        max_value = stress_value(
            summary, load=max_load, component=component, metric="max", scope=scope
        )
        min_value = stress_value(
            summary, load=min_load, component=component, metric="min", scope=scope
        )
        if max_value is not None and min_value is not None:
            ranges.append(max_value - min_value)
    return None if not ranges else max(ranges)


def make_row(
    group: str,
    quantity: str,
    unit: str,
    report: float | None,
    midas: float | None,
    midas_source: str,
    comment: str,
    status: str,
) -> list[Any]:
    diff = None if report is None or midas is None else midas - report
    pct = None if diff is None or report == 0 else diff / report * 100.0
    return [
        group,
        quantity,
        unit,
        status,
        REPORT_SOURCE.get(quantity, ""),
        report,
        None if midas is None else round(midas, 3),
        None if diff is None else round(diff, 3),
        None if pct is None else round(pct, 3),
        midas_source,
        comment,
    ]


def build_comparison(summaries: dict[str, pd.DataFrame]) -> pd.DataFrame:
    beam = summaries["beam"]
    reaction = summaries["reaction"]
    disp = summaries["disp"]
    construction = summaries["construction_disp"]
    stress_static = summaries["stress_static"]
    stress_construction = summaries["stress_construction"]
    eigen = summaries["eigen"]
    dynamic = summaries["dynamic"]

    g1 = scalar(beam, "SelfWeight", "My_max_kNm")
    g2 = scalar(beam, "G2_REPORT", "My_max_kNm")
    lm71 = scalar(beam, "LM71_2T(max)", "My_max_kNm")
    lm71_phi = scalar(beam, "LM71_2T_PHI(max)", "My_max_kNm")
    fatigue_moment, fatigue_moment_load = first_scalar(
        beam,
        ["FATIGUE_LM71_EN(max)", "LM71_FAT_2T_PHI(max)"],
        "My_max_kNm",
    )
    fatigue_concrete = stress_pair_range_between_loads(
        stress_static,
        max_load="FATIGUE_LM71_EN(max)",
        min_load="FATIGUE_LM71_EN(min)",
        components=STRESS_BOT,
    )
    fatigue_concrete_load = "FATIGUE_LM71_EN(max-min)" if fatigue_concrete is not None else ""
    if fatigue_concrete is None:
        fatigue_concrete = stress_pair_range_between_loads(
            stress_static,
            max_load="LM71_FAT_2T_PHI(max)",
            min_load="LM71_FAT_2T_PHI(min)",
            components=STRESS_BOT,
        )
        fatigue_concrete_load = "LM71_FAT_2T_PHI(max-min)" if fatigue_concrete is not None else ""
    deflection_lm71 = scalar(disp, "LM71_2T(min)", "DZ_min_mm")
    if deflection_lm71 is not None:
        deflection_lm71 = abs(deflection_lm71)
    else:
        deflection_lm71 = scalar(disp, "LM71_2T(all)", "DZ_absmax_mm")
    transfer_stress = stress_pair_value(
        stress_construction,
        load="Summation",
        stage="CS1_Prestress_3d",
        step="001(last)",
        components=STRESS_BOT,
        metric="min",
    )
    service_stress = stress_pair_value(
        stress_static,
        load="SLS_CHAR_LM71(max)",
        components=STRESS_BOT,
        metric="max",
        scope="midspan",
    )
    transport_stress = stress_pair_value(
        stress_static,
        load="SLS_TRANSPORT_P",
        components=STRESS_BOT,
        metric="max",
        scope="midspan",
    )
    long_term_stress = stress_pair_value(
        stress_construction,
        load="Summation",
        stage="CS3_LongTerm_100y",
        step="005(last)",
        components=STRESS_TOP,
        metric="min",
    )
    transport_stress_status = "Đã so" if transport_stress is not None else "Chờ export"
    transport_stress_comment = (
        "Theo bảng 5.1: Thi công kiểm sigma_bot,max để không kéo thớ dưới; lấy đúng bot = Cb3/Cb4 tại giữa nhịp."
        if transport_stress is not None
        else "Đã thêm combo SLS_TRANSPORT_P vào MCT; cần chạy lại MIDAS và export Beam Stress.xls để cập nhật."
    )
    service_no_p = None if None in [g1, g2, lm71_phi] else g1 + g2 + lm71_phi
    camber_36d = construction_midspan(construction, "CS2_G2_36d", "002(last)")
    camber_100y = construction_midspan(construction, "CS3_LongTerm_100y", "005(last)")
    camber_delta = None if None in [camber_36d, camber_100y] else camber_36d - camber_100y
    dynamic_frequency = first_eigen_frequency(eigen)
    dynamic_acc = dynamic_response_value(dynamic, result="absolute_accel", component="DZ")
    dynamic_disp = dynamic_response_value(dynamic, result="displacement", component="DZ")
    dynamic_frequency_status = "Đã so" if dynamic_frequency is not None else "Chờ export dynamic"
    dynamic_acc_status = "Đã so" if dynamic_acc is not None else "Chờ export dynamic"
    dynamic_disp_status = "Đã so" if dynamic_disp is not None else "Chờ export dynamic"

    rows = [
        make_row(
            "Nội lực 4.2",
            "G1 trọng lượng bản thân giữa nhịp",
            "kNm",
            REPORT["M_G1_report_kNm"],
            g1,
            "Beam Force.xls: SelfWeight max My",
            "MIDAS tự tính theo hình học/taper; báo cáo dùng q_G1 tại mặt cắt giữa nhịp.",
            "Đã so",
        ),
        make_row(
            "Nội lực 4.2",
            "G2 tĩnh tải giai đoạn 2 giữa nhịp",
            "kNm",
            REPORT["M_G2_report_kNm"],
            g2,
            "Beam Force.xls: G2_REPORT max My",
            "OK",
            "Đã so",
        ),
        make_row(
            "Nội lực 4.2",
            "Mô men âm lớn nhất do dự ứng lực",
            "kNm",
            REPORT["M_prestress_effective_report_kNm"],
            scalar(beam, "Prestress", "My_min_kNm"),
            "Beam Force.xls: Prestress min My",
            "Sai khác cơ bản do cách kể dự ứng lực/mất mát giữa báo cáo và tendon MIDAS.",
            "Đã so",
        ),
        make_row(
            "Nội lực 4.2",
            "LM71 hai làn",
            "kNm",
            REPORT["M_LM71_2T_report_kNm"],
            lm71,
            "Beam Force.xls: LM71_2T(max) max My",
            "OK",
            "Đã so",
        ),
        make_row(
            "Nội lực 4.2",
            "LM71 hai làn x phi",
            "kNm",
            REPORT["M_LM71_2T_phi_report_kNm"],
            lm71_phi,
            "Beam Force.xls: LM71_2T_PHI(max) max My",
            "OK",
            "Đã so",
        ),
        make_row(
            "Nội lực 4.2",
            "Xe vận chuyển",
            "kNm",
            REPORT["M_transport_report_kNm"],
            scalar(beam, "TRANSPORT", "My_max_kNm"),
            "Beam Force.xls: TRANSPORT max My",
            "OK",
            "Đã so",
        ),
        make_row(
            "Nội lực 4.2",
            "Xe vận chuyển x hệ số động",
            "kNm",
            REPORT["M_transport_dyn_report_kNm"],
            scalar(beam, "TRANSPORT_DYN", "My_max_kNm"),
            "Beam Force.xls: TRANSPORT_DYN max My",
            "OK",
            "Đã so",
        ),
        make_row(
            "Tổ hợp 4.2",
            "Khai thác không kể DUL: G1+G2+LM71*phi",
            "kNm",
            REPORT["M_service_no_prestress_report_kNm"],
            service_no_p,
            "Cộng từ Beam Force.xls",
            "Tổng từ các thành phần; không phải load case export trực tiếp.",
            "Đã so",
        ),
        make_row(
            "Tổ hợp 4.2",
            "ULS khai thác LM71",
            "kNm",
            REPORT["M_ULS_LM71_report_kNm"],
            scalar(beam, "ULS_LM71(max)", "My_max_kNm"),
            "Beam Force.xls: ULS_LM71(max) max My",
            "Sai khác theo trọng lượng bản thân MIDAS.",
            "Đã so",
        ),
        make_row(
            "Tổ hợp 4.2",
            "ULS vận chuyển",
            "kNm",
            REPORT["M_ULS_transport_report_kNm"],
            scalar(beam, "ULS_TRANSPORT", "My_max_kNm"),
            "Beam Force.xls: ULS_TRANSPORT max My",
            "OK; tổ hợp đã bỏ G2_REPORT.",
            "Đã so",
        ),
        make_row(
            "Lực cắt 4.2",
            "Phản lực gối do trọng lượng bản thân",
            "kN",
            3372.075,
            scalar(reaction, "SelfWeight", "support_FZ_absmax_kN"),
            "Reaction(Global).xls: max abs FZ tại gối",
            "Khác do MIDAS lấy trọng lượng theo hình học/taper.",
            "Đã so",
        ),
        make_row(
            "Lực cắt 4.2",
            "Lực cắt ULS khai thác có DUL",
            "kN",
            REPORT["V_ULS_service_report_kN"],
            abs(scalar(beam, "ULS_LM71_P(all)", "Vz_absmax_signed_kN") or 0.0),
            "Beam Force.xls: absmax Vz ULS_LM71_P(all)",
            "Sai khác cơ bản do ảnh hưởng dự ứng lực: tendon xiên trong MIDAS sinh lực cắt đứng và mất mát DUL khác báo cáo.",
            "Cần rà DUL",
        ),
        make_row(
            "Ứng suất 5.1",
            "Ứng suất căng kéo 3 ngày",
            "MPa",
            REPORT["stress_transfer_report_mpa"],
            transfer_stress,
            "Beam Stress_construction.xls: Summation CS1, sigma_bot,min = min Cb3/Cb4",
            "Theo bảng 5.1: Căng kéo kiểm sigma_bot,min, bot = Cb3/Cb4.",
            "Đã so",
        ),
        make_row(
            "Ứng suất 5.1",
            "Ứng suất khai thác SLS",
            "MPa",
            REPORT["stress_service_report_mpa"],
            service_stress,
            "Beam Stress.xls: SLS_CHAR_LM71(max), sigma_bot,max tại node giữa nhịp x00016 = max Cb3/Cb4",
            "Theo bảng 5.1: Khai thác kiểm sigma_bot,max; phải dùng envelope max của tổ hợp moving load, không dùng all/min.",
            "Đã so",
        ),
        make_row(
            "Ứng suất 5.1",
            "Ứng suất thi công - vận chuyển SLS",
            "MPa",
            REPORT["stress_transport_report_mpa"],
            transport_stress,
            "Beam Stress.xls: SLS_TRANSPORT_P, sigma_bot,max tại node giữa nhịp x00016 = max Cb3/Cb4",
            transport_stress_comment,
            transport_stress_status,
        ),
        make_row(
            "Ứng suất 5.1",
            "Ứng suất dài hạn 100 năm",
            "MPa",
            REPORT["stress_long_report_mpa"],
            long_term_stress,
            "Beam Stress_construction.xls: Summation CS3 last, sigma_top,min = min Cb1/Cb2",
            "Theo bảng 5.1: Dài hạn kiểm sigma_top,min, top = Cb1/Cb2.",
            "Đã so",
        ),
        make_row(
            "Độ võng/vồng 5.2",
            "Độ võng do LM71",
            "mm",
            REPORT["deflection_LM71_report_mm"],
            deflection_lm71,
            "Displacements(Global).xls: abs DZ_min LM71_2T(min)",
            "Độ võng xuống lấy trị tuyệt đối của DZ_min; không dùng DZ_max vì đó là chiều ngược.",
            "Đã so",
        ),
        make_row(
            "Độ võng/vồng 5.2",
            "Độ vồng sau lắp tĩnh tải GĐ2",
            "mm",
            REPORT["camber_after_g2_36d_report_mm"],
            camber_36d,
            "Displacements(Global)_construction.xls: Summation CS2_G2_36d last, local 16",
            "So cùng mốc sau lắp tĩnh tải GĐ2 trong mục 5.2.",
            "Đã so",
        ),
        make_row(
            "Độ võng/vồng 5.2",
            "Độ vồng dài hạn 100 năm",
            "mm",
            REPORT["camber_long_100y_report_mm"],
            camber_100y,
            "Displacements(Global)_construction.xls: Summation CS3_LongTerm_100y last, local 16",
            "So cùng mốc dài hạn 100 năm trong mục 5.2.",
            "Đã so",
        ),
        make_row(
            "Độ võng/vồng 5.2",
            "Chênh lệch độ vồng",
            "mm",
            REPORT["camber_delta_report_mm"],
            camber_delta,
            "Tính từ CS2 - CS3",
            "Dấu âm nghĩa là MIDAS tăng vồng theo thời gian; cần rà time-dependent/DUL.",
            "Đã so",
        ),
        make_row(
            "Góc xoay 5.2",
            "Góc xoay tại đầu dầm do LM71",
            "mrad",
            REPORT["rotation_LM71_report_mrad"],
            scalar(disp, "LM71_2T(all)", "RY_end_absmax_mrad"),
            "Displacements(Global).xls: abs RY tại node đầu dầm x00001/x00031",
            "Báo cáo ghi góc xoay tại đầu dầm; MIDAS lấy đúng node đầu dầm.",
            "Đã so",
        ),
        make_row(
            "Góc xoay 5.2",
            "Góc xoay tại đầu dầm do vận chuyển",
            "mrad",
            REPORT["rotation_transport_report_mrad"],
            scalar(disp, "TRANSPORT_DYN", "RY_end_absmax_mrad"),
            "Displacements(Global).xls: abs RY tại node đầu dầm x00001/x00031",
            "Báo cáo ghi góc xoay tại đầu dầm; MIDAS lấy đúng node đầu dầm.",
            "Đã so",
        ),
        make_row(
            "Mỏi 5.8",
            "Mỏi - mô men kiểm toán",
            "kNm",
            REPORT["fatigue_moment_report_kNm"],
            fatigue_moment,
            f"Beam Force.xls: {fatigue_moment_load} max My"
            if fatigue_moment_load
            else "Cần export Beam Force.xls: FATIGUE_LM71_EN(max)",
            "Theo EN: lấy biên độ nội lực do LM71 alpha=1.0, có Phi, nhân lambda=1.04; không dùng LM71 alpha=0.90 của mục hoạt tải thường.",
            "Đã so" if fatigue_moment is not None else "Chờ export fatigue",
        ),
        make_row(
            "Mỏi 5.8",
            "Mỏi - ứng suất bê tông",
            "MPa",
            REPORT["fatigue_concrete_stress_report_mpa"],
            fatigue_concrete,
            f"Beam Stress.xls: {fatigue_concrete_load}, max-min Cb3/Cb4"
            if fatigue_concrete_load
            else "Cần export Beam Stress.xls: FATIGUE_LM71_EN(max/min)",
            "Theo EN: lấy biên độ ứng suất = max-min do LM71 alpha=1.0, có Phi, nhân lambda=1.04.",
            "Đã so" if fatigue_concrete is not None else "Chờ export fatigue",
        ),
        make_row(
            "Mỏi 5.8",
            "Mỏi - ứng suất cáp dự ứng lực",
            "MPa",
            REPORT["fatigue_cable_stress_report_mpa"],
            None,
            "Chưa có export stress range trong cáp",
            "Cần công thức/thiết kế cáp hoặc xuất kết quả tendon stress range để so trực tiếp.",
            "Cần bổ sung",
        ),
        make_row(
            "Mỏi 5.8",
            "Mỏi - ứng suất cốt đai",
            "MPa",
            REPORT["fatigue_stirrup_stress_report_mpa"],
            None,
            "Chưa có export ứng suất cốt đai",
            "Cần công thức kiểm toán cốt đai theo báo cáo hoặc module design riêng.",
            "Cần bổ sung",
        ),
        make_row(
            "Động lực 5.7",
            "Tần số dao động riêng n0",
            "Hz",
            REPORT["frequency_report_Hz"],
            dynamic_frequency,
            "Eigenvalue Mode.xls: Mode 1, Frequency (cycle/sec)",
            "Mode uốn đứng đầu của nhóm dầm song song; export hiện tại cao hơn báo cáo.",
            dynamic_frequency_status,
        ),
        make_row(
            "Động lực 5.7",
            "Gia tốc động lớn nhất HSLM-A",
            "m/s²",
            REPORT["dynamic_acc_report_mps2"],
            dynamic_acc,
            "Absolute Accel._dynamic.xls: Node 100016, HSLM-A1_330(all), abs DZ",
            "Báo cáo khống chế bởi A1 @ 330 km/h; export hiện tại thấp hơn đáng kể, cần sweep thêm tốc độ/case HSLM nếu muốn tìm giá trị khống chế.",
            dynamic_acc_status,
        ),
        make_row(
            "Động lực 5.7",
            "Độ võng động lớn nhất HSLM-A",
            "mm",
            REPORT["dynamic_disp_report_mm"],
            dynamic_disp,
            "Displacement_dynamic.xls: Node 100016, HSLM-A1_330(all), abs DZ x 1000",
            "Báo cáo khống chế bởi A1 @ 330 km/h; export hiện tại thấp hơn đáng kể, cần kiểm lại damping/khối lượng và sweep tốc độ nếu cần khớp báo cáo.",
            dynamic_disp_status,
        ),
    ]

    return pd.DataFrame(
        rows,
        columns=[
            "Group",
            "Quantity",
            "Unit",
            "Status",
            "Report_source",
            "Report_32_6",
            "MIDAS_Excel",
            "Difference",
            "Difference_pct",
            "MIDAS_source",
            "Comment",
        ],
    )


def build_checklist(comparison: pd.DataFrame) -> pd.DataFrame:
    stress_transport_done = (
        comparison.loc[
            comparison["Quantity"].eq("Ứng suất thi công - vận chuyển SLS"),
            "Status",
        ]
        .eq("Đã so")
        .any()
    )
    fatigue_done = (
        comparison.loc[
            comparison["Quantity"].isin(["Mỏi - mô men kiểm toán", "Mỏi - ứng suất bê tông"]),
            "Status",
        ]
        .eq("Đã so")
        .all()
    )
    dynamic_rows = comparison[comparison["Group"].eq("Động lực 5.7")]
    dynamic_done = not dynamic_rows.empty and dynamic_rows["Status"].eq("Đã so").all()
    dynamic_ready = not dynamic_rows.empty
    items = [
        (
            "Đã so",
            "Mục 4.2 - Nội lực và tổ hợp",
            "Đã so tải đơn, tổ hợp khai thác, ULS LM71, ULS vận chuyển và lực cắt có DUL.",
            "Beam Force/Reaction",
        ),
        (
            "Đã so" if stress_transport_done else "Chờ export",
            "Mục 5.1 - Ứng suất",
            "Đã so căng kéo, khai thác, vận chuyển SLS và dài hạn."
            if stress_transport_done
            else "Đã so căng kéo, khai thác và dài hạn; thi công chờ export SLS_TRANSPORT_P.",
            "Beam Stress",
        ),
        (
            "Đã so",
            "Mục 5.2 - Độ võng/vồng/góc xoay",
            "Đã so đúng các hàng trong mục 5.2 cho dầm 32,6 m; góc xoay lấy tại đầu dầm.",
            "Displacements",
        ),
        (
            "Bỏ qua",
            "Gió ngang",
            "Đã có ghi chú riêng; không tiếp tục đối chứng trong bản này theo yêu cầu.",
            "Báo cáo 4.2/5.6",
        ),
        (
            "Đã so" if fatigue_done else "Chờ export fatigue",
            "Mục 5.8 - Mỏi",
            "Đã so mô men mỏi và biên độ ứng suất bê tông từ FATIGUE_LM71_EN; cáp/cốt đai vẫn cần dữ liệu/công thức riêng."
            if fatigue_done
            else "MCT đã có FATIGUE_LM71_EN = biên độ LM71 mỏi nhân lambda=1.04; cần chạy MIDAS và export Beam Force/Beam Stress cho case này.",
            "Beam Force/Beam Stress",
        ),
        (
            "Đã so" if dynamic_done else ("Chờ export dynamic" if dynamic_ready else "Chưa làm"),
            "Động lực",
            "Đã so modal, gia tốc và võng động mục 5.7."
            if dynamic_done
            else (
                "Đã sinh model_dynamic_countercheck_32_6_HSLM-A1_330.mct cho A1 @ 330 km/h; cần chạy MIDAS và export TH-Graph/modal."
                if dynamic_ready
                else "Chưa triển khai HSLM/time-history để so gia tốc, võng động, tốc độ tới hạn."
            ),
            "Báo cáo 5.7",
        ),
    ]
    if not stress_transport_done:
        items.append(
            (
                "Cần export lại",
                "SLS_TRANSPORT_P",
                "MCT đã bổ sung combo; cần chạy lại MIDAS và export Beam Stress.xls để cập nhật ứng suất thi công.",
                "model_static_countercheck_32_6.mct",
            )
        )
    pending = comparison[
        comparison["Status"].isin(
            ["Chờ export", "Chờ export fatigue", "Chờ export dynamic", "Cần bổ sung", "Cần rà DUL"]
        )
    ]
    for _, row in pending.iterrows():
        items.append((row["Status"], row["Quantity"], row["Comment"], row["MIDAS_source"]))
    return pd.DataFrame(items, columns=["Status", "Item", "What_to_check", "Source"])


def fmt_md(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:,.3f}"
    return str(value)


def write_outputs(comparison: pd.DataFrame, summaries: dict[str, pd.DataFrame]) -> None:
    checklist = build_checklist(comparison)
    xlsx = BASE / "comparison_bxd_32_6.xlsx"
    notes = [
        "Bảng được tính lại tự động từ các file Excel MIDAS bằng rebuild_comparison_bxd_32_6.py.",
        "Ứng suất MIDAS trong file Beam Stress có đơn vị kN/m²; script quy đổi sang MPa.",
        "Mapping thớ mục 5.1: top = Cb1/Cb2, bot = Cb3/Cb4; Căng kéo dùng sigma_bot,min, Khai thác/Thi công dùng sigma_bot,max, Dài hạn dùng sigma_top,min.",
        "Với sigma_bot,max của Khai thác, script dùng SLS_CHAR_LM71(max) tại node giữa nhịp x00016; không dùng SLS_CHAR_LM71(all/min) vì đó là envelope bất lợi theo chiều ngược.",
        "Với sigma_bot,max của Thi công, script lấy tại node giữa nhịp x00016 để tránh node đầu dầm có ứng suất 0 làm sai giá trị max.",
        "Độ võng LM71 dùng LM71_2T(min) vì DZ_min là chiều võng xuống; góc xoay dùng trị tuyệt đối envelope tại đầu dầm.",
        "Mỏi bê tông dùng biên độ FATIGUE_LM71_EN(max) - FATIGUE_LM71_EN(min), không lấy trực tiếp một chiều max/min.",
        "Động lực đọc từ Eigenvalue Mode.xls, Displacement_dynamic.xls và Absolute Accel._dynamic.xls; node kiểm tra là 100016 tại giữa nhịp.",
        "Gia tốc Absolute và Relative trong export hiện tại trùng nhau vì time-history không dùng ground motion.",
        "Mục 5.2 được đối chiếu theo đúng các hàng trong báo cáo: độ võng LM71, độ vồng sau GĐ2, độ vồng 100 năm, chênh lệch độ vồng, góc xoay tại đầu dầm.",
        "G1 gọi là trọng lượng bản thân.",
        "Gió đã ghi chú và bỏ qua trong bản này theo yêu cầu.",
        "SLS_TRANSPORT_P và FATIGUE_LM71_EN được đọc từ các file export MIDAS mới nhất nếu có trong thư mục generated/midas.",
        "File Tendon Stress Limit Check.xls hiện là kiểm giới hạn ứng suất tendon sau neo/khai thác, không phải biên độ ứng suất mỏi cáp.",
    ]
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        comparison.to_excel(writer, sheet_name="comparison", index=False)
        pd.DataFrame({"Key": list(REPORT), "Value": list(REPORT.values())}).to_excel(
            writer, sheet_name="report_32_6_values", index=False
        )
        summaries["beam"].reset_index().to_excel(
            writer, sheet_name="midas_beam_summary", index=False
        )
        summaries["reaction"].reset_index().to_excel(
            writer, sheet_name="midas_reaction_summary", index=False
        )
        summaries["disp"].reset_index().to_excel(
            writer, sheet_name="midas_disp_summary", index=False
        )
        summaries["construction_disp"].to_excel(
            writer, sheet_name="midas_construction_disp", index=False
        )
        summaries["stress_static"].to_excel(writer, sheet_name="midas_stress_static", index=False)
        summaries["stress_construction"].to_excel(
            writer, sheet_name="midas_stress_constr", index=False
        )
        summaries["eigen"].to_excel(writer, sheet_name="midas_eigen_summary", index=False)
        summaries["dynamic"].to_excel(writer, sheet_name="midas_dynamic_summary", index=False)
        checklist.to_excel(writer, sheet_name="checklist", index=False)
        pd.DataFrame({"Note": notes}).to_excel(writer, sheet_name="notes", index=False)

    md = BASE / "comparison_bxd_32_6.md"
    lines = [
        "# BXD 32.6 m - so sanh MIDAS / bao cao",
        "",
        f"- MIDAS exports: `{BASE}`",
        "- Bao cao goc: `projects\\de tai BXD\\Bao_cao_tinh_toan_thiet_ke_dam_HSR_nhom_tren_30m.docx`",
        f"- Workbook chi tiet: `{xlsx}`",
        "",
        "| Nhóm | Đại lượng | Trạng thái | Đơn vị | Báo cáo | MIDAS | Sai khác % | Ghi chú |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in comparison.iterrows():
        lines.append(
            f"| {row['Group']} | {row['Quantity']} | {row['Status']} | {row['Unit']} | "
            f"{fmt_md(row['Report_32_6'])} | {fmt_md(row['MIDAS_Excel'])} | {fmt_md(row['Difference_pct'])} | {row['Comment']} |"
        )
    md.write_text("\n".join(lines), encoding="utf-8")

    checklist_md = BASE / "comparison_checklist_bxd_32_6.md"
    checklist_lines = [
        "# Checklist doi chung BXD 32,6 m",
        "",
        "| Trạng thái | Hạng mục | Cần kiểm tra | Nguồn |",
        "| --- | --- | --- | --- |",
    ]
    for _, row in checklist.iterrows():
        checklist_lines.append(
            f"| {row['Status']} | {row['Item']} | {row['What_to_check']} | {row['Source']} |"
        )
    checklist_md.write_text("\n".join(checklist_lines), encoding="utf-8")

    print("Wrote", xlsx)
    print("Wrote", md)
    print("Wrote", checklist_md)


def main() -> None:
    summaries = build_summaries()
    comparison = build_comparison(summaries)
    pd.set_option("display.width", 220, "display.max_columns", None)
    print(
        comparison[
            ["Quantity", "Status", "Report_32_6", "MIDAS_Excel", "Difference_pct"]
        ].to_string(index=False)
    )
    write_outputs(comparison, summaries)


if __name__ == "__main__":
    main()
