"""Sinh project.yaml template (sample minimal)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from textwrap import dedent


def write_project_template(
    path: Path,
    *,
    name: str,
    author: str = "",
    design_speed_kmh: float = 350.0,
    track_type: str = "ballasted",
) -> None:
    """Sinh `project.yaml` mẫu với comment dẫn dắt người dùng (tiếng Việt)."""
    today = date.today().isoformat()
    content = dedent(
        f"""\
        # ----------------------------------------------------------
        # VBridge-Dyn project.yaml — template tự sinh
        # Tài liệu: AGENTS.md, CLAUDE.md, docs/PLAN_REV9.md
        # ----------------------------------------------------------

        meta:
          name: "{name}"
          author: "{author}"
          description: ""
          created_at: {today}
          schema_version: "1.0"
          locale: vi-VN

        standards_profile: vietnam_tcvn13594

        tcvn13594_versions:
          part_3: "2022"
          part_4: "2022"   # override "2023" nếu dự án dùng bản mới
          part_5: "2023"
          part_10: "2023"

        design:
          design_speed_kmh: {design_speed_kmh:g}
          max_analysis_speed_factor: 1.2     # V_max = factor × V_tk
          track_type: {track_type}
          track_gauge_mm: 1435

        dynamic:
          check_required_method: tcvn13594_dynamic_required
          damping_method: tcvn13594_3_table_18
          resonance_check: true
          time_step_method: erri_d214

        velocity_range:
          v_min_kmh: 140
          v_max_kmh: {design_speed_kmh * 1.2:g}
          v_line_design_kmh: {design_speed_kmh:g}
          step_kmh: 5
          refine_near_resonance: true

        analysis:
          n_modes: 30
          fmax_target_hz: null      # null = auto: max(30 Hz, 1.5·n0, n3)
          damping:
            standard: tcvn13594_3_table_18
            bridge_type: prestressed_concrete
          time_step:
            method: erri_d214
          integration: modal_superposition

        # ----------------------------------------------------------
        # bridge: nhập từ bridge.xlsx — cần điền sheets
        # Nodes / Elements / Materials / Sections / Supports / Tracks / ...
        # ----------------------------------------------------------
        bridge:
          # Hiện tại để rỗng — workbook_reader sẽ load từ bridge.xlsx
          # Khi bridge.xlsx có dữ liệu, validate sẽ tự merge vào.
          nodes: []
          elements: []
          materials: []
          sections: []
          supports: []

        # Đường ray — gắn vào element nào của model
        tracks: []

        # Đoàn tàu — import từ trains/*.xlsx (TCVN catalog không ship sẵn)
        trains: []

        # Vị trí xuất kết quả (giữa nhịp, đầu cọc, ...)
        result_stations:
          - id: S1
            name: "Giữa nhịp 1"
            target: track
            track_id: T1
            track_x: 17.5

        targets:
          midas_civil:
            enabled: true
            midas_version: "2022"
            units: {{ force: kN, length: m, mass: ton, time: s }}
            export_mode: mct
            case_split: grouped_by_train
            output_dir: generated/midas
            moving_load_strategy: time_history_function
          rm_bridge:
            enabled: false     # bật khi vào Phase 2
            rm_version: "12.x"
            export_mode: tcl
            output_dir: generated/rm_bridge

        checks:
          standards:
            - tcvn13594_4_dynamic_check
            - tcvn13594_4_acceleration_limit
            - tcvn13594_4_deflection_limit
            - tcvn13594_4_daf
          cross_check:
            - en1990_a2_4_4_2

        report:
          template: full_report
          language: vi-VN
          engine: reportlab
          output: "reports/{{date}}_full_report.pdf"
        """,
    )
    path.write_text(content, encoding="utf-8")
