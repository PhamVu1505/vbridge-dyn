from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

BASE = Path(__file__).resolve().parent
PROJECT_DIR = BASE.parents[1]
MCT = BASE / "model_static_countercheck_32_6.mct"
CONFIG = PROJECT_DIR / "static_countercheck_32_6.yaml"
COMPARISON_XLSX = BASE / "comparison_bxd_32_6.xlsx"
REPORT_DOCX = BASE / "bao_cao_tinh_toan_midas_bxd_32_6.docx"
APPENDIX_XLSX = BASE / "bao_cao_tinh_toan_midas_bxd_32_6_phu_luc.xlsx"
TENDON_FIG = BASE / "tendon_layout_bxd_32_6.png"
RM_REFERENCE = BASE / "report refer RM bridge" / "report.pdf"


REPORT_SOURCES = [
    {
        "Nguon": "MIDAS Dynamic Report",
        "Noi_dung_ap_dung": "Report gom input/output, material, section, boundary, load combination, reactions, member forces, displacements, stresses; co the xuat Word.",
        "URL": "https://support.midasuser.com/hc/en-us/articles/24721486569369-Dynamic-Report",
    },
    {
        "Nguon": "SOFiSTiK Report Browser",
        "Noi_dung_ap_dung": "Report tinh toan nen tong hop thong tin phan tich va ket qua bang text, bang bieu va do hoa.",
        "URL": "https://docs.sofistik.com/2026/en/analysis_and_design/cmdref/current_system/report_browser.html",
    },
    {
        "Nguon": "CSI/SAP2000 Reporting FAQ",
        "Noi_dung_ap_dung": "Bang model definition, load pattern, response combination va ket qua co the in/xuat de hau xu ly.",
        "URL": "https://web.wiki.csiamerica.com/wiki/spaces/kb/pages/2002913/Reporting%2BFAQ",
    },
    {
        "Nguon": "SAP2000 Load Combination",
        "Noi_dung_ap_dung": "Load combinations co the do chuong trinh sinh hoac nguoi dung dinh nghia; can trinh bay ro cac thanh phan va he so.",
        "URL": "https://help.csiamerica.com/help/sap2000/26/26.0.0/SAP2000/WebHelp/Menus/Define/Load_Combination/Load_Combination.htm",
    },
    {
        "Nguon": "RM Bridge calculation report reference",
        "Noi_dung_ap_dung": "Bo cuc bao cao du lieu mo hinh -> spring/support -> section -> load case -> stage -> results.",
        "URL": str(RM_REFERENCE),
    },
]


def load_config() -> dict[str, Any]:
    try:
        import yaml

        return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def split_fields(line: str) -> list[str]:
    return [field.strip() for field in line.strip().rstrip(",").split(",")]


