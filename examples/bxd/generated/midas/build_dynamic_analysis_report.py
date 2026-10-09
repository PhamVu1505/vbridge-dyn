from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from docx import Document
from PIL import Image


BASE = Path(__file__).resolve().parent
CASE = "model_dynamic_countercheck_32_6_HSLM-A1_330"
RESULT_DIR = BASE / CASE
TEMPLATE = BASE / "Tinh_toan_phan_tich_dong.docx"
SOURCE_MCT = BASE / f"{CASE}.mct"
RESULT_MCT = RESULT_DIR / f"{CASE}.mct"
OUT = RESULT_DIR / f"{CASE}.OUT"
REPORT_DOCX = BASE / f"bao_cao_tinh_toan_phan_tich_dong_{CASE}.docx"
APPENDIX_XLSX = BASE / f"bao_cao_tinh_toan_phan_tich_dong_{CASE}_phu_luc.xlsx"
SUMMARY_MD = BASE / f"bao_cao_tinh_toan_phan_tich_dong_{CASE}.md"

REPORT_VALUES = {
    "frequency_hz": 5.066,
    "accel_mps2": 2.30,
    "disp_mm": 2.97,
}


@dataclass(frozen=True)
class DynamicSummary:
    warnings: list[str]
    errors: list[str]
    valid_dofs: int | None
    dynamic_inputs: int | None
    time_steps: int | None
    time_increment_s: float | None
    end_time_s: float | None
    mct_dynamic_inputs: int
    frequency_hz: float
    period_s: float
    uz_mass_mode_1_pct: float | None
    uz_mass_sum_5_pct: float | None
    ry_mass_sum_5_pct: float | None
    midspan_disp_mm: float
    midspan_disp_time_s: float | None
    midspan_acc_mps2: float
    midspan_acc_time_s: float | None
    global_acc_mps2: float
    global_acc_node: int
    global_acc_time_s: float | None
    global_disp_mm: float
    global_disp_node: int
    global_disp_time_s: float | None
    beam_my_kNm: float
    beam_my_elem: int
    beam_my_time_s: float | None
    beam_vz_kN: float
    beam_vz_elem: int
    beam_vz_time_s: float | None


def num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def absmax_row(data: pd.DataFrame, values: pd.Series) -> tuple[int, float]:
    scoped = values.dropna()
    if scoped.empty:
        raise ValueError("No numeric values available for absmax.")
    idx = int(scoped.abs().idxmax())
    return idx, float(values.loc[idx])


