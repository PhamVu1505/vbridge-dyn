# Project Status — VBridge-Dyn

> **Last updated**: 2026-09-12
> Mỗi khi đóng/mở task lớn, đổi version, hoặc gặp blocker — update file này.

**Việc gần nhất (2026-09-12)**: **SB29 — mô hình đối chứng** (ngoài repo,
`1_du_an/SB29_HNQN/`). Mô hình tĩnh tổng thể **đã chạy
sạch, 0 warning** trên 6 loại phân tích; pipeline tự động hoàn toàn qua MAPI
(`build_sb29_global.py` → `push_to_midas.py --run` → `report_results.py`).
Đã vá 6 lỗi im lặng — nặng nhất là **gối P1/P4 bị thả phương đứng** khiến hai
nhịp biên chạy như công xôn 40,85 m (mô men âm tại P2 dưới DC từ −235 602 về
đúng −124 117 kN·m). Bổ sung LM71 (trước chưa từng được đẩy vào midas), gradient
nhiệt, lún lệch, phổ phản ứng và 17 tổ hợp. **Động đất chi phối phần dưới**:
mô men đáy bệ P2 tới 191 803 kN·m. **Blocker**: chưa chốt hệ số ứng xử `q`
(1,5 hay 3,5·λ — lệch >2 lần) và chưa có bố trí cốt thép để kiểm toán GSD.
Next: rà soát thành phần lực → rà soát tổ hợp → kiểm toán GSD → động HSLM + RSI
→ báo cáo. Chi tiết: `1_du_an/SB29_HNQN/docs/02_TIEN_DO_VA_VIEC_TIEP_THEO.md`.

**Việc trước đó (2026-07-26)**: **Chốt bản sửa phụ lục lần 3** theo markup của user trên
`05_BAO_CAO_TGD/Phu_luc_tinh_toan_lan_3_chi_tiet.docx`: accept 14 đoạn gạch bỏ + 2 chỗ
highlight (chữ user chèn), **xoá hết viện dẫn "Mục X, tài liệu 8-4"** (trích TCVN 13594
trực tiếp), bỏ giọng tự quảng bá, **căn chỉnh lại 5 bảng** (khổ cố định 9.355 twips, lặp
dòng tiêu đề, cantSplit, căn giữa theo chiều cao) và **đặt tên Bảng 1-5**. File 8 trang,
đã xuất PDF kiểm tra bằng Word. Backup: `*_BACKUP_truoc_sua.docx`. Next: user review →
áp cùng 3 quy tắc biên tập cho `Bao_cao_lan_3.docx`; DAF (DY-06) vẫn chờ bảng My tĩnh
LM71×Φ; RS-09 fastener chờ catalog. Xem `vbridge-dyn/CLAUDE.md` §0 Current Sprint.

**Việc trước đó (2026-07-25)**: Hoàn thiện **hồ sơ báo cáo TGD** (ngoài repo, ở
`1_du_an/BXD/TGD/05_BAO_CAO_TGD/`): (1) **Báo cáo chính lần 3**
`Bao_cao_lan_3.docx` (bám style bản chính thức lần 1, NĐ30, đã bỏ nội dung BXD 32,6m); (2)
**Phụ lục tính toán** `Phu_luc_tinh_toan_lan_3_chi_tiet.docx` (9 mục, 5 bảng, 10 hình + đồ thị).
**RSI đã giải quyết bằng MIDAS RSI Wizard** (ballastless): ứng suất ray 72,7<92 → đạt. Ma trận
tiêu chí: 31 đã có kết quả/5 một phần/2 N/A/7 chờ đầu vào. Next: user đóng file summary cũ để
đổi tên phụ lục; DAF cần xuất LM71×Φ riêng; RS-09 fastener chờ catalog. Chi tiết: TASK_LOG mục 2026-07-25.

---

## Current version

**v0.2 — MCT generator (in-progress)** — v0.1 đã đạt acceptance; đã có MCT writer/generator + CLI `generate` (base model). Đang mở rộng sang loads + eigen + dynamic.

