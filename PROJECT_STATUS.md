# Project Status — VBridge-Dyn

> **Last updated**: 2026-05-29
> Mỗi khi đóng/mở task lớn, đổi version, hoặc gặp blocker — update file này.

---

## Current version

**v0.0 — Pre-foundation** (chưa bắt đầu v0.1)

- [x] Plan rev9 đã được duyệt — bản trong repo: [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md)
- [x] Project folder `vbridge-dyn/` đã tạo
- [x] 4 file tracking md đã tạo: `README.md`, `CLAUDE.md`, `PROJECT_STATUS.md` (file này), `TASK_LOG.md`
- [x] `AGENTS.md` đã tạo (entry point cho mọi agent/dev)
- [x] `docs/PLAN_REV9.md` đã copy vào repo (self-contained, không phụ thuộc `.claude/`)
- [ ] **Bắt đầu v0.1** sau khi user xác nhận hoặc tự khởi động khi sẵn sàng

---

## Active focus (v0.0 → v0.1)

### Việc tiếp theo cần làm

1. [ ] Khởi tạo `pyproject.toml` + `uv.lock` + `src/vbridge_dyn/` skeleton
2. [ ] Setup CI: ruff + mypy + pytest + pre-commit
3. [ ] Pydantic schemas v0.1 (theo `CLAUDE.md` §4):
   - [ ] `core/schemas/units.py`
   - [ ] `core/schemas/geometry.py` (Node, Element, CoordinateSystem)
   - [ ] `core/schemas/properties.py` (Material, FrameSection, ElementRelease)
   - [ ] `core/schemas/boundary.py` (Support, ElasticLink, RigidLink)
   - [ ] `core/schemas/mass.py` (NodalMass, ElementDistributedMass)
   - [ ] `core/schemas/groups.py` (StructureGroup, BoundaryGroup, LoadGroup)
   - [ ] `core/schemas/track.py`
   - [ ] `core/schemas/train.py`
   - [ ] `core/schemas/analysis.py`
   - [ ] `core/schemas/result_station.py`
   - [ ] `core/schemas/project.py`
4. [ ] Excel template + reader: `importers/excel/templates/bridge_template.xlsx` + `workbook_reader.py`
5. [ ] **Reverse-engineer 1 file MCT từ Midas Civil 2022** (cần file mẫu từ anh — B1)
6. [ ] `cli/main.py` + `vbdyn init` + `vbdyn validate`
7. [ ] **`generation_manifest.json` schema + writer** — *bắt buộc cho MVP vì không có API*; định nghĩa pydantic schema cho manifest (train, velocity_kmh, case_name, expected_csv_name, result_stations, node/element IDs)
8. [ ] **`export_instructions.md` template generator** — sinh hướng dẫn cho user export từ Midas tay tới đâu, file CSV nào ứng case nào

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
