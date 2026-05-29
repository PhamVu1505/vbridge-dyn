# VBridge-Dyn — Context cho Claude / Agents

> File này được Claude load tự động và mọi agent/dev khác cũng phải đọc qua
> `AGENTS.md`. Đây là **nguồn duy nhất** (single source of truth) về kiến trúc
> + nguyên tắc. Khi quyết định kiến trúc thay đổi, cập nhật file này **trong
> cùng commit** với entry mới ở `TASK_LOG.md`.
>
> Plan đầy đủ (bản trong repo, self-contained): [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md).

---

## 1. Vai trò phần mềm (KHÔNG THAY ĐỔI)

VBridge-Dyn là **lớp tự động hóa (pre + post processor)** cho phân tích động
lực học cầu đường sắt tốc độ cao, dùng Midas Civil (MVP) và RM Bridge (Phase 2)
làm engine tính toán.

### 3 nguyên tắc MVP (không vi phạm)

1. **MVP = 5 module nền cho Midas**:
   - `core/schemas/*`
   - `importers/excel/*`
   - `integrations/midas/mct/*` (generator)
   - `integrations/midas/readers/*` (CSV ingest)
   - `report/*` + `postprocessor/*`
   - Mọi tính năng ngoài 5 module này đều **không** thuộc MVP.

2. **RM Bridge ở MVP = skeleton + schema-ready, triển khai Phase 2.**
   `core/schemas` đủ trường để Phase 2 không refactor. **Không** writer/reader RM thật.

3. **Không tự viết solver.** Engine = Midas Civil 2022 (MVP), RM Bridge (Phase 2).
   **Không có** OpenSeesPy/Cast3M/Code_Aster/hand-rolled FEM trong bất kỳ phase nào.

### MVP workflow (4 dòng)

1. Sinh `.mct` cho **Midas Civil 2022** (default `midas_version: "2022"`).
2. User import/run/export CSV **thủ công** (qua `export_instructions.md`).
3. App ingest CSV → SQLite + Parquet → tìm case bất lợi → vẽ envelope/TH.
4. Xuất PDF tiếng Việt 13 mục theo TCVN 13594.

---

## 2. Stack công nghệ chốt

| Thành phần | Lựa chọn | Lý do |
|---|---|---|
| Ngôn ngữ | Python 3.11+, `uv` + `pyproject.toml` | Stack chuẩn |
| Data model | pydantic v2 | Validate ràng buộc engineering |
| Excel/CSV | openpyxl + pandas | Format kỹ sư cầu quen |
| Storage | SQLite (envelope/meta) + Parquet (TH) | DuckDB query là v1.1+ |
| UI Desktop | PySide6 (LGPL) + pyqtgraph + pyvista | An toàn thương mại |
| CLI | Typer + rich | UTF-8 đẹp |
| Plot | matplotlib (backend pdf/svg) — vector | Báo cáo PDF chuẩn vector |
| PDF compose | reportlab + Jinja2 (v1.0); WeasyPrint cân nhắc v1.1 | Unicode tiếng Việt |
| Test/Lint | pytest + hypothesis + ruff + mypy + pre-commit | Chuẩn |
| Đóng gói | PyInstaller + Inno Setup | Windows MSI |

---

## 3. Tiêu chuẩn áp dụng

### Việt Nam — CHÍNH (`standards_profile: vietnam_tcvn13594`)

- TCVN 13594-1..10:2022-2023 (HSR 1435mm, 350 km/h). Mặc định
  `part_3: "2022"`, `part_4: "2022"`. Override qua `project.yaml`.
- TCVN 2737:2023, TCVN 5574:2022, TCVN 9386:2012, TCVN 10304:2015.

### Châu Âu — THAM CHIẾU

- EN 1990:2002+A1:2005, EN 1991-1-1..1-7, **EN 1991-2:2003**, EN 1992-1-1,
  **EN 1992-2**, EN 1993-1-1, EN 1994-1-1, **EN 1994-2**.
- ERRI D214:1999 (time-step formula).

### Mapping TCVN ↔ EN

Xem section "Mapping Standard → module" trong [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md).

---

## 4. Kiến trúc package (rút gọn)