- [x] Plan rev9 đã duyệt — [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md)
- [x] 4 file tracking + `AGENTS.md`
- [x] `pyproject.toml` (pip + uv compat), `src/vbridge_dyn/` skeleton
- [x] Pydantic schemas: units, geometry, properties, boundary, mass, groups, track, train, analysis, result_station, bridge, project
- [x] `io/project_io.py` + `io/project_templates.py` (project.yaml generator)
- [x] `importers/excel/`: template writer + workbook reader (11 sheets)
- [x] CLI Typer: `vbdyn --version | info | init | validate`
- [x] Tests: 23/23 PASS (schemas + CLI roundtrip + Excel roundtrip)
- [x] Ruff + ruff format clean, mypy strict cấu hình sẵn
- [x] CI workflow `.github/workflows/ci.yml` (ubuntu + windows × py3.11/3.12)
- [x] Apache-2.0 LICENSE, `.gitignore` Python + project-specific
- [x] `examples/hcm_cg/` initialized (HSR HCM-Cần Giờ benchmark V09 placeholder)
- [x] Reverse-engineer MCT mẫu `16 Eurocode Rail loads Final.mct` (36 sections, 2534 dòng) → đã hiểu cú pháp `*NODE` `*ELEMENT` `*MATERIAL` `*SECTION` `*CONSTRAINT` `*MVLDCODE` `*VEHICLE` `*MVLDCASE(EURO)` `*MV-DYFG` `*MOVE-CTRL`
- [x] Tham khảo `4_cong_cu/rm2midas` (private repo): pipeline pattern, sectionproperties lib, ECC→Rigid Link, STIFF3 Euclidean
- [x] **`generation_manifest.json` schema khóa** (GenerationManifest + CaseEntry + StationRef, pydantic v2 trong `core/schemas/manifest.py`) + 8 tests roundtrip/validation
- [x] mypy strict clean (28 source files), ruff check + format clean, 33/33 tests PASS

**v0.2 (in-progress)** — chi tiết quyết định ở `TASK_LOG.md` mục 2026-06-01:

- [x] `integrations/midas/mct/`: `writer.py` + `generator.py` + `sections.py` (polygon OPOLY/IPOLY)
- [x] CLI `vbdyn generate --target midas` → `model_base.mct` + `generation_manifest.json` (1 case modal)
- [x] Verify pipeline mặt cắt khớp bản đã validate (Converte `src/core/geometry.py`, Euclidean STIFF3 100% match 38 SPC)
- [x] Research sub girder cho tải tàu + xác nhận block keyword time-history (→ `1_du_an/hcm_cg/`)
- [x] **DXF section importer** (`importers/dxf/`, cột `dxf_file`, auto-chain) + vá writer fallback OPOLY → mọi GEN section hiển thị trong Midas (verify trên MG_01.dxf)
- [x] **ARC/CIRCLE chia 10°** trong DXF reader + **`detect_circle`→`DBUSER SR/P`** (cọc D1500) trong writer
- [x] Mở rộng writer: `*STLDCASE`/`*SELFWEIGHT`/`*BEAMLOAD` (DW từ `distributed_masses` theo group)
- [ ] `*EIGEN-CTRL` (modal) — chờ field layout từ file mẫu Midas 2022 (B1)
- [x] Đổi STIFF2 sang mesh vertices cho khớp 100% reference; hỗ trợ LWPOLYLINE bulge cong
- [x] Fix lỗi Midas Material Name > 16 ký tự: writer dùng `material.id` ngắn (`C50`, `C40`, `C30`, ...)
- [~] Dựng base model HCM-CG 5 nhịp từ `1_du_an/hcm_cg/input_parameters.yaml`: dầm chính + bệ + cọc 8 m + thân trụ taper + boundary chân cọc đã sinh MCT; còn thiếu dữ liệu đoàn tàu / dynamic case.
- [ ] Dynamic blocks `*TFUNCTION`/`*THLDCASE`/`*DYN-NLOAD` — chờ field layout từ file mẫu (B1)
- [x] Test: **56/56 PASS** (33 → +MCT gen/polygon/excel → +DXF reader & fallback OPOLY → +ARC 10° & circle DBUSER → +STIFF2 mesh vertices/LWPOLYLINE bulge → +static load blocks → +material short name + tapered section → +DXF layer/axis order → +solid rectangle DBUSER SB → +bearing links/TS-GROUP → +preserve DXF polygon points)

---

## Active focus (v0.0 → v0.1)

### Việc tiếp theo (v0.1 → v0.2)

