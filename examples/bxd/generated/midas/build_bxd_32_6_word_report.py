from __future__ import annotations

from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

BASE = Path(__file__).resolve().parent
COMPARISON_XLSX = BASE / "comparison_bxd_32_6.xlsx"
OUTPUT_DOCX = BASE / "so_sanh_midas_bao_cao_bxd_32_6_moc_3d_36d_100y.docx"


def fmt(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:,.3f}"
    return str(value)


def set_cell_text(cell, text: str, *, bold: bool = False, size: int = 7) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(document: Document, headers: list[str], rows: list[list[str]], font_size: int = 7) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[index], header, bold=True, size=font_size)
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value, size=font_size)


def add_bullet(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(style="List Bullet")
    paragraph.add_run(text)


def main() -> None:
    comparison = pd.read_excel(COMPARISON_XLSX, sheet_name="comparison")
    checklist = pd.read_excel(COMPARISON_XLSX, sheet_name="checklist")

    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    section.top_margin = Cm(1.2)
    section.bottom_margin = Cm(1.2)
    section.left_margin = Cm(1.0)
    section.right_margin = Cm(1.0)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(10)

    title = doc.add_heading("So sánh kết quả MIDAS với báo cáo BXD - dầm 32,6 m", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Workbook nguồn: {COMPARISON_XLSX}")
    doc.add_paragraph(
        "Phạm vi: đối chiếu các nội dung của báo cáo thiết kế dầm HSR nhóm trên 30 m cho loại dầm 32,6 m. "
        "Các hàng chưa có dữ liệu MIDAS trực tiếp được giữ trạng thái chờ export hoặc cần bổ sung công thức."
    )

    doc.add_heading("1. Bảng so sánh tổng hợp", level=1)
    rows = []
    for _, row in comparison.iterrows():
        rows.append(
            [
                fmt(row["Group"]),
                fmt(row["Quantity"]),
                fmt(row["Status"]),
                fmt(row["Unit"]),
                fmt(row["Report_source"]),
                fmt(row["Report_32_6"]),
                fmt(row["MIDAS_Excel"]),
                fmt(row["Difference_pct"]),
                fmt(row["MIDAS_source"]),
                fmt(row["Comment"]),
            ]
        )
    add_table(
        doc,
        ["Nhóm", "Đại lượng", "Trạng thái", "Đơn vị", "Nguồn báo cáo", "Báo cáo", "MIDAS", "Sai khác (%)", "Nguồn MIDAS", "Ghi chú"],
        rows,
        font_size=6,
    )

    doc.add_heading("2. Trạng thái đối chứng theo báo cáo", level=1)
    add_table(
        doc,
        ["Trạng thái", "Hạng mục", "Cần kiểm tra", "Nguồn"],
        checklist[["Status", "Item", "What_to_check", "Source"]].astype(str).values.tolist(),
        font_size=8,
    )

    doc.add_heading("3. Ghi chú tái tạo", level=1)
    add_bullet(doc, "File Word này được tạo tự động từ comparison_bxd_32_6.xlsx bằng build_bxd_32_6_word_report.py.")
    add_bullet(doc, "Sau khi chỉnh file MCT và export lại kết quả MIDAS, chạy lại rebuild_comparison_bxd_32_6.py rồi chạy lại script Word này.")
    add_bullet(doc, "Mục 5.1 dùng quy ước top = Cb1/Cb2, bot = Cb3/Cb4; khai thác lấy SLS_CHAR_LM71(max) cho sigma_bot,max tại node giữa nhịp x00016.")
    add_bullet(doc, "Độ võng LM71 lấy abs(DZ_min) từ LM71_2T(min); góc xoay/lực cắt lấy trị tuyệt đối envelope khi báo cáo nêu giá trị lớn nhất.")
    add_bullet(doc, "Mỏi bê tông lấy biên độ FATIGUE_LM71_EN(max) - FATIGUE_LM71_EN(min), không lấy riêng một chiều max hoặc min.")

    try:
        doc.save(OUTPUT_DOCX)
        print(OUTPUT_DOCX)
    except PermissionError:
        fallback = OUTPUT_DOCX.with_name("so_sanh_midas_bao_cao_bxd_32_6_latest.docx")
        doc.save(fallback)
        print(fallback)


if __name__ == "__main__":
    main()