```
src/vbridge_dyn/
├── core/                          # mô hình trung lập (KHÔNG phụ thuộc tiêu chuẩn/solver)
│   ├── schemas/                   # pydantic
│   ├── validation/                # geometry/reference/unit checks
│   ├── mode_classifier.py
│   └── grid/                      # velocity + time grid
├── standards/                     # namespace theo quốc gia
│   ├── vietnam/tcvn13594/         # FLAT structure — dynamic_required, train_loads,
│   │                              # hslm_rules, speed_range, damping, acceleration,
│   │                              # resonance, load_actions, load_distribution,
│   │                              # combinations, version_registry
│   ├── eurocode/                  # cross-check
│   └── international/erri_d214/
├── importers/excel/               # workbook_reader + train_catalog_reader + templates/
├── integrations/
│   ├── midas/
│   │   ├── mct/                   # writer + blocks/ (capability-based: geometry,
│   │   │                          # properties, boundary, mass, groups, moving_load,
│   │   │                          # time_history, analysis_control, result_request)
│   │   │                          # + manifest_writer.py + export_guide.py
│   │   ├── readers/               # modal_csv + time_history_csv + column_mapping.yaml
│   │   └── runner.py              # OPTIONAL — NGOÀI MVP
│   └── rm_bridge/                 # Phase 2 skeleton
├── postprocessor/                 # envelope + checks (dispatch theo standards_profile)
├── storage/                       # sqlite_store + parquet_store
├── report/                        # ReportLab + Jinja2 + matplotlib factories
├── services/                      # project, generate, ingest, analyze, report
├── ui/                            # PySide6 main_window + panels + dialogs + widgets
├── cli/                           # Typer commands (init, validate, generate, ingest,
│                                  # envelope, report, benchmark)
└── tests/                         # unit + integration + benchmarks
```

---

## 5. Quyết định kiến trúc đã chốt (từ AskUserQuestion + reviews rev1..rev9)

- **Backend**: Pre+Post processor cho Midas Civil 2022 + RM Bridge (Phase 2).
  KHÔNG solver nội bộ.
- **Result IO**: User export CSV thủ công từ Midas, app ingest qua
  `generation_manifest.json` mapping.
- **Project workspace**: folder-based với `project.yaml` + Excel workbook +
  `generated/` + `solver_outputs/` + `storage/` + `figures/` + `reports/`.
- **Storage**: SQLite (envelope/meta) + Parquet (TH). DuckDB query là v1.1+.
- **Tiêu chuẩn**: vietnam_tcvn13594 (chính), eurocode (cross-check). Năm xuất
  bản KHÔNG hard-code — đọc từ `project.yaml > tcvn13594_versions`.
- **Moving load strategy**: `time_history_function` (default cho Midas Civil
  2022). `rail_track_analysis` experimental.
- **Case split**: `grouped_by_train` (default) — gộp 50 vận tốc cùng train vào
  1 `.mct`. `one_file_per_case` chỉ debug.
- **MCT version chuẩn**: 2022. `column_mapping.yaml` cho phép override.
- **Eurocode catalog**: ship rỗng vì bản quyền; user import từ Excel template.
- **Civil NX**: NGOÀI MVP, ra v1.2+ "future MIDAS API/NX integration".
- **UI**: Desktop PySide6 + CLI Typer song hành.
- **Ngôn ngữ**: tiếng Việt cho UI, comment, error message, PDF report.
- **License**: Apache-2.0 (stack BSD/MIT/LGPL/Apache).

---

## 6. Lộ trình MVP snapshot

| Version | Tuần | Mục tiêu |
|---|---|---|
| v0.1 | 1-3 | Repo + CI + schemas + Excel reader + reverse-engineer MCT 2022 |
| v0.2 | 4-6 | MCT skeleton (geometry/properties/boundary/mass/groups/analysis_control) + standards TCVN |
| v0.3 | 7-10 | MCT moving_load + readers + storage + postprocessor + CLI |
| v0.4 | 11-14 | PySide6 UI + ReportLab PDF 13 mục + checks |
| v0.5 | 15-17 | RM Bridge skeleton |
| v0.6 | 18-21 | RM Bridge full |
| v0.7 | 22-25 | VBI Phase 3 |
| v1.0 | 26-28 | Installer + manual + V01-V09 regression |
| v1.1+ | future | DuckDB, WeasyPrint, MP4 animation, multi-project compare |
| v1.2+ | future | MIDAS API/Civil NX, cable-stayed, gió ngang, optimization |

---

## 7. Benchmarks

Phân thành **2 nhóm rõ ràng** theo quyết định rev7:

### 7.1. Hard benchmarks (có analytical/reference rõ — tolerance cứng, CI gate)

| ID | Case | Reference | Tolerance |
|---|---|---|---|
| V01 | Simple beam static | `δ = PL³/48EI` analytical | ±0.5% |
| V02 | Single moving load | Frýba 1972 analytical | ±2% |
| V06 | TCVN damping vs EN damping | parity (cùng công thức Bảng 18 ≡ Table 6.6) | exact |
| V07 | TCVN ψ vs EN ψ | parity (Bảng A.1 vs EN 1990 A2.4) | exact |
| V08 | MCT vs TCL parity (Phase 2) | cùng project, 2 targets | ±2% |
| V10 | VBI HSLM-A1 @ 220 km/h (Phase 3) | Yang/Zhang VBI paper | ±10% |