1. [x] `pyproject.toml` + skeleton + CI workflow
2. [x] Pydantic schemas + Excel template + reader
3. [x] CLI `init` + `validate` (load Excel auto-merge)
4. [x] Reverse-engineer MCT mẫu `16 Eurocode Rail loads Final.mct` (block structure đã document)
5. [ ] **Push code lên GitHub** — chờ user chạy `!gh repo create ...` (auto mode chặn)
6. [x] **`generation_manifest.json` schema** đã khóa; writer sinh manifest base (1 case modal). `export_instructions.md` generator vẫn chưa.
7. [ ] **`export_instructions.md` template generator** — hướng dẫn user export CSV
8. [~] v0.2 MCT writer: geometry + properties (polygon) + boundary + groups + static dead loads **xong**; nodal mass + `*EIGEN-CTRL` **chưa**
9. [ ] v0.2: `standards/vietnam/tcvn13594/{damping, dynamic_required, speed_range, resonance, hslm_rules}.py`
10. [~] v0.2: `model_base.mct` sinh được (geometry/section/boundary); cần thêm `*EIGEN-CTRL` để thành `case_modal.mct` chạy modal trong Midas
11. [~] Dựng model 5 nhịp HCM-CG thật từ `1_du_an/hcm_cg/input_parameters.yaml` (Main + foundation/pier đã có; Sub girder/dynamic train case còn chờ B1/B2)

### Acceptance v0.1

- `vbdyn init my_project` tạo được folder với `project.yaml` + `bridge.xlsx` template
- `vbdyn validate my_project` load Excel ra `Project` model không lỗi
- Sample MCT minh họa parse được bằng tay đối chiếu với schema
- **`generation_manifest.json` schema được khóa** — sample output cho 1 train + 1 velocity ra đúng schema (dù chưa generate MCT thật)

---

## Milestones (next 3)

| Milestone | Target | Acceptance |
|---|---|---|
| **v0.1 complete** | Tuần 3 (≈ 2026-06-19) | `vbdyn init` + `vbdyn validate` chạy + schemas + Excel reader |
| **v0.2 complete** | Tuần 6 (≈ 2026-07-10) | Sinh MCT modal cho HSR HCM-CG, Midas chạy không lỗi syntax; `generation_manifest.json` cho case modal đầy đủ; `export_instructions.md` cover step Run + Export ở Midas |
| **v0.3 complete** | Tuần 10 (≈ 2026-08-07) | Xu hướng envelope khớp HSR HCM-CG/HS2; CLI generate/ingest/envelope hoạt động |

---

## Blockers / Open questions

| # | Mô tả | Blocking version | Owner | Status |
|---|---|---|---|---|
| B1 | Cần file MCT sample từ **Midas Civil 2022** có khối **time-history** (Train Load Generator) để lấy field layout của `*EIGEN-CTRL`/`*TFUNCTION`/`*THLDCASE`/`*DYN-NLOAD`. Tên block đã xác nhận qua MIDAS manual; còn thiếu thứ tự field. | v0.2 | Vũ (cung cấp) | OPEN — export 1 file modal + 1 case HSLM time-history |
| B2 | Cần catalog HSLM/LM71 Excel cho TCVN 13594-3 Bảng 15 | v0.2 | Vũ (cung cấp dữ liệu Bảng) | OPEN — sẽ nhập tay từ TCVN |
| B3 | Cần xác nhận format CSV export chuẩn của Midas Civil 2022 (cột nào, encoding nào) | v0.3 | Vũ (export sample) | OPEN |
| B4 | Cần sample TCL của RM Bridge với module Rolling Stock | v0.5 | Vũ (cung cấp) | OPEN — Phase 2, chưa gấp |

---

## Recent changes

- **2026-07-24**: **Quét động HSLM-A1…A10 hoàn tất và cập nhật hồ sơ tiêu chí TGD.**
  User đã chạy MIDAS Civil 2022 toàn bộ 320 case (144–420 km/h, ζ=1,0%, chạy gộp
  theo đoàn tàu, MCT `...V144-420_GROUPED`); do MIDAS hạn chế chiều dài đường dẫn,
  nguồn chạy đặt tại `D:\00_MCT_GOP_NHIEU_VAN_TOC`. Đọc 76/76 sheet, `complete_exports`
  và `out_ok` đều True. **Trường hợp chi phối: HSLM-A7** — |DZ|=4,268 mm (@415),
  |az|=3,374 m/s² (@420), |My|=12.690 kN·m (@415), f1=4,790193 Hz. Đã cập nhật ma trận tiêu chí
  `1_du_an/BXD/slide/.../00_QUAN_LY_HO_SO/SO_THEO_DOI_TIEU_CHI_VA_CASE_MIDAS.xlsx`:
  Đã có kết quả 12→19, Một phần 10→7, MCT chờ chạy 4→0 (CS-02/03/04/07 + DY-03/04/05
  → ĐÃ CÓ KẾT QUẢ); So_case 320 dòng → ĐÃ CHẠY-ĐÃ XUẤT; Ket_qua_da_co thêm block
  envelope A1–A10; README_TONG_THE cập nhật. Chưa động vào báo cáo TGD (làm một lượt sau).
  Còn lại theo tiêu chí: DAF động/tĩnh (DY-06), mode cutoff (CS-10), L/600 & tiện nghi
  (AT-01/TN), mỏi cáp-cốt đai (ST-09/DY-07), RSI không hội tụ (RS-01…09), đoàn tàu thực (CS-05).