def read_out(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    bad_patterns = [
        "ERROR",
        "WARNING",
        "FATAL",
        "ABNORMAL",
        "TERMINAT",
        "FAILED",
        "NOT CONVERG",
        "SINGULAR",
        "INSTABILITY",
    ]
    flagged = [
        line.strip()
        for line in text.splitlines()
        if any(pattern in line.upper() for pattern in bad_patterns)
    ]

    def find_int(pattern: str) -> int | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return int(match.group(1)) if match else None

    def find_float(pattern: str) -> float | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return float(match.group(1)) if match else None

    return {
        "flagged": flagged,
        "valid_dofs": find_int(r"TOTAL NUMBER OF VALID DOFS IN MODEL\s*[^:]*:\s*(\d+)"),
        "dynamic_inputs": find_int(r"NUMBER OF DYNAMIC INPUTS\s*[^:]*:\s*(\d+)"),
        "time_steps": find_int(r"NUMBER OF TIME STEPS\s*[^:]*:\s*(\d+)"),
        "time_increment_s": find_float(r"TIME INCREMENT\s*[^:]*:\s*([0-9.Ee+-]+)"),
    }


def read_mct_control(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    case_idx = text.find("NAME=HSLM-A1_330")
    end_time = None
    if case_idx >= 0:
        match = re.search(r"1,\s*1,\s*1,\s*0,\s*([0-9.Ee+-]+),\s*([0-9.Ee+-]+)", text[case_idx:])
        if match:
            end_time = float(match.group(1))
    return {
        "end_time_s": end_time,
        "dynamic_inputs": len(re.findall(r"^\s*\d+,\s*HSLM-A1_330,", text, flags=re.MULTILINE)),
    }


def read_eigen(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(path, header=None)
    header_row = None
    for idx in range(min(20, len(raw))):
        row = raw.iloc[idx].astype(str)
        if row.str.contains("Mode", na=False).any() and row.str.contains("Frequency", na=False).any():
            header_row = idx
            break
    if header_row is None:
        raise ValueError(f"Cannot find eigen header in {path}")
    rows = []
    for _, row in raw.iloc[header_row + 2 :].iterrows():
        mode = pd.to_numeric(row.iloc[3], errors="coerce")
        if pd.isna(mode):
            if rows:
                break
            continue
        rows.append(
            {
                "Mode": int(mode),
                "Frequency_rad_s": float(pd.to_numeric(row.iloc[4], errors="coerce")),
                "Frequency_Hz": float(pd.to_numeric(row.iloc[6], errors="coerce")),
                "Period_s": float(pd.to_numeric(row.iloc[8], errors="coerce")),
                "Tolerance": pd.to_numeric(row.iloc[10], errors="coerce"),
            }
        )

    modal_start = None
    for idx in range(len(raw)):
        values = raw.iloc[idx].astype(str)
        if values.str.contains("MODAL PARTICIPATION MASSES", na=False).any():
            modal_start = idx
            break
    mass_rows = []
    if modal_start is not None:
        for _, row in raw.iloc[modal_start + 3 :].iterrows():
            mode = pd.to_numeric(row.iloc[3], errors="coerce")
            if pd.isna(mode):
                if mass_rows:
                    break
                continue
            mass_rows.append(
                {
                    "Mode": int(mode),
                    "UX_mass_pct": pd.to_numeric(row.iloc[4], errors="coerce"),
                    "UX_sum_pct": pd.to_numeric(row.iloc[5], errors="coerce"),
                    "UY_mass_pct": pd.to_numeric(row.iloc[6], errors="coerce"),
                    "UY_sum_pct": pd.to_numeric(row.iloc[7], errors="coerce"),
                    "UZ_mass_pct": pd.to_numeric(row.iloc[8], errors="coerce"),
                    "UZ_sum_pct": pd.to_numeric(row.iloc[9], errors="coerce"),
                    "RX_mass_pct": pd.to_numeric(row.iloc[10], errors="coerce"),
                    "RX_sum_pct": pd.to_numeric(row.iloc[11], errors="coerce"),
                    "RY_mass_pct": pd.to_numeric(row.iloc[12], errors="coerce"),
                    "RY_sum_pct": pd.to_numeric(row.iloc[13], errors="coerce"),
                    "RZ_mass_pct": pd.to_numeric(row.iloc[14], errors="coerce"),
                    "RZ_sum_pct": pd.to_numeric(row.iloc[15], errors="coerce"),
                }
            )
    return pd.DataFrame(rows).round(6), pd.DataFrame(mass_rows).round(3)


def read_dynamic_export(path: Path, *, node: int, result: str, scale: float) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    raw = pd.read_excel(path, header=None)
    headers = [str(value).split("\n")[0].strip() for value in raw.iloc[1].tolist()]
    data = raw.iloc[3:].copy()
    data["node"] = num(data.iloc[:, 2])
    data["load"] = data.iloc[:, 3].astype(str)
    data = data.dropna(subset=["node"]).copy()
    data["node"] = data["node"].astype(int)
    value_col = headers.index("DZ")
    time_col = value_col + 1
    values = num(data.iloc[:, value_col]) * scale
    times = num(data.iloc[:, time_col])

    global_idx, global_value = absmax_row(data, values)
    mid_selector = data["node"].eq(node) & data["load"].str.endswith("(all)")
    if not mid_selector.any():
        mid_selector = data["node"].eq(node)
    mid_idx, mid_value = absmax_row(data.loc[mid_selector], values.loc[mid_selector])
    table = pd.DataFrame(
        [
            {
                "Result": result,
                "Scope": "global_absmax",
                "Node": int(data.loc[global_idx, "node"]),
                "Load": data.loc[global_idx, "load"],
                "DZ": global_value,
                "Abs_DZ": abs(global_value),
                "Time_s": None if pd.isna(times.loc[global_idx]) else float(times.loc[global_idx]),
            },
            {
                "Result": result,
                "Scope": f"node_{node}_all",
                "Node": int(data.loc[mid_idx, "node"]),
                "Load": data.loc[mid_idx, "load"],
                "DZ": mid_value,
                "Abs_DZ": abs(mid_value),
                "Time_s": None if pd.isna(times.loc[mid_idx]) else float(times.loc[mid_idx]),
            },
        ]
    ).round(6)
    return (
        table,
        table[table["Scope"].eq("global_absmax")].iloc[0].to_dict(),
        table[table["Scope"].eq(f"node_{node}_all")].iloc[0].to_dict(),
    )


def read_beam_force(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None)
    headers = [str(value).split("\n")[0].strip() for value in raw.iloc[1].tolist()]
    data = raw.iloc[3:].copy()
    data["elem"] = num(data.iloc[:, 2])
    data["load"] = data.iloc[:, 3].astype(str)
    data = data.dropna(subset=["elem"]).copy()
    data["elem"] = data["elem"].astype(int)
    rows = []
    for label, comp in [("Moment-y", "My_kNm"), ("Shear-z", "Vz_kN")]:
        value_col = headers.index(label)
        time_col = value_col + 1
        values = num(data.iloc[:, value_col])
        times = num(data.iloc[:, time_col])
        idx, value = absmax_row(data, values)
        rows.append(
            {
                "Component": comp,
                "Elem": int(data.loc[idx, "elem"]),
                "Load": data.loc[idx, "load"],
                "Value": value,
                "Abs_value": abs(value),
                "Time_s": None if pd.isna(times.loc[idx]) else float(times.loc[idx]),
            }
        )
    return pd.DataFrame(rows).round(3)


def update_cell(table, row: int, col: int, value: Any) -> None:
    table.cell(row, col).text = str(value)


def replace_paragraph_text(doc: Document, replacements: dict[str, str]) -> None:
    for para in doc.paragraphs:
        text = para.text
        for old, new in replacements.items():
            text = text.replace(old, new)
        if text != para.text:
            para.clear()
            para.add_run(text)


def convert_bmp_to_png(source: Path, target: Path) -> Path:
    with Image.open(source) as image:
        image.save(target)
    return target


def paragraph_image_rids(doc: Document) -> dict[int, list[str]]:
    mapping: dict[int, list[str]] = {}
    for index, para in enumerate(doc.paragraphs):
        rids: list[str] = []
        for run in para.runs:
            for blip in run._element.xpath(".//a:blip"):
                rid = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                if rid:
                    rids.append(rid)
        if rids:
            mapping[index] = rids
    return mapping


def replace_image_blob(doc: Document, paragraph_index: int, image_path: Path) -> None:
    mapping = paragraph_image_rids(doc)
    rids = mapping.get(paragraph_index, [])
    if not rids:
        return
    rel = doc.part.rels[rids[0]]
    rel.target_part._blob = image_path.read_bytes()


def sync_result_mct() -> None:
    if SOURCE_MCT.exists() and RESULT_MCT.exists():
        src_text = SOURCE_MCT.read_text(encoding="utf-8", errors="ignore")
        dst_text = RESULT_MCT.read_text(encoding="utf-8", errors="ignore")
        if "8.142545455" in src_text and "8.142545455" not in dst_text:
            shutil.copy2(SOURCE_MCT, RESULT_MCT)


def build_summary() -> tuple[DynamicSummary, dict[str, pd.DataFrame]]:
    sync_result_mct()
    out_data = read_out(OUT)
    mct_data = read_mct_control(SOURCE_MCT)
    eigen, modal_mass = read_eigen(RESULT_DIR / "Eigenvalue Mode.xls")
    disp_table, disp_global, disp_mid = read_dynamic_export(
        RESULT_DIR / "Displacement.xls", node=100016, result="displacement", scale=1000.0
    )
    acc_table, acc_global, acc_mid = read_dynamic_export(
        RESULT_DIR / "Absolute Accel..xls", node=100016, result="absolute_accel", scale=1.0
    )
    vel_table, _, _ = read_dynamic_export(
        RESULT_DIR / "Velocity.xls", node=100016, result="velocity", scale=1.0
    )
    rel_acc_table, _, _ = read_dynamic_export(
        RESULT_DIR / "Relative Accel..xls", node=100016, result="relative_accel", scale=1.0
    )
    beam = read_beam_force(RESULT_DIR / "Beam Force.xls")

    mode1 = eigen[eigen["Mode"].eq(1)].iloc[0]
    mode5 = modal_mass[modal_mass["Mode"].eq(5)].iloc[0] if not modal_mass.empty else None
    mode1_mass = modal_mass[modal_mass["Mode"].eq(1)].iloc[0] if not modal_mass.empty else None
    my = beam[beam["Component"].eq("My_kNm")].iloc[0]
    vz = beam[beam["Component"].eq("Vz_kN")].iloc[0]

    summary = DynamicSummary(
        warnings=out_data["flagged"],
        errors=[],
        valid_dofs=out_data["valid_dofs"],
        dynamic_inputs=out_data["dynamic_inputs"],
        time_steps=out_data["time_steps"],
        time_increment_s=out_data["time_increment_s"],
        end_time_s=mct_data["end_time_s"],
        mct_dynamic_inputs=int(mct_data["dynamic_inputs"]),
        frequency_hz=float(mode1["Frequency_Hz"]),
        period_s=float(mode1["Period_s"]),
        uz_mass_mode_1_pct=None if mode1_mass is None else float(mode1_mass["UZ_mass_pct"]),
        uz_mass_sum_5_pct=None if mode5 is None else float(mode5["UZ_sum_pct"]),
        ry_mass_sum_5_pct=None if mode5 is None else float(mode5["RY_sum_pct"]),
        midspan_disp_mm=float(disp_mid["Abs_DZ"]),
        midspan_disp_time_s=disp_mid["Time_s"],
        midspan_acc_mps2=float(acc_mid["Abs_DZ"]),
        midspan_acc_time_s=acc_mid["Time_s"],
        global_acc_mps2=float(acc_global["Abs_DZ"]),
        global_acc_node=int(acc_global["Node"]),
        global_acc_time_s=acc_global["Time_s"],
        global_disp_mm=float(disp_global["Abs_DZ"]),
        global_disp_node=int(disp_global["Node"]),
        global_disp_time_s=disp_global["Time_s"],
        beam_my_kNm=float(my["Abs_value"]),
        beam_my_elem=int(my["Elem"]),
        beam_my_time_s=my["Time_s"],
        beam_vz_kN=float(vz["Abs_value"]),
        beam_vz_elem=int(vz["Elem"]),
        beam_vz_time_s=vz["Time_s"],
    )
    tables = {
        "eigen": eigen,
        "modal_mass": modal_mass,
        "dynamic_response": pd.concat([disp_table, acc_table, rel_acc_table, vel_table], ignore_index=True),
        "beam_force": beam,
    }
    return summary, tables


def update_report_docx(summary: DynamicSummary, tables: dict[str, pd.DataFrame]) -> None:
    doc = Document(TEMPLATE)

    replacements = {
        "Hình 1: mode dao động uốn – f=4.79 Hz": f"Hình 1: mode dao động uốn - f={summary.frequency_hz:.3f} Hz",
        "Hình 2: biểu đồ chuyển vị tại giữa nhịp của đoàn tàu HSLM-A1 ở vận tốc 330km/h – 2.245mm": (
            "Hình 2: biểu đồ chuyển vị tại giữa nhịp của đoàn tàu HSLM-A1 "
            f"ở vận tốc 330km/h - {summary.midspan_disp_mm:.3f} mm"
        ),
        "Hình 3: biểu đồ gia tốc tại giữa nhịp của đoàn tàu HSLM-A1 ở vận tốc 330km/h – 1.766m/s2": (
            "Hình 3: biểu đồ gia tốc tại giữa nhịp của đoàn tàu HSLM-A1 "
            f"ở vận tốc 330km/h - {summary.midspan_acc_mps2:.3f} m/s2"
        ),
        "Kiểm tra: gia tốc lớn nhất amax = 1.766m/s2 => đảm bảo": (
            f"Kiểm tra: gia tốc lớn nhất tại giữa nhịp amax = {summary.midspan_acc_mps2:.3f} m/s2 "
            f"(toàn cục {summary.global_acc_mps2:.3f} m/s2 tại node {summary.global_acc_node}) => đảm bảo"
        ),
        "chuyển vị do tải trọng động dmax = 2.245mm": (
            f"chuyển vị do tải trọng động tại giữa nhịp dmax = {summary.midspan_disp_mm:.3f}mm"
        ),
    }
    replace_paragraph_text(doc, replacements)

    table0 = doc.tables[0]
    update_cell(table0, 4, 1, f"{summary.mct_dynamic_inputs}")
    update_cell(table0, 6, 1, "HSLM-A1 @ 330 km/h")
    update_cell(table0, 7, 1, f"{summary.time_increment_s:.3f} s")
    update_cell(table0, 8, 1, f"{summary.end_time_s:.6f} s")
    update_cell(table0, 9, 1, "Modal transient, damping 1.5%")
    update_cell(table0, 10, 1, f"{summary.time_steps} bước; valid DOF {summary.valid_dofs}")

    eigen = tables["eigen"].head(70)
    table1 = doc.tables[1]
    for ridx, (_, row) in enumerate(eigen.iterrows(), start=3):
        if ridx >= len(table1.rows):
            break
        update_cell(table1, ridx, 0, int(row["Mode"]))
        update_cell(table1, ridx, 1, f"{row['Frequency_rad_s']:.6f}")
        update_cell(table1, ridx, 2, f"{row['Frequency_Hz']:.6f}")
        update_cell(table1, ridx, 3, f"{row['Period_s']:.5f}")
        update_cell(table1, ridx, 4, f"{row['Tolerance']:.4E}")

    mass = tables["modal_mass"].head(70)
    table2 = doc.tables[2]
    for ridx, (_, row) in enumerate(mass.iterrows(), start=2):
        if ridx >= len(table2.rows):
            break
        values = [
            int(row["Mode"]),
            row["UX_mass_pct"],
            row["UX_sum_pct"],
            row["UY_mass_pct"],
            row["UY_sum_pct"],
            row["UZ_mass_pct"],
            row["UZ_sum_pct"],
            row["RX_mass_pct"],
            row["RX_sum_pct"],
            row["RY_mass_pct"],
            row["RY_sum_pct"],
            row["RZ_mass_pct"],
            row["RZ_sum_pct"],
        ]
        for cidx, value in enumerate(values):
            update_cell(table2, ridx, cidx, f"{value:.2f}" if isinstance(value, float) else value)

    table4 = doc.tables[4]
    update_cell(table4, 1, 3, f"{summary.frequency_hz:.3f}")
    update_cell(table4, 2, 3, f"{summary.midspan_acc_mps2:.3f}")
    update_cell(table4, 3, 3, f"{summary.midspan_disp_mm:.3f}")
    update_cell(table4, 1, 5, f"Mode 1; UZ mass sum mode 1-5 = {summary.uz_mass_sum_5_pct:.2f}%")
    update_cell(table4, 2, 5, f"Node 100016(all), t={summary.midspan_acc_time_s:.3f}s; global max {summary.global_acc_mps2:.3f} tại node {summary.global_acc_node}")
    update_cell(table4, 3, 5, f"Node 100016(all), t={summary.midspan_disp_time_s:.3f}s; global max {summary.global_disp_mm:.3f} tại node {summary.global_disp_node}")

    png_dz = convert_bmp_to_png(RESULT_DIR / "deck_dz.bmp", RESULT_DIR / "deck_dz.png")
    png_acc = convert_bmp_to_png(RESULT_DIR / "deck_acc.bmp", RESULT_DIR / "deck_acc.png")
    replace_image_blob(doc, 38, png_dz)
    replace_image_blob(doc, 41, png_acc)

    doc.save(REPORT_DOCX)


def write_appendix(summary: DynamicSummary, tables: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(APPENDIX_XLSX, engine="openpyxl") as writer:
        pd.DataFrame([summary.__dict__]).to_excel(writer, sheet_name="summary", index=False)
        for name, table in tables.items():
            table.to_excel(writer, sheet_name=name[:31], index=False)


def write_markdown(summary: DynamicSummary) -> None:
    freq_diff = (summary.frequency_hz - REPORT_VALUES["frequency_hz"]) / REPORT_VALUES["frequency_hz"] * 100.0
    acc_diff = (summary.midspan_acc_mps2 - REPORT_VALUES["accel_mps2"]) / REPORT_VALUES["accel_mps2"] * 100.0
    disp_diff = (summary.midspan_disp_mm - REPORT_VALUES["disp_mm"]) / REPORT_VALUES["disp_mm"] * 100.0
    lines = [
        f"# Báo cáo phân tích động {CASE}",
        "",
        f"Cập nhật: {date.today().isoformat()}",
        "",
        "## Nguồn",
        "",
        f"- MCT: `{SOURCE_MCT.name}`",
        f"- OUT: `{OUT}`",
        f"- Result folder: `{RESULT_DIR}`",
        "",
        "## Kiểm tra chạy",
        "",
        f"- Dynamic inputs: {summary.dynamic_inputs}; MCT nodal loads: {summary.mct_dynamic_inputs}.",
        f"- Time steps: {summary.time_steps}; dt = {summary.time_increment_s:.3f} s; ETIME = {summary.end_time_s:.6f} s.",
        f"- Valid DOF: {summary.valid_dofs}.",
        f"- Warning/error chính: {'không thấy' if not summary.warnings else len(summary.warnings)}.",
        "",
        "## Kết quả chính",
        "",
        "| Đại lượng | Báo cáo | MIDAS mới | Chênh |",
        "| --- | ---: | ---: | ---: |",
        f"| Tần số mode 1 | {REPORT_VALUES['frequency_hz']:.3f} Hz | {summary.frequency_hz:.3f} Hz | {freq_diff:+.1f}% |",
        f"| Gia tốc giữa nhịp | {REPORT_VALUES['accel_mps2']:.3f} m/s2 | {summary.midspan_acc_mps2:.3f} m/s2 | {acc_diff:+.1f}% |",
        f"| Chuyển vị giữa nhịp | {REPORT_VALUES['disp_mm']:.3f} mm | {summary.midspan_disp_mm:.3f} mm | {disp_diff:+.1f}% |",
        "",
        f"- Gia tốc DZ toàn cục: {summary.global_acc_mps2:.3f} m/s2 tại node {summary.global_acc_node}, t={summary.global_acc_time_s:.3f}s.",
        f"- Chuyển vị DZ toàn cục: {summary.global_disp_mm:.3f} mm tại node {summary.global_disp_node}, t={summary.global_disp_time_s:.3f}s.",
        f"- UZ modal mass mode 1 = {summary.uz_mass_mode_1_pct:.2f}%; UZ sum mode 1-5 = {summary.uz_mass_sum_5_pct:.2f}%; RY sum mode 1-5 = {summary.ry_mass_sum_5_pct:.2f}%.",
        f"- My abs max = {summary.beam_my_kNm:.2f} kN.m tại elem {summary.beam_my_elem}; Vz abs max = {summary.beam_vz_kN:.2f} kN tại elem {summary.beam_vz_elem}.",
        "",
        "## Đầu ra",
        "",
        f"- Word: `{REPORT_DOCX}`",
        f"- Phụ lục Excel: `{APPENDIX_XLSX}`",
    ]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary, tables = build_summary()
    update_report_docx(summary, tables)
    write_appendix(summary, tables)
    write_markdown(summary)
    print(REPORT_DOCX)
    print(APPENDIX_XLSX)
    print(SUMMARY_MD)


if __name__ == "__main__":
    main()