def is_float(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def floats_from_line(line: str) -> list[float]:
    out = []
    for field in split_fields(line):
        if is_float(field):
            out.append(float(field))
    return out


def mct_blocks() -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in MCT.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("*"):
            current = {"cmd": line.split()[0], "header": line, "lines": []}
            blocks.append(current)
        elif current is not None:
            current["lines"].append(line)
    return blocks


def data_lines(block: dict[str, Any]) -> list[str]:
    return [
        line.strip()
        for line in block["lines"]
        if line.strip() and not line.strip().startswith(";")
    ]


def blocks_by_cmd(blocks: list[dict[str, Any]], cmd: str) -> list[dict[str, Any]]:
    return [block for block in blocks if block["cmd"].upper() == cmd.upper()]


def parse_nodes(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for block in blocks_by_cmd(blocks, "*NODE"):
        for line in data_lines(block):
            fields = split_fields(line)
            if len(fields) >= 4 and fields[0].isdigit():
                node = int(fields[0])
                rows.append(
                    {
                        "Node": node,
                        "Girder": node // 100000,
                        "Local": node % 100000,
                        "X_m": float(fields[1]),
                        "Y_m": float(fields[2]),
                        "Z_m": float(fields[3]),
                    }
                )
    return pd.DataFrame(rows)


def parse_elements(blocks: list[dict[str, Any]], nodes: pd.DataFrame) -> pd.DataFrame:
    node_lookup = nodes.set_index("Node")[["X_m", "Y_m", "Z_m"]].to_dict("index")
    rows = []
    for block in blocks_by_cmd(blocks, "*ELEMENT"):
        for line in data_lines(block):
            fields = split_fields(line)
            if len(fields) >= 6 and fields[0].isdigit():
                eid = int(fields[0])
                n1 = int(fields[4])
                n2 = int(fields[5])
                p1 = node_lookup.get(n1, {})
                p2 = node_lookup.get(n2, {})
                length = None
                if p1 and p2:
                    length = (
                        (p2["X_m"] - p1["X_m"]) ** 2
                        + (p2["Y_m"] - p1["Y_m"]) ** 2
                        + (p2["Z_m"] - p1["Z_m"]) ** 2
                    ) ** 0.5
                rows.append(
                    {
                        "Elem": eid,
                        "Girder": eid // 100000,
                        "Local": eid % 100000,
                        "Type": fields[1],
                        "Material": int(fields[2]),
                        "Section": int(fields[3]),
                        "Node_I": n1,
                        "Node_J": n2,
                        "Length_m": None if length is None else round(length, 6),
                    }
                )
    return pd.DataFrame(rows)


def parse_materials(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for block in blocks_by_cmd(blocks, "*MATERIAL"):
        for line in data_lines(block):
            fields = split_fields(line)
            if len(fields) >= 15 and fields[0].isdigit():
                rows.append(
                    {
                        "Mat": int(fields[0]),
                        "Type": fields[1],
                        "Name": fields[2],
                        "E_kN_m2": float(fields[10]),
                        "E_MPa": round(float(fields[10]) / 1000.0, 3),
                        "Poisson": float(fields[11]),
                        "Thermal": float(fields[12]),
                        "UnitWeight_kN_m3": float(fields[13]),
                    }
                )
    return pd.DataFrame(rows)


def parse_time_dependent(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for cmd in ["*TDM-TYPE", "*TDM-ELAST", "*TDM-LINK"]:
        for block in blocks_by_cmd(blocks, cmd):
            for line in data_lines(block):
                rows.append({"Command": cmd, "Data": line})
    return pd.DataFrame(rows)


def parse_sections(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    section_blocks = blocks_by_cmd(blocks, "*SECT-PSCVALUE")
    if not section_blocks:
        return pd.DataFrame()
    lines = data_lines(section_blocks[0])
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.startswith("SECT="):
            idx += 1
            continue
        header = split_fields(line.replace("SECT=", ""))
        sec = int(header[0])
        sec_type = header[1]
        name = header[2]
        start_geom = floats_from_line(lines[idx + 1]) if idx + 1 < len(lines) else []
        start_fiber = floats_from_line(lines[idx + 2]) if idx + 2 < len(lines) else []
        end_geom: list[float] = []
        end_fiber: list[float] = []
        if sec_type.upper().startswith("TAPER") and idx + 4 < len(lines):
            end_geom = floats_from_line(lines[idx + 4])
            end_fiber = floats_from_line(lines[idx + 5])
        row = {
            "Section": sec,
            "Name": name,
            "Type": sec_type,
            "Area_start_m2": start_geom[0] if len(start_geom) > 0 else None,
            "Ixx_start_m4": start_geom[3] if len(start_geom) > 3 else None,
            "Iyy_start_m4": start_geom[4] if len(start_geom) > 4 else None,
            "Izz_start_m4": start_geom[5] if len(start_geom) > 5 else None,
            "Cz_top_start_m": start_fiber[2] if len(start_fiber) > 2 else None,
            "Cz_bot_start_m": start_fiber[3] if len(start_fiber) > 3 else None,
            "Area_end_m2": end_geom[0] if len(end_geom) > 0 else None,
            "Ixx_end_m4": end_geom[3] if len(end_geom) > 3 else None,
            "Iyy_end_m4": end_geom[4] if len(end_geom) > 4 else None,
            "Izz_end_m4": end_geom[5] if len(end_geom) > 5 else None,
            "Cz_top_end_m": end_fiber[2] if len(end_fiber) > 2 else None,
            "Cz_bot_end_m": end_fiber[3] if len(end_fiber) > 3 else None,
        }
        rows.append(row)
        idx += 1
    return pd.DataFrame(rows).round(6)


def parse_taper_groups(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for block in blocks_by_cmd(blocks, "*TS-GROUP"):
        for line in data_lines(block):
            fields = split_fields(line)
            if len(fields) >= 2:
                rows.append({"Name": fields[0], "Elements": fields[1], "Raw": line})
    return pd.DataFrame(rows)


def decode_constraint(code: str) -> dict[str, str]:
    dofs = ["Dx", "Dy", "Dz", "Rx", "Ry", "Rz"]
    return {dof: ("Fixed" if idx < len(code) and code[idx] == "1" else "Free") for idx, dof in enumerate(dofs)}


def parse_supports(blocks: list[dict[str, Any]], nodes: pd.DataFrame) -> pd.DataFrame:
    node_lookup = nodes.set_index("Node")[["X_m", "Y_m", "Z_m", "Girder", "Local"]].to_dict("index")
    rows = []
    for block in blocks_by_cmd(blocks, "*CONSTRAINT"):
        for line in data_lines(block):
            fields = split_fields(line)
            if len(fields) >= 3 and fields[0].isdigit():
                node = int(fields[0])
                data = node_lookup.get(node, {})
                row = {
                    "Node": node,
                    "Girder": data.get("Girder"),
                    "Local": data.get("Local"),
                    "X_m": data.get("X_m"),
                    "Y_m": data.get("Y_m"),
                    "Z_m": data.get("Z_m"),
                    "Constraint": fields[1],
                    "Group": fields[2],
                }
                row.update(decode_constraint(fields[1]))
                rows.append(row)
    return pd.DataFrame(rows)


def parse_static_load_cases(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for block in blocks_by_cmd(blocks, "*STLDCASE"):
        for line in data_lines(block):
            fields = split_fields(line)
            if len(fields) >= 2 and not fields[0].startswith("*"):
                rows.append({"LoadCase": fields[0], "Type": fields[1], "Description": fields[2] if len(fields) > 2 else ""})
    return pd.DataFrame(rows).drop_duplicates()


def parse_tendon_property(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for block in blocks_by_cmd(blocks, "*TDN-PROPERTY"):
        for line in data_lines(block):
            fields = split_fields(line)
            if len(fields) >= 12:
                rows.append(
                    {
                        "Name": fields[0],
                        "Type": fields[1],
                        "Material": fields[2],
                        "Area_m2": float(fields[3]),
                        "DuctDia_m": float(fields[4]),
                        "Relaxation": fields[5],
                        "FrictionCurvature": fields[7],
                        "FrictionWobble": fields[8],
                        "Ultimate_kN_m2": fields[9],
                        "Yield_kN_m2": fields[10],
                        "System": fields[11],
                    }
                )
    return pd.DataFrame(rows)


def parse_tendon_profiles(blocks: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    profiles: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []
    for block in blocks_by_cmd(blocks, "*TDN-PROFILE"):
        current: dict[str, Any] | None = None
        for line in data_lines(block):
            if line.startswith("NAME="):
                fields = split_fields(line.replace("NAME=", ""))
                current = {
                    "Tendon": fields[0],
                    "Property": fields[1] if len(fields) > 1 else "",
                    "Elements": fields[2] if len(fields) > 2 else "",
                    "Girder": fields[0].split("-")[0] if "-" in fields[0] else "",
                    "GroupName": fields[0].split("-")[1][:2] if "-" in fields[0] else "",
                    "n_points": 0,
                    "x_min_m": None,
                    "x_max_m": None,
                    "y_min_m": None,
                    "y_max_m": None,
                    "z_min_m": None,
                    "z_max_m": None,
                }
                profiles.append(current)
                continue
            if current is None:
                continue
            fields = split_fields(line)
            if len(fields) >= 3 and is_float(fields[0]) and is_float(fields[1]) and is_float(fields[2]):
                point = {
                    "Tendon": current["Tendon"],
                    "Girder": current["Girder"],
                    "x_m": float(fields[0]),
                    "y_m": float(fields[1]),
                    "z_m": float(fields[2]),
                }
                points.append(point)
                vals = [p for p in points if p["Tendon"] == current["Tendon"]]
                current["n_points"] = len(vals)
                for axis in ["x", "y", "z"]:
                    current[f"{axis}_min_m"] = min(p[f"{axis}_m"] for p in vals)
                    current[f"{axis}_max_m"] = max(p[f"{axis}_m"] for p in vals)
    return pd.DataFrame(profiles), pd.DataFrame(points)


def parse_tendon_prestress(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for block in blocks_by_cmd(blocks, "*TDN-PRESTRESS"):
        for line in data_lines(block):
            fields = split_fields(line)
            if len(fields) >= 7:
                rows.append(
                    {
                        "Tendon": fields[0],
                        "InputType": fields[1],
                        "Jacking": fields[2],
                        "Begin_kN": float(fields[3]),
                        "End_kN": float(fields[4]),
                        "Grouting": fields[5],
                        "LoadGroup": fields[6],
                    }
                )
    return pd.DataFrame(rows)


def parse_stages(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    current: dict[str, Any] | None = None
    for block in blocks_by_cmd(blocks, "*STAGE"):
        for line in data_lines(block):
            if line.startswith("NAME="):
                fields = split_fields(line.replace("NAME=", ""))
                current = {"Stage": fields[0], "Duration_days": float(fields[1]), "AELEM": "", "ABNDR": "", "ALOAD": "", "STEP": ""}
                rows.append(current)
            elif current is not None:
                key = line.split("=", 1)[0].strip()
                if key in current:
                    current[key] = line.split("=", 1)[1].strip()
    return pd.DataFrame(rows)


def parse_moving_loads(blocks: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    lanes = []
    vehicles = []
    cases = []
    for block in blocks_by_cmd(blocks, "*LINELANE"):
        for line in data_lines(block):
            if line.startswith("NAME="):
                fields = split_fields(line.replace("NAME=", ""))
                lanes.append({"Lane": fields[0], "Type": fields[1], "Moving": fields[5], "LaneWidth_m": fields[6], "Raw": line})
    for block in blocks_by_cmd(blocks, "*VEHICLE"):
        for line in data_lines(block):
            if line.startswith("NAME="):
                fields = split_fields(line.replace("NAME=", ""))
                vehicles.append({"Vehicle": fields[0], "DBName": fields[3] if len(fields) > 3 else "", "Alpha": fields[11] if len(fields) > 11 else "", "Raw": line})
    for block in blocks_by_cmd(blocks, "*MVLDCASE(EURO)"):
        current = None
        for line in data_lines(block):
            if line.startswith("NAME="):
                fields = split_fields(line.replace("NAME=", ""))
                current = {"Case": fields[0], "Raw": line, "VehicleLine": ""}
                cases.append(current)
            elif current is not None:
                current["VehicleLine"] = line
    return pd.DataFrame(lanes), pd.DataFrame(vehicles), pd.DataFrame(cases)


def parse_load_combinations(blocks: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    current: dict[str, Any] | None = None
    for block in blocks_by_cmd(blocks, "*LOADCOMB"):
        for line in data_lines(block):
            if line.startswith("NAME="):
                fields = split_fields(line.replace("NAME=", ""))
                current = {"Combination": fields[0], "Description": fields[5] if len(fields) > 5 else "", "Terms": ""}
                rows.append(current)
            elif current is not None:
                current["Terms"] = (current["Terms"] + " " + line).strip()
    return pd.DataFrame(rows)


def build_load_summary(config: dict[str, Any], static_cases: pd.DataFrame, vehicles: pd.DataFrame, moving_cases: pd.DataFrame) -> pd.DataFrame:
    loads = config.get("loads", {})
    prestress = config.get("prestress", {})
    rows = [
        {"Load": "SelfWeight", "Type": "Dead", "Summary": "MIDAS self-weight from geometry, material unit weight 25 kN/m3."},
        {"Load": "G2_REPORT", "Type": "Dead", "Summary": f"Uniform beam load GZ = {-float(loads.get('g2_superimposed_dead_kn_per_m', 0)):.3f} kN/m."},
        {"Load": "Prestress", "Type": "Prestress", "Summary": f"{prestress.get('tendon_count_per_girder', '')} tendons/girder, {prestress.get('strands_per_tendon', '')} strands/tendon, jacking force {prestress.get('tendon_force_kn', '')} kN/tendon."},
        {"Load": "TRANSPORT", "Type": "Nodal axle", "Summary": f"{loads.get('transport', {}).get('axle_count', '')} axles x {loads.get('transport', {}).get('axle_load_kn', '')} kN, spacing {loads.get('transport', {}).get('axle_spacing_m', '')} m."},
        {"Load": "TRANSPORT_DYN", "Type": "Nodal axle", "Summary": f"TRANSPORT x dynamic factor {loads.get('transport', {}).get('dynamic_factor', '')}."},
        {"Load": "WIND_Y_REPORT", "Type": "Beam uniform", "Summary": f"Total transverse wind {loads.get('wind', {}).get('total_transverse_kn', '')} kN distributed to girders/elements."},
    ]
    for _, row in vehicles.iterrows():
        rows.append({"Load": row["Vehicle"], "Type": "Moving vehicle", "Summary": row["Raw"]})
    for _, row in moving_cases.iterrows():
        rows.append({"Load": row["Case"], "Type": "Moving load case", "Summary": row["VehicleLine"]})
    for _, row in static_cases.iterrows():
        if row["LoadCase"] not in {item["Load"] for item in rows}:
            rows.append({"Load": row["LoadCase"], "Type": row["Type"], "Summary": row["Description"]})
    return pd.DataFrame(rows)


def fmt(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:,.3f}"
    return str(value)


def set_cell(cell, text: object, *, bold: bool = False, size: int = 7) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(fmt(text))
    run.bold = bold
    run.font.size = Pt(size)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_df_table(doc: Document, df: pd.DataFrame, columns: list[str] | None = None, max_rows: int = 25, font_size: int = 7) -> None:
    if df.empty:
        doc.add_paragraph("Không có dữ liệu.")
        return
    view = df.copy()
    if columns is not None:
        view = view[[col for col in columns if col in view.columns]]
    if max_rows and len(view) > max_rows:
        view = view.head(max_rows).copy()
    table = doc.add_table(rows=1, cols=len(view.columns))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for idx, col in enumerate(view.columns):
        set_cell(table.rows[0].cells[idx], col, bold=True, size=font_size)
    for _, row in view.iterrows():
        cells = table.add_row().cells
        for idx, col in enumerate(view.columns):
            set_cell(cells[idx], row[col], size=font_size)


def add_bullet(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.add_run(text)


def add_field(paragraph, field: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = field
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(end)


def setup_document(doc: Document) -> None:
    section = doc.sections[0]
    section.orientation = WD_ORIENT.PORTRAIT
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(1.6)
    section.right_margin = Cm(1.3)
    section.header_distance = Cm(0.7)
    section.footer_distance = Cm(0.7)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(10)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.add_run("BXD 32,6 m - Báo cáo tính toán mô hình MIDAS").bold = True

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Trang ")
    add_field(footer, "PAGE")
    footer.add_run(" / ")
    add_field(footer, "NUMPAGES")
    footer.add_run(f" | Nguồn: {MCT.name}")


def add_cover(doc: Document) -> None:
    title = doc.add_heading("Báo cáo tính toán mô hình MIDAS", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Dầm BXD 32,6 m - mô hình đối chứng 5 dầm")
    run.bold = True
    run.font.size = Pt(14)
    doc.add_paragraph(f"Ngày tạo báo cáo: {date.today().isoformat()}")
    doc.add_paragraph(f"Nguồn MCT: {MCT}")
    doc.add_paragraph(f"Nguồn dữ liệu so sánh: {COMPARISON_XLSX}")
    doc.add_paragraph(f"Phụ lục dữ liệu đầy đủ: {APPENDIX_XLSX}")
    doc.add_paragraph(f"Mẫu trình bày tham khảo: {RM_REFERENCE}")
    doc.add_paragraph(
        "Phạm vi: mô hình đối chứng tĩnh 5 dầm 32,6 m, bỏ qua trụ/móng, "
        "dùng kết quả MIDAS export mới nhất trong thư mục generated/midas."
    )


def add_manual_toc(doc: Document) -> pd.DataFrame:
    outline = pd.DataFrame(
        [
            {"Mục": "1", "Nội dung": "Mô hình tính"},
            {"Mục": "1.1", "Nội dung": "Tổng quan mô hình"},
            {"Mục": "1.2", "Nội dung": "Node - tọa độ"},
            {"Mục": "1.3", "Nội dung": "Element - tham số phần tử"},
            {"Mục": "1.4", "Nội dung": "Liên kết và support"},
            {"Mục": "1.5", "Nội dung": "Vật liệu và đặc trưng theo thời gian"},
            {"Mục": "1.6", "Nội dung": "Mặt cắt và taper group"},
            {"Mục": "1.7", "Nội dung": "Cáp dự ứng lực"},
            {"Mục": "1.8", "Nội dung": "Tải trọng và load case"},
            {"Mục": "1.9", "Nội dung": "Stage thi công"},
            {"Mục": "1.10", "Nội dung": "Tổ hợp tải trọng và quy tắc max/min"},
            {"Mục": "2", "Nội dung": "Kết quả tính toán"},
            {"Mục": "2.1", "Nội dung": "Nội lực và phản lực gối"},
            {"Mục": "2.2", "Nội dung": "Ứng suất"},
            {"Mục": "2.3", "Nội dung": "Độ võng, độ vồng và góc xoay đầu dầm"},
            {"Mục": "2.4", "Nội dung": "Mỏi"},
            {"Mục": "2.5", "Nội dung": "Checklist và các mục cần tiếp tục"},
            {"Mục": "3", "Nội dung": "Phụ lục kết quả"},
        ]
    )
    doc.add_heading("Mục lục nội dung", level=1)
    add_df_table(doc, outline, max_rows=40, font_size=8)
    return outline


def support_interpretation_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Constraint": "111100",
                "Vị trí áp dụng": "Node local 2 của mỗi dầm",
                "Bậc tự do khóa": "Dx, Dy, Dz, Rx",
                "Bậc tự do mở": "Ry, Rz",
                "Diễn giải": "Gối khống chế chuyển vị dọc, ngang, đứng và xoay quanh trục dọc.",
            },
            {
                "Constraint": "011100",
                "Vị trí áp dụng": "Node local 30 của mỗi dầm",
                "Bậc tự do khóa": "Dy, Dz, Rx",
                "Bậc tự do mở": "Dx, Ry, Rz",
                "Diễn giải": "Gối di động theo phương dọc dầm, vẫn khống chế ngang/đứng.",
            },
        ]
    )


def add_comparison_section(doc: Document, title: str, comparison: pd.DataFrame, mask: pd.Series) -> None:
    doc.add_heading(title, level=2)
    cols = [
        "Group",
        "Quantity",
        "Status",
        "Unit",
        "Report_source",
        "Report_32_6",
        "MIDAS_Excel",
        "Difference_pct",
        "MIDAS_source",
        "Comment",
    ]
    add_df_table(doc, comparison.loc[mask, cols], max_rows=30, font_size=6)


def build_tendon_figure(points: pd.DataFrame) -> None:
    if points.empty:
        return
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return
    g1 = points[points["Girder"].eq("G1")]
    if g1.empty:
        return
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 5.0), sharex=True)
    for _, group in g1.groupby("Tendon"):
        axes[0].plot(group["x_m"], group["z_m"], linewidth=0.8)
        axes[1].plot(group["x_m"], group["y_m"], linewidth=0.8)
    axes[0].set_ylabel("z tendon (m)")
    axes[0].set_title("Sơ đồ mặt đứng cáp DUL - dầm G1")
    axes[1].set_ylabel("y tendon (m)")
    axes[1].set_xlabel("x dọc dầm (m)")
    axes[1].set_title("Sơ đồ mặt bằng cáp DUL - dầm G1")
    for ax in axes:
        ax.grid(True, linewidth=0.3)
    fig.tight_layout()
    fig.savefig(TENDON_FIG, dpi=180)
    plt.close(fig)


def write_appendix(tables: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(APPENDIX_XLSX, engine="openpyxl") as writer:
        for sheet, df in tables.items():
            safe = sheet[:31].replace(":", "_").replace("/", "_")
            df.to_excel(writer, sheet_name=safe, index=False)


def main() -> None:
    config = load_config()
    blocks = mct_blocks()
    nodes = parse_nodes(blocks)
    elements = parse_elements(blocks, nodes)
    materials = parse_materials(blocks)
    time_dependent = parse_time_dependent(blocks)
    sections = parse_sections(blocks)
    taper_groups = parse_taper_groups(blocks)
    supports = parse_supports(blocks, nodes)
    static_cases = parse_static_load_cases(blocks)
    tendon_property = parse_tendon_property(blocks)
    tendon_profiles, tendon_points = parse_tendon_profiles(blocks)
    tendon_prestress = parse_tendon_prestress(blocks)
    stages = parse_stages(blocks)
    lanes, vehicles, moving_cases = parse_moving_loads(blocks)
    combinations = parse_load_combinations(blocks)
    load_summary = build_load_summary(config, static_cases, vehicles, moving_cases)

    comparison = pd.read_excel(COMPARISON_XLSX, sheet_name="comparison")
    checklist = pd.read_excel(COMPARISON_XLSX, sheet_name="checklist")
    result_sheets: dict[str, pd.DataFrame] = {}
    xls = pd.ExcelFile(COMPARISON_XLSX)
    for sheet in xls.sheet_names:
        if sheet.startswith("midas_"):
            result_sheets[sheet] = pd.read_excel(COMPARISON_XLSX, sheet_name=sheet)

    node_summary = nodes.groupby("Girder").agg(Node_count=("Node", "count"), X_min_m=("X_m", "min"), X_max_m=("X_m", "max"), Z_m=("Z_m", "mean")).reset_index()
    element_summary = elements.groupby(["Girder", "Section"]).agg(Elem_count=("Elem", "count"), Length_sum_m=("Length_m", "sum")).reset_index().round(3)
    tendon_summary = tendon_profiles.groupby(["Girder", "GroupName"]).agg(Tendon_count=("Tendon", "count"), x_min_m=("x_min_m", "min"), x_max_m=("x_max_m", "max"), y_min_m=("y_min_m", "min"), y_max_m=("y_max_m", "max"), z_min_m=("z_min_m", "min"), z_max_m=("z_max_m", "max")).reset_index().round(3)
    support_summary = supports.groupby(["Girder", "Constraint"]).agg(Support_count=("Node", "count"), Nodes=("Node", lambda x: ", ".join(map(str, x)))).reset_index()
    support_interpretation = support_interpretation_table()
    support_activation = stages[stages["ABNDR"].astype(str).str.contains("Support", na=False)][["Stage", "Duration_days", "ABNDR"]].copy()
    if support_activation.empty:
        support_activation = pd.DataFrame([{"Stage": "", "Duration_days": "", "ABNDR": "Không tìm thấy stage kích hoạt Support"}])
    combo_audit = pd.DataFrame(
        [
            {"Item": "Momen duong / noi luc ULS", "Rule": "Dung envelope (max)"},
            {"Item": "Ung suat cang keo", "Rule": "sigma_bot,min = min Cb3/Cb4"},
            {"Item": "Ung suat khai thac", "Rule": "sigma_bot,max = SLS_CHAR_LM71(max), node x00016"},
            {"Item": "Ung suat thi cong", "Rule": "sigma_bot,max tai node x00016"},
            {"Item": "Ung suat dai han", "Rule": "sigma_top,min = min Cb1/Cb2"},
            {"Item": "Do vong LM71", "Rule": "abs(DZ_min) cua LM71_2T(min)"},
            {"Item": "Moi be tong", "Rule": "FATIGUE_LM71_EN(max) - FATIGUE_LM71_EN(min)"},
        ]
    )

    tables = {
        "nodes": nodes,
        "elements": elements,
        "node_summary": node_summary,
        "element_summary": element_summary,
        "materials": materials,
        "time_dependent": time_dependent,
        "sections": sections,
        "taper_groups": taper_groups,
        "supports": supports,
        "support_summary": support_summary,
        "support_interpretation": support_interpretation,
        "support_activation": support_activation,
        "load_cases": static_cases,
        "load_summary": load_summary,
        "lanes": lanes,
        "vehicles": vehicles,
        "moving_cases": moving_cases,
        "tendon_property": tendon_property,
        "tendon_profiles": tendon_profiles,
        "tendon_points": tendon_points,
        "tendon_prestress": tendon_prestress,
        "construction_stages": stages,
        "load_combinations": combinations,
        "comparison": comparison,
        "checklist": checklist,
        "max_min_rules": combo_audit,
        "report_sources": pd.DataFrame(REPORT_SOURCES),
    }
    tables.update(result_sheets)
    write_appendix(tables)
    build_tendon_figure(tendon_points)

    doc = Document()
    setup_document(doc)
    add_cover(doc)
    doc.add_page_break()
    add_manual_toc(doc)
    doc.add_heading("Nguồn dữ liệu và chuẩn trình bày", level=1)
    doc.add_paragraph(
        "Bố cục được chỉnh theo mẫu RM bridge report: dữ liệu mô hình được trình bày trước, "
        "sau đó là khai báo tải trọng, stage, tổ hợp và kết quả kiểm toán. Các bảng dài được đẩy sang phụ lục Excel."
    )
    add_df_table(doc, pd.DataFrame(REPORT_SOURCES), ["Nguon", "Noi_dung_ap_dung", "URL"], max_rows=10, font_size=6)

    doc.add_page_break()
    doc.add_heading("1. Mô hình tính", level=1)
    doc.add_heading("1.1. Tổng quan mô hình", level=2)
    overview = pd.DataFrame(
        [
            {"Thông số": "Chiều dài dầm", "Giá trị": f"{config.get('girder_length_m', 32.6)} m"},
            {"Thông số": "Nhịp tính toán", "Giá trị": f"{config.get('calculation_span_m', 31.5)} m"},
            {"Thông số": "Số dầm trong mô hình", "Giá trị": int(nodes["Girder"].nunique()) if not nodes.empty else ""},
            {"Thông số": "Số node", "Giá trị": len(nodes)},
            {"Thông số": "Số phần tử beam", "Giá trị": len(elements)},
            {"Thông số": "Số support node", "Giá trị": len(supports)},
            {"Thông số": "Số stage thi công", "Giá trị": len(stages)},
            {"Thông số": "Số tổ hợp tải trọng", "Giá trị": len(combinations)},
            {"Thông số": "Đơn vị MCT", "Giá trị": "kN, m, C"},
        ]
    )
    add_df_table(doc, overview, max_rows=20, font_size=8)
    doc.add_paragraph("Mô hình dùng 5 dầm độc lập 32,6 m để đối chứng báo cáo BXD; chưa xét trụ, móng và liên kết ngang chi tiết.")

    doc.add_heading("1.2. Node - tọa độ", level=2)
    add_df_table(doc, node_summary.round(3), max_rows=10, font_size=8)
    add_df_table(doc, nodes[["Node", "Girder", "Local", "X_m", "Y_m", "Z_m"]], max_rows=12, font_size=7)
    doc.add_paragraph("Bảng node đầy đủ được lưu tại sheet nodes của phụ lục Excel.")

    doc.add_heading("1.3. Element - tham số phần tử", level=2)
    add_df_table(doc, element_summary, max_rows=30, font_size=8)
    add_df_table(doc, elements[["Elem", "Girder", "Local", "Node_I", "Node_J", "Material", "Section", "Length_m"]], max_rows=12, font_size=7)
    doc.add_paragraph("Bảng element đầy đủ gồm node I/J, vật liệu, mặt cắt và chiều dài được lưu tại sheet elements.")

    doc.add_heading("1.4. Liên kết và support", level=2)
    doc.add_paragraph(
        "Mục này được đặt ngay sau node/element tương tự mục Spring Declaration của mẫu RM. "
        "Quy ước constraint theo MIDAS: Dx, Dy, Dz, Rx, Ry, Rz; 1 = khóa, 0 = tự do."
    )
    add_df_table(doc, support_summary, max_rows=20, font_size=8)
    add_df_table(doc, support_interpretation, max_rows=5, font_size=7)
    add_df_table(doc, supports[["Node", "Girder", "Local", "X_m", "Constraint", "Dx", "Dy", "Dz", "Rx", "Ry", "Rz", "Group"]], max_rows=15, font_size=7)
    doc.add_paragraph("Stage kích hoạt support:")
    add_df_table(doc, support_activation, max_rows=5, font_size=7)

    doc.add_heading("1.5. Vật liệu và đặc trưng theo thời gian", level=2)
    add_df_table(doc, materials, max_rows=10, font_size=8)
    if not time_dependent.empty:
        doc.add_paragraph("Khai báo vật liệu theo thời gian:")
        add_df_table(doc, time_dependent, max_rows=10, font_size=7)

    doc.add_heading("1.6. Mặt cắt và taper group", level=2)
    add_df_table(doc, sections, max_rows=10, font_size=7)
    if not taper_groups.empty:
        doc.add_paragraph("Nhóm mặt cắt taper:")
        add_df_table(doc, taper_groups, max_rows=10, font_size=7)
    doc.add_paragraph("Quy ước so sánh ứng suất: Cb1/Cb2 là thớ trên, Cb3/Cb4 là thớ dưới theo bảng mục 5.1 của báo cáo BXD.")

    doc.add_heading("1.7. Cáp dự ứng lực", level=2)
    add_df_table(doc, tendon_property, max_rows=5, font_size=7)
    add_df_table(doc, tendon_summary, max_rows=25, font_size=7)
    add_df_table(doc, tendon_prestress.head(10), max_rows=10, font_size=7)
    if TENDON_FIG.exists():
        doc.add_picture(str(TENDON_FIG), width=Cm(16))
    doc.add_paragraph(
        "Logic đọc tendon hiện tại đang phục vụ riêng bài toán BXD: điểm refer xác định nhóm cáp, "
        "còn element gán cáp lấy theo file DXF để xử lý được trường hợp cáp ngắn hoặc thi công phân đoạn."
    )
    doc.add_paragraph("Tọa độ toàn bộ profile cáp DUL được lưu tại sheet tendon_points.")

    doc.add_heading("1.8. Tải trọng và load case", level=2)
    add_df_table(doc, load_summary, max_rows=25, font_size=7)
    if not vehicles.empty:
        doc.add_paragraph("Hoạt tải tàu dùng khai báo vehicle/moving load của MIDAS:")
        add_df_table(doc, vehicles, max_rows=10, font_size=6)
    if not moving_cases.empty:
        add_df_table(doc, moving_cases, max_rows=10, font_size=6)
    doc.add_paragraph("Các lane, vehicle, moving load case và static load case chi tiết có trong phụ lục Excel.")

    doc.add_heading("1.9. Stage thi công", level=2)
    add_df_table(doc, stages, max_rows=10, font_size=7)
    doc.add_paragraph("Các mốc 3 ngày, 36 ngày và 100 năm được dùng khi đối chiếu độ võng/độ vồng và ứng suất theo báo cáo BXD.")

    doc.add_heading("1.10. Tổ hợp tải trọng và quy tắc max/min", level=2)
    add_df_table(doc, combinations, max_rows=20, font_size=6)
    doc.add_paragraph("Quy tắc đọc max/min/all dùng khi trích kết quả:")
    add_df_table(doc, combo_audit, max_rows=10, font_size=8)

    doc.add_page_break()
    doc.add_heading("2. Kết quả tính toán", level=1)
    group_text = comparison["Group"].astype(str)
    add_comparison_section(doc, "2.1. Nội lực và phản lực gối", comparison, group_text.str.contains("Nội lực|Tổ hợp|Lực cắt", regex=True, na=False))
    add_comparison_section(doc, "2.2. Ứng suất", comparison, group_text.str.contains("Ứng suất", regex=False, na=False))
    add_comparison_section(doc, "2.3. Độ võng, độ vồng và góc xoay đầu dầm", comparison, group_text.str.contains("Độ võng/vồng|Góc xoay", regex=True, na=False))
    add_comparison_section(doc, "2.4. Mỏi", comparison, group_text.str.contains("Mỏi", regex=False, na=False))
    doc.add_heading("2.5. Checklist và các mục cần tiếp tục", level=2)
    add_df_table(doc, checklist, max_rows=20, font_size=7)

    doc.add_page_break()
    doc.add_heading("3. Phụ lục kết quả", level=1)
    add_bullet(doc, f"Phụ lục Excel: {APPENDIX_XLSX}")
    for sheet in tables:
        add_bullet(doc, sheet)

    doc.save(REPORT_DOCX)
    print(REPORT_DOCX)
    print(APPENDIX_XLSX)


if __name__ == "__main__":
    main()