- **2026-07-24 (2)**: **Chốt loại ray = ballastless + SW/0-SW/2 không yêu cầu** (user xác nhận).
  Hệ quả: (1) giới hạn gia tốc = **γdf 5,0 m/s²** (không phải 3,5) ⇒ |az|=3,374 → **dự trữ ~32,5%**;
  đã sửa DY-03 + KIEM_TRA_TONG_THE.md + README + Ket_qua_da_co. (2) **CS-08 biến thể mass balát
  KHÔNG áp dụng** cho ballastless (mass danh nghĩa đủ) → CS-08 = ĐÃ CÓ KẾT QUẢ có lập luận.
  (3) **ST-03 (SW/0) + ST-04 (SW/2) = KHÔNG ÁP DỤNG** (BXD giản đơn; tuyến HSR khách) — thêm
  cột đếm "Không áp dụng" vào Tong_quan. Tổng quan mới: Đã có 20 / Một phần 6 / Chờ chạy 0 /
  Chưa đủ 8 / Không áp dụng 2 / Không hội tụ 9 = 45. Không sinh MCT mới.
- **2026-07-23**: File gộp lớn một đoàn tàu không mở được trong MIDAS Civil
  2022 (A1 có 10 case/1.550 time functions, khoảng 5,2 MB). Đã thay bằng 81
  MCT chunked: pilot A1 330+340 có 2 case/310 functions; các file còn lại tối
  đa 4 case/620 functions và 2,12 MB. Bộ gộp lớn được đánh dấu không sử dụng.
- **2026-07-23**: Kiểm tra kết quả thiết kế HSLM-A1 đến 325 km/h bằng bộ đọc
  toàn bộ sheet: 23 case hoàn chỉnh, 161/161 sheet đọc thành công; 320 và
  325 km/h có OUT hội tụ, 155 dynamic inputs, `dt=0.001 s`. Tạo 10 MCT
  `grouped_by_train` cho 297 case chưa chạy, giữ nguyên 23 case đã có kết quả.
  File A1 thử nghiệm chứa 10 vận tốc 330–420 km/h; các block/function/case/graph
  và toàn bộ tham chiếu tải động đã qua kiểm tra cấu trúc.
- **2026-07-03**: BXD dynamic countercheck đã sửa `span_indices` để load path
  dùng chuỗi `Girder1..Girder5`; HSLM-A1 @ 330 km/h hiện có `155` dynamic nodal
  loads, `ETIME=8.142545455 s`, `dt=0.001 s`. User đã chạy lại MIDAS và export
  kết quả; OUT mới có `8142` time steps, valid DOF `895`, không thấy warning/error
  chính. Thêm harness
  `examples/bxd/generated/midas/build_dynamic_analysis_report.py`, tạo Word report
  `bao_cao_tinh_toan_phan_tich_dong_model_dynamic_countercheck_32_6_HSLM-A1_330.docx`
  và phụ lục Excel/Markdown. Tạo 4 skill dự án trong Codex skills: navigator,
  MCT dynamic hardener, MIDAS output reviewer, dynamic report builder.
- **2026-06-02**: Fix lỗi Midas `Material Name` tối đa 16 ký tự bằng cách xuất
  tên vật liệu theo `material.id` ngắn. Cập nhật `examples/hcm_cg/bridge.xlsx`
  thành base model 5 nhịp: 301 node, 254 element, 6 material, 9 section,
  36 boundary supports tại chân cọc, 6 rigid links đầu cọc↔đáy bệ. Chỉnh tiếp
  theo review: cọc dài 8 m, đổi đúng phương dọc/ngang layout cọc, `Pilecap`
  lấy riêng layer `pilecap` và `dxf_axis_order=yx` nên là hình chữ nhật đặc
  7.5×10.5 không có lỗ, xuất bằng built-in `SB , BUILT`; `Pier_Taper` đổi
  hướng `Pier_01 -> Pier_02` từ dưới lên. Sinh lại
  `generated/midas/model_base.mct` thành công; `validate` chỉ còn FAIL `Trains`
  vì chưa import HSLM/LM71/real train catalog. Đối chiếu
  `model_base_review.mct`: đã cập nhật 40 bearing nodes, 20 `*ELASTICLINK`,
  22 `*RIGIDLINK`, tapered Box-1-3/Box-3-1 cho dầm chính, `*TS-GROUP`,
  `*LOADTOMASS`, `*EIGEN-CTRL` 70 modes. Chưa tích hợp raw time-history
  HSLM-A1 (`*TFUNCTION`/`*THLDCASE`/`*DYN-NLOAD`) vì cần xác nhận strategy.
  Fix tiếp OPOLY/IPOLY không còn xóa điểm thẳng hàng trước khi ghi MCT; `Box-01`
  và `Box-03` hiện cùng giữ `OPOLY=48`, `IPOLY=12` theo DXF. 56/56 tests,
  ruff check/format, mypy strict sạch.