### 7.2. Reference comparisons (soft — kiểm tra xu hướng + order-of-magnitude)

Chỉ chuyển sang tolerance cứng khi có file model gốc của reference. Đến lúc đó
phải có file model trong repo (hoặc owner cung cấp local), không chỉ PDF.

| ID | Case | Reference | Soft acceptance |
|---|---|---|---|
| V03 | KD-Railway Chapter6_Example | KD-Railway output CSV (chưa có file model) | Xu hướng peak velocity + critical speed approximate + report layout đúng |
| V04 | HS2 case eigenvalues | docs HS2 PDF p.30 (chỉ PDF, không có file model) | f_1 cùng order (~6 Hz), N modes đầu cùng chiều biến |
| V05 | HS2 envelope HSLM-A1..A10 | docs HS2 PDF p.36 (chỉ PDF) | Peak velocity ≈ ±20 km/h; accel trend qualitative giống |
| **V09** | **HSR HCM-CG typical span** | `refer/202512-23_HSR-CG Ban Tinh Tong The H7H15m.pdf` (Midas Civil 2025, HSLM-A, ξ=1%, dt=0.001s, Vtk=350, Vmax=420, f_bending≈5.9312 Hz, f_torsion≈16.35 Hz, Vcr≈384.34 km/h) | f_bending cùng order (~6 Hz), f_torsion cùng order (~16 Hz), Vcr ±20 km/h, report layout đầy đủ 13 mục |

CI: V01-V02 + V06-V07 chạy mỗi PR (<5 min). V03-V05, V09 chạy weekly hoặc
on-demand. V08, V10 chạy khi tới Phase 2/3.

---

## 8. Tham chiếu nguồn

| Nguồn | Đường dẫn / URL | Vai trò |
|---|---|---|
| Bản tính HSR HCM-CG | `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\refer\202512-23_HSR-CG Ban Tinh Tong The H7H15m.pdf` | Benchmark V09 + tham chiếu TCVN |
| MIDAS UK Tutorial HS2 | `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\docs\[Final]Dynamic Analysis for High Speed Two (HS2).pdf` | Benchmark V04-V05 + Eurocode mapping |
| KD-Railway snapshots | `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\refer\KD_Railway_software\Snapshot\*.JPG` | UX inspiration |
| KD-Railway repo | https://github.com/lekhuong/KD-Railway | File format tham khảo |
| Plan chi tiết (bản trong repo) | [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md) | Rev9, đã được duyệt |

---

## 9. Conventions

- Tiếng Việt cho mọi text user-facing (UI, comment in code, error message, PDF
  report). Tên biến/function/class theo tiếng Anh.
- **Không hard-code năm TCVN** — đọc từ `project.yaml > tcvn13594_versions`.
- `standards_profile` dispatch trong `postprocessor/checks.py`. Cùng API
  signature giữa `vietnam` và `eurocode` namespace.
- Capability-based block naming trong MCT generator (geometry/properties/...) —
  **không** đặt tên theo MCT keyword.
- pydantic v2 (`model_validate_json`, `model_dump`), ruff + mypy strict,
  pre-commit.
- Test Hard benchmarks (V01-V02 analytical + V06-V07 parity) chạy mỗi PR (<5 min); Reference comparisons (V03-V05, V09) weekly/on-demand; V08 (Phase 2 RM Bridge) và V10 (Phase 3 VBI) chỉ chạy khi tới phase tương ứng.

---

## 10. Khi bắt đầu phiên mới (cho Claude)

1. Đọc `PROJECT_STATUS.md` để biết đang ở version nào, đang làm gì, blocker
   nào.
2. Đọc `TASK_LOG.md` mục cuối cùng để xem context gần nhất.
3. Trước khi sửa code: check `standards_profile`, không vi phạm 3 nguyên tắc
   MVP (§1).
4. Khi đóng quyết định kiến trúc mới: cập nhật cả `CLAUDE.md` (mục liên quan)
   và `TASK_LOG.md` (append entry mới) trong cùng commit.

---

## 11. Handoff (chuyển dự án cho người/AI khác)

Nếu chuyển dự án:

1. Cập nhật `PROJECT_STATUS.md` với hiện trạng (version, active focus,
   blockers).
2. Append vào `TASK_LOG.md` đoạn `## Handoff <yyyy-mm-dd>` liệt kê:
   - Todo còn lại
   - Blockers đã biết
   - Files đã sửa gần đây
   - Quyết định kiến trúc mới (nếu có) — cũng update `CLAUDE.md`
3. Commit với message `handoff: <ngày> — <summary 1 dòng>`.

---

## 12. Liên hệ

- Author: Vũ (`quangvu0515@gmail.com`)
- Repo: TBD (chưa khởi tạo git)
- Issues: TBD
