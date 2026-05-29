# Project Status — VBridge-Dyn

> **Last updated**: 2026-05-29
> Mỗi khi đóng/mở task lớn, đổi version, hoặc gặp blocker — update file này.

---

## Current version

**v0.1 — Foundation (in-progress, tuần 1/3)** — foundation skeleton complete; v0.1 acceptance đã đạt

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
- [x] Tham khảo `refer/Converte_RM_to_Midas` (private repo): pipeline pattern, sectionproperties lib, ECC→Rigid Link, STIFF3 Euclidean
- [x] **`generation_manifest.json` schema khóa** (GenerationManifest + CaseEntry + StationRef, pydantic v2 trong `core/schemas/manifest.py`) + 8 tests roundtrip/validation
- [x] mypy strict clean (28 source files), ruff check + format clean, 33/33 tests PASS

---

## Active focus (v0.0 → v0.1)

### Việc tiếp theo (v0.1 → v0.2)

1. [x] `pyproject.toml` + skeleton + CI workflow
2. [x] Pydantic schemas + Excel template + reader
3. [x] CLI `init` + `validate` (load Excel auto-merge)
4. [x] Reverse-engineer MCT mẫu `16 Eurocode Rail loads Final.mct` (block structure đã document)
5. [ ] **Push code lên GitHub** — chờ user chạy lệnh `!gh repo create ...` (auto mode chặn)
6. [ ] **`generation_manifest.json` schema + writer** — pydantic schema cho manifest mapping
7. [ ] **`export_instructions.md` template generator** — hướng dẫn user export CSV
8. [ ] v0.2: `integrations/midas/mct/{writer + blocks/}` cho geometry + properties + boundary + mass + groups + analysis_control
9. [ ] v0.2: `standards/vietnam/tcvn13594/{damping, dynamic_required, speed_range, resonance, hslm_rules}.py`
10. [ ] v0.2: Sinh được `case_modal.mct` cho 1 nhịp giản đơn, mở được trong Midas Civil 2022
11. [ ] `examples/hcm_cg/`: nâng cấp bridge.xlsx lên 5 nhịp Main+Sub girder khi có dữ liệu cụ thể từ B1

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
| B1 | Cần file MCT sample từ **Midas Civil 2022** để reverse-engineer block format | v0.1 | Vũ (cung cấp) | OPEN — đề nghị anh export 1 file mẫu cho cầu đơn giản |
| B2 | Cần catalog HSLM/LM71 Excel cho TCVN 13594-3 Bảng 15 | v0.2 | Vũ (cung cấp dữ liệu Bảng) | OPEN — sẽ nhập tay từ TCVN |
| B3 | Cần xác nhận format CSV export chuẩn của Midas Civil 2022 (cột nào, encoding nào) | v0.3 | Vũ (export sample) | OPEN |
| B4 | Cần sample TCL của RM Bridge với module Rolling Stock | v0.5 | Vũ (cung cấp) | OPEN — Phase 2, chưa gấp |

---

## Recent changes

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
- Tài liệu nguồn:
  - Bản tính HSR HCM-CG: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\refer\202512-23_HSR-CG Ban Tinh Tong The H7H15m.pdf`
  - MIDAS UK HS2 Tutorial: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\docs\[Final]Dynamic Analysis for High Speed Two (HS2).pdf`
  - KD-Railway snapshots: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\refer\KD_Railway_software\Snapshot\`