- **2026-06-01** (chiều 4): MCT writer sinh static load blocks: `*STLDCASE`,
  `*USE-STLD`, `*SELFWEIGHT`; `distributed_masses` hợp lệ sinh `*BEAMLOAD`
  `UNILOAD GZ` theo group. `*EIGEN-CTRL` vẫn pending vì thiếu field layout
  mẫu Midas 2022. 49/49 tests, ruff format/check, mypy strict sạch.
- **2026-06-01** (chiều 3): STIFF2 Cy/Cz lấy theo `section_model.mesh["vertices"]`
  để khớp reference Converte; DXF reader xử lý trực tiếp LWPOLYLINE bulge qua
  `ezdxf.math.bulge_to_arc`. 48/48 tests, ruff format/check, mypy strict sạch.
- **2026-06-01** (chiều 2): ARC/CIRCLE chia 10° trong DXF reader + `detect_circle`→
  `DBUSER SR/P` (cọc tròn). 46/46 tests. Checkpoint trước đó: commit `38bb43a`.
- **2026-06-01** (chiều): DXF section importer (`importers/dxf/`, cột `dxf_file`,
  auto-chain) + vá writer fallback OPOLY → mặt cắt hiển thị được trong Midas; verify
  trên `MG_01.dxf`. 43/43 tests.
- **2026-06-01**: Sync v0.2 (log 4 commit MCT generator/polygon section), verify
  pipeline mặt cắt khớp bản đã validate, research sub girder + xác nhận block
  keyword time-history, link `1_du_an/hcm_cg/`. Xem `TASK_LOG.md` 2026-06-01.
- **2026-05-29**: Plan rev1 → rev9, duyệt. Tạo 4 file md tracking. Khởi tạo
  project folder. Xem `TASK_LOG.md` cho lịch sử quyết định.

---

## Decisions log pointer

Quyết định gần nhất → `TASK_LOG.md` mục **"## 2026-05-29 — Plan rev9 chốt + project tracking files"**.

Quyết định kiến trúc tổng thể → `CLAUDE.md` §5.

---

## Quick links

- Plan đầy đủ: [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md) (bản trong repo)
- Entry point cho mọi agent/dev: [`AGENTS.md`](./AGENTS.md)
- Context cho Claude: [`CLAUDE.md`](./CLAUDE.md)
- History: [`TASK_LOG.md`](./TASK_LOG.md)
- Research model HSR HCM-CG (ngoài repo, dùng dựng model thật):
  - `C:\Backup\D\2026\09_Tinh_toan_cau_duong_sat_toc_do_cao\1_du_an\hcm_cg\input_parameters.yaml` (input trung lập, có TODO_CONFIRM)
  - `...\1_du_an\hcm_cg\MODEL_UNDERSTANDING.md` (node/element/vật liệu/mặt cắt)
  - `...\1_du_an\hcm_cg\SUB_GIRDER_RESEARCH.md` (sub girder cho Train Load Generator)
- Tài liệu nguồn:
  - Bản tính HSR HCM-CG: `C:\Backup\D\2026\09_Tinh_toan_cau_duong_sat_toc_do_cao\3_ho_so_tham_khao\202512-23_HSR-CG Ban Tinh Tong The H7H15m.pdf`
  - MIDAS UK HS2 Tutorial: `C:\Backup\D\2026\09_Tinh_toan_cau_duong_sat_toc_do_cao\docs\[Final]Dynamic Analysis for High Speed Two (HS2).pdf`
  - KD-Railway snapshots: `C:\Backup\D\2026\09_Tinh_toan_cau_duong_sat_toc_do_cao\3_ho_so_tham_khao\KD_Railway_software\Snapshot\`
