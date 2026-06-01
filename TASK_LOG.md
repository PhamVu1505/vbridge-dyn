# Task Log — VBridge-Dyn

> Append-only. KHÔNG sửa entry cũ. Mỗi entry là 1 mốc thời gian / quyết định /
> task done. Format: `## YYYY-MM-DD — <Tiêu đề ngắn>`.

---

## 2026-06-01 — ARC chia theo góc (10°) + detect_circle→DBUSER

**Quyết định** (theo yêu cầu owner sau khi xác nhận MG_01 hiển thị đúng trong Midas):
chia ARC mặc định góc 10°; mặt cắt tròn xuất DBUSER. Đã commit checkpoint `38bb43a`
TRƯỚC khi làm 2 việc này.

**Đã làm**:
- `importers/dxf/section_reader.py`: `ARC`/`CIRCLE` chia theo **bước góc**
  (`arc_angle_deg`, mặc định **10°** — khớp Midas SPC) thay cho sagitta;
  `ELLIPSE`/`SPLINE` vẫn flatten theo sagitta. CIRCLE → vòng kín 36 đỉnh.
- `integrations/midas/mct/sections.py`: thêm `detect_circle()` + `CircleInfo` (port
  từ Converte `core/geometry`): hệ số biến thiên bán kính < 2% ⇒ tròn đặc (SR) /
  ống (P, 1 lỗ tròn đồng tâm).
- `integrations/midas/mct/writer.py`: tách section thành **2 khối** — `*SECTION`
  (DBUSER SR/P cho mặt cắt tròn, vd cọc D1500) + `*SECT-PSCVALUE` (GEN polygon còn lại).
- Tests: +3 (circle chia 10° = 36 đỉnh, override góc 30° = 12 đỉnh, circular section
  → DBUSER SR). **46/46 PASS**, ruff + mypy strict sạch.

**Verify**: CIRCLE D1.5 trong DXF → 36 đỉnh → `detect_circle` ra SR D≈1.5 → dòng
`*SECTION … DBUSER … SR`. MG_01 dầm hộp vẫn ra `*SECT-PSCVALUE` + OPOLY (KHÔNG nhận
nhầm tròn).

**Follow-up**: đổi STIFF2 sang mesh vertices; hỗ trợ LWPOLYLINE có bulge cong.

---

## 2026-06-01 — DXF section importer + vá writer fallback OPOLY

**Bối cảnh**: Midas không hiển thị mặt cắt vì writer phát `SHAPE=GEN` mà **thiếu
OPOLY** (section chỉ có A/Iy/Iz/J, không polygon → đi nhánh fallback). Owner xác
nhận nguồn mặt cắt = file DXF (`projects/hcm_cg/dxf/MG_01.dxf`).

**Quyết định** (qua AskUserQuestion):
- Section tham chiếu DXF qua **cột `dxf_file`** trong sheet Sections.
- Trích hình bằng **auto-chain toàn modelspace** (prune nhánh hở, vòng lớn nhất = bao ngoài).

**Đã làm**:
- Module mới `importers/dxf/section_reader.py` (`read_section_polygon`): ezdxf → gom
  LINE/ARC/POLYLINE/INSERT thành đoạn → đổi đơn vị theo `$INSUNITS` → nối đồ thị →
  **prune đỉnh bậc ≤ 1** (tự loại dimension/leader/text) → trace vòng kín → vòng lớn
  nhất = outer, còn lại = holes; map DXF(x,y)→section(y,z). Thêm `ezdxf>=1.1` vào extra `[sections]`.
- `workbook_reader.py`: đọc cột `dxf_file` (resolve theo thư mục workbook qua `base_dir`);
  A/Iy/Iz/J cho phép trống khi có polygon (placeholder 1.0, writer tính lại).
- `bridge_template_writer.py`: thêm cột `dxf_file` + note hướng dẫn 2 cách nhập hình.
- **Vá writer fallback** (`writer.py`): section không polygon → tự sinh **OPOLY chữ
  nhật** (±cy, ±cz) + warning; GEN section giờ LUÔN có hình hiển thị.
- Tests: `test_dxf_section_reader.py` (4 ca: outer+hole, mm→m, chuỗi hở raise, vòng
  lớn nhất=outer) + assert `OPOLY=` ở init template. **43/43 PASS**, ruff + mypy strict sạch.

**Verify thật trên MG_01.dxf** (đối chiếu file Midas đã chạy `MG-001`):
- `$INSUNITS=6` (m); dimension text khớp 1:1 hình học (H=3000↔3.0, ttop=300↔0.3, 7604↔7.6039).
- Trích: bao ngoài 14 đỉnh + 2 lỗ 7 đỉnh; shapely valid; net area **20.93 m²**.
- `vbdyn generate examples/hcm_cg` → `*SECT-PSCVALUE` đầy đủ STIFF1/2/3 + OPOLY + 2
  IPOLY, prefix CT — **cấu trúc giống hệt file thật**. Đã copy MG_01.dxf + thêm cột
  `dxf_file`/`mesh_size` vào `examples/hcm_cg/bridge.xlsx`.

**Cần owner xác nhận**: MG_01 rộng **35 m** (±17.5) × cao 3 m, 2 lỗ ở cánh — lệch
12.6 m trong `input_parameters.yaml` trước đó (có thể là section vẽ thử hôm nay).

**Follow-up**: hỗ trợ ARC/bulge cho mặt cắt trụ cong (MG_01 toàn LINE nên chưa cần);
port `detect_circle`→DBUSER cho cọc tròn.

---

## 2026-06-01 — Sync v0.2 + research sub girder & verify section generation

**Bối cảnh**: code đã đi trước tracking docs (4 commit v0.2 chưa log). Phiên này
đồng bộ docs + research thêm sub girder cho tải tàu + đối chiếu pipeline mặt cắt với
code tham khảo `refer/020_Chuyển_json_sang_mct_và_gan_mat_cat_V4.py`.

**Đã log các commit v0.2 (trước đó chưa ghi)**:
- `538f544` feat(v0.2): MCT generator đầu tiên (writer + generator + CLI `generate --target midas`).
- `c3fc17a` fix(mct): bỏ group boundary chưa khai báo.
- `11247f0` feat(mct): sinh polygon section OPOLY/IPOLY.
- `ea06a75` feat(excel): import polygon section geometry.
- Writer hiện sinh: header + `*NODE` + `*ELEMENT` + `*GROUP` + `*MATERIAL`(+color) +
  `*SECT-PSCVALUE` (polygon hoặc fallback stiffness-only) + `*CONSTRAINT` + `*RIGIDLINK`.
  Manifest mới sinh 1 case modal (`case_modal_base`). Test **39/39 PASS**.

**Verify mặt cắt (đối chiếu V4 + bản production Converte `src/`)**:
- `integrations/midas/mct/sections.py` của vbridge **KHỚP thuật toán ĐÃ KIỂM CHỨNG**
  trong `Converte_RM_to_Midas/src/core/geometry.py` (STIFF3 = max Euclidean distance từ
  centroid trên boundary đã simplify; 100% match 38 file Midas SPC). **KHÔNG** phải bản
  `020...V4.py` cũ — V4 dùng mesh vertices + tolerance top/bottom region, đã bị thay thế.
  STIFF1, arrangement STIFF3, thứ tự OPOLY (CCW từ Q1) / IPOLY (CW) đều khớp production.
- 3 điểm lệch so với bản production cần xử lý:
  1. **STIFF2 (CyP/CyM/CzP/CzM)**: vbridge lấy từ `translated_outer` (boundary đã
     simplify); production lấy từ **mesh vertices** (`section.mesh["vertices"]`). Cùng kết
     quả với mặt cắt cạnh thẳng → nên đổi sang mesh vertices cho đúng 100% reference (an
     toàn cả mặt cắt cong). Rủi ro thấp.
  2. **Thiếu circle→DBUSER**: production `detect_circle` → xuất `DBUSER SR/P` cho mặt cắt
     tròn/ống; vbridge luôn xuất GEN polygon. Ảnh hưởng **cọc D1500 HCM-CG** → nên port.
  3. Ngưỡng lọc hole: vbridge `< 3` điểm, production `< 4`. Edge case nhỏ.
- Lưu ý: example `examples/hcm_cg` hiện chỉ có section dạng stiffness (không polygon) nên
  nhánh polygon mới được cover bằng `test_mct_generation.py` (rectangle), chưa chạy trên
  dầm hộp thật.

**Research sub girder (chi tiết → `projects/hcm_cg/SUB_GIRDER_RESEARCH.md`)**:
- `*LINELANE` template: track **tĩnh** Eurocode = element-list + ECC ngang trên phần tử
  có sẵn (KHÔNG cần sub girder). Sub girder 601..785 chỉ cần khi dùng Train Load Generator
  (time-history **động**) — đúng strategy mặc định HCM-CG.
- Đã xác nhận TÊN block MCT động (MIDAS manual): `*EIGEN-CTRL`, `*TFUNCTION`, `*THLDCASE`,
  `*DYN-NLOAD` (+ `*MOVE-CTRL`/`*MVLDCASE` cho moving load tĩnh). Field layout vẫn cần file
  mẫu (B1).

**Liên kết research vào repo**: thêm trỏ tới `projects/hcm_cg/` (MODEL_UNDERSTANDING,
SUB_GIRDER_RESEARCH, input_parameters.yaml) trong `CLAUDE.md` §8 + `PROJECT_STATUS.md`.

**Lý do**: tránh repo lệch khi chuyển máy/agent; chốt rằng pipeline mặt cắt đang theo
đúng bản đã validate; làm rõ điều kiện cần sub girder trước khi code v0.2 dynamic.

**Blockers**:
- B1 cập nhật: đã biết TÊN block time-history, vẫn cần file MCT mẫu Midas 2022 để lấy
  field layout + cách Train Load Generator sinh `*DYN-NLOAD`/`*TFUNCTION`.

---

## 2026-05-29 — Fix mypy, lock manifest schema, đổi tên test (P1-P3 follow-up)

**Quyết định** (theo review user):

- **P1 — Fix 9 mypy errors** (CI sẽ fail nếu không fix):
  - `train.py:36`: `catalog_meta: dict` → `dict[str, Any]` (thêm `from typing import Any`)
  - `workbook_reader.py:23`: thêm type `ws: Worksheet`
  - `workbook_reader.py:188`: signature `read_bridge_workbook() -> Bridge` → `tuple[Bridge, list[Track]]` (đúng với thực tế trả 2-tuple)
  - `workbook_reader.py:202`: thêm type `wb: Workbook` cho `_read_tracks`
  - `project_io.py:6` + `validate.py:8`: thêm `types-PyYAML>=6.0` vào dev deps
  - `validate.py:45`: `tracks_from_excel: list` → `list[Track]` (import Track)
  - `validate.py:48`: type của `raw` được khóa `dict[str, Any]`, tuple unpack từ read_bridge_workbook giờ đúng type
  - `pyproject.toml`: dọn `[[tool.mypy.overrides]]` chỉ giữ `openpyxl.*` (các deps khác đã có stubs hoặc không import)
  - Verify: `mypy src` → "Success: no issues found in 28 source files"

- **P2 — Lock `generation_manifest.json` schema** (acceptance v0.1):
  - `core/schemas/manifest.py`: `GenerationManifest` + `CaseEntry` + `StationRef`
  - Trường chính: target, target_version, run_id, generated_at, vbridge_dyn_version, project_name, project_hash, case_split_strategy, moving_load_strategy, cases (list), output_dir, expected_solver_outputs_dir
  - CaseEntry: case_name, case_kind (modal | time_history | static_envelope), mct_file, expected_csv_name, train_id, velocity_kmh, stations, signals, midas_load_case_name, time_history_case_name
  - StationRef: station_id, midas_node_ids, midas_element_ids, interpolation (direct | linear), eta
  - Helper properties: n_cases, trains_covered, velocities_kmh
  - 8 tests trong `test_manifest_schema.py`: required fields, train coverage, velocities, case kinds, interpolation modes, JSON roundtrip + file IO, grouped_by_train invariant, validation negative cases
  - Re-export trong `core/schemas/__init__.py`
  - Wording PROJECT_STATUS.md: "v0.1 skeleton hoàn tất" → "foundation skeleton complete; v0.1 acceptance đã đạt" để chính xác (vẫn in-progress về tuần 1/3 nhưng đã đạt acceptance)

- **P3 — Đổi tên test cho đúng coverage thật**:
  - `test_validate_empty_bridge_reports_failures` → `test_validate_template_only_reports_missing_trains` (rõ ràng: template có sample hợp lệ nên Bridge PASS, chỉ FAIL vì Trains rỗng — đó là expected behavior)
  - Thêm test mới `test_validate_missing_supports_fails_bridge_check`: xóa Supports khỏi bridge.xlsx bằng openpyxl → validate fail ngay ở bridge level (cover scenario user xóa data)

**Verify final**:
- ruff check: PASS
- ruff format --check: PASS
- mypy src: 28 files, no issues
- pytest tests/unit: 33/33 PASS (24 cũ + 8 manifest + 1 missing supports = 33)

---

## 2026-05-29 — v0.1 skeleton chạy được (init + validate + tests)

**Đã làm**:
- `pyproject.toml`: pip + uv compat, hatchling build, deps cứng (pydantic v2, typer, rich, pyyaml, pandas, openpyxl, numpy, scipy, pyarrow, matplotlib, reportlab, jinja2, loguru, h5py), optional `ui` (PySide6/pyqtgraph/pyvista), `sections` (sectionproperties/shapely/chardet), `dev` (pytest/hypothesis/ruff/mypy/pre-commit).
- `src/vbridge_dyn/` skeleton:
  - `core/schemas/`: units, geometry, properties, boundary, mass, groups, track, train, analysis, result_station, bridge, project (12 modules + __init__).
  - `io/`: project_io (YAML load/save), project_templates (sinh project.yaml mẫu).
  - `importers/excel/`: bridge_template_writer (11 sheets có sample + comment tiếng Việt) + workbook_reader (parse → Bridge schema).
  - `cli/main.py` + `cli/commands/{init,validate}.py`: Typer app với `--version`, `info`, `init`, `validate`. Validate tự load bridge.xlsx khi project.yaml bridge rỗng.
- Tests: 23/23 PASS
  - `test_schemas.py` (17 tests): Bridge ref consistency, Support binary, RigidLink dof_mask, ElementRelease, Track accel_limit, ResultStation target, Project defaults
  - `test_cli_init_validate.py` (4 tests): init creates folders, validate empty fails, info, --version
  - `test_excel_template_roundtrip.py` (2 tests): write template → read back → check schema
- Lint: ruff check + format clean (allow `×`, `≡`, `≥`, `°` Unicode khoa học; allow Typer B008 idiom + physics N815 cho alpha_T).
- CI workflow `.github/workflows/ci.yml`: lint+mypy + tests trên ubuntu+windows × py3.11/3.12 + schedule weekly cho V03-V05/V09 reference benchmarks.
- `.gitignore` + `LICENSE` (Apache-2.0).
- `examples/hcm_cg/` init thành công, validate ra hầu hết PASS (chỉ FAIL Trains vì user chưa import HSLM/LM71 từ Excel — B2 blocker, expected).

**Quyết định kỹ thuật**:
- Validate dispatch: nếu `project.yaml > bridge` rỗng và `bridge.xlsx` tồn tại → tự load Excel merge vào Bridge schema. User không cần copy data từ Excel sang YAML.
- Template `bridge.xlsx`: 11 sheets (Nodes/Elements/Materials/Sections/Supports/ElasticLinks/RigidLinks/NodalMasses/DistributedMasses/StructureGroups/Tracks) + `_README` sheet với hướng dẫn tiếng Việt. Đơn vị nội bộ SI; exporter sẽ tự đổi.
- Project.yaml: comment tiếng Việt dẫn dắt từng block (standards_profile, tcvn13594_versions, design, dynamic, velocity_range, analysis, targets, checks, report).

**Đã reverse-engineer MCT mẫu** (`refer/template_mct/16 Eurocode Rail loads Final.mct`, Midas 9.1.0, 2534 dòng, 36 sections):
- File mẫu dùng pattern **moving load Eurocode** (`*MVLDCODE=EUROCODE`, `*LINELANE`, `*VEHICLE`, `*MVLDCASE(EURO)`, `*MV-DYFG`, `*MOVE-CTRL`) — đây là **static moving load + DAF** (giải pháp cho LM71/SW/0/SW/2), KHÔNG phải dynamic time-history.
- Để làm **dynamic transient HSLM** (theo plan: `moving_load_strategy: time_history_function`) cần thêm `*EIGEN-CTRL`, `*TIME-HISTORY-FUNCTION`, `*TIME-HISTORY-LOAD`, `*TIME-HISTORY-CASE`, `*MODAL-DAMPING`. v0.2 sẽ research thêm sample MCT có time-history.
- Tham khảo `refer/Converte_RM_to_Midas` (private, PhamVu1505): pipeline 12 steps (010-095), `sectionproperties` lib để tính Area/Iy/Iz/J/Asy/Asz từ outer boundary, ECC→Rigid Link conversion, STIFF3 max Euclidean distance from centroid (đã validated 100% match Midas SPC trên 38 file).

**Blockers**:
- B1 (vẫn open): cần thêm MCT mẫu có **time-history block** + có HSLM time function — để v0.2 sinh được full dynamic case.
- B5 (mới): repo push lên GitHub bị auto mode chặn — user cần chạy `!gh repo create vbridge-dyn --private --source=... --remote=origin --push` thủ công, hoặc cấp permission.

---

## 2026-05-29 — Sửa 3 điểm còn lệch sau review P1-P3

**Quyết định** (theo review tiếp theo của user):

- **PLAN_REV9.md §Verification & Validation** đồng bộ với CLAUDE.md §7: tách
  thành 2 nhóm
  - **Hard benchmarks** (V01-V02 analytical + V06-V07 parity + V08 Phase 2 +
    V10 Phase 3) — tolerance cứng, CI gate
  - **Reference comparisons** (V03-V05 + V09) — soft, chỉ nâng lên cứng khi có
    file model gốc trong repo.
- **Rule test trên PR đồng bộ** ở 3 file:
  - CLAUDE.md §9 conventions: V01-V02 + V06-V07 mỗi PR; V03-V05/V09
    weekly/on-demand; V08/V10 theo phase.
  - AGENTS.md §6: cùng nội dung, format ngắn gọn.
  - PLAN_REV9.md §V&V: thêm subsection "CI chính sách" rõ ràng.
- **README.md §Vai trò bước 4**: "Eurocode/TCVN checks" → "checks theo
  `standards_profile` (mặc định TCVN 13594, Eurocode cross-check)" để phản ánh
  đúng quyết định TCVN là chính.

**Đã làm**:
- Edit `docs/PLAN_REV9.md`: bảng V&V tái cấu trúc thành 2 nhóm + CI policy.
- Edit `CLAUDE.md`: line "Test V01-V07 ... V08-V09 ..." sửa thành mô tả Hard
  vs Reference comparisons.
- Edit `AGENTS.md`: §6 "Test trước khi commit" sửa cùng nội dung.
- Edit `README.md`: "Eurocode/TCVN checks" → "checks theo standards_profile".

**Lý do**: 3 file (plan + claude.md + agents.md) phải nhất quán về benchmark
groups và CI rules, nếu không reviewer mới hoặc agent khác đọc sẽ thấy mâu
thuẫn — đó là root cause của review này.

---

## 2026-05-29 — Áp dụng review P1-P3 trước khi vào v0.1

**Quyết định** (theo 5 điểm review user nêu):

- **P1**: Plan rev9 đã được **copy vào repo** tại
  [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md). Mọi reference trong CLAUDE.md +
  PROJECT_STATUS.md trỏ về đường dẫn nội bộ thay vì
  `C:\Users\...\.claude\plans\...`. Repo trở thành self-contained, chuyển máy
  / agent khác vẫn có plan đầy đủ.
- **P2 (1)**: Thêm `AGENTS.md` ở repo root — entry point ngắn cho mọi agent
  (Codex, Cursor, dev mới). Nội dung: đọc 3 file (CLAUDE.md, PROJECT_STATUS.md,
  TASK_LOG.md) trước khi sửa code; 3 nguyên tắc MVP; quy tắc handoff.
- **P2 (2)**: Tách bảng Benchmarks trong CLAUDE.md §7 thành **2 nhóm rõ**:
  - **Hard benchmarks** (V01, V02, V06, V07, V08, V10) — có analytical/parity
    rõ → tolerance cứng, CI gate.
  - **Reference comparisons** (V03 KD-Railway, V04 HS2 eigen, V05 HS2 envelope,
    V09 HSR HCM-CG) — chỉ có PDF, **chưa có file model gốc** → soft acceptance
    (xu hướng + order-of-magnitude + report layout). Khi có file model thật
    mới đổi sang tolerance cứng.
  - Phù hợp với quyết định "soft" đã ghi ở rev7.
- **P3 (1)**: README.md sửa diễn đạt "Sinh `.mct` cho **từng case**" → "sinh
  `.mct` theo strategy đã chọn (mặc định `grouped_by_train`: 1 file/train,
  nhiều velocity cases)" + nhắc rõ `generation_manifest.json` bắt buộc.
- **P3 (2)**: PROJECT_STATUS.md v0.1 checklist thêm 2 task tách riêng:
  - `generation_manifest.json` schema + writer (pydantic)
  - `export_instructions.md` template generator
  Acceptance v0.1 mới thêm dòng: "manifest schema được khóa với sample output".
  Acceptance v0.2 cập nhật: phải có manifest đầy đủ cho case modal.

**Đã làm**:
- Tạo `vbridge-dyn/docs/` folder; copy plan `t-i-mu-n-ph-t-tri-n-polished-walrus.md` thành `docs/PLAN_REV9.md` (60 KB).
- Tạo `vbridge-dyn/AGENTS.md` (entry point).
- Edit `CLAUDE.md`: header tham chiếu AGENTS.md, mapping pointer đổi sang
  `docs/PLAN_REV9.md`, §7 Benchmarks tách 2 bảng, §8 đổi pointer plan.
- Edit `README.md`: diễn đạt MCT generation strategy, link AGENTS/PLAN_REV9.
- Edit `PROJECT_STATUS.md`: refs plan, v0.1 checklist thêm manifest/export
  guide, v0.1 acceptance thêm manifest schema, v0.2 acceptance bổ sung.

**Lý do**: theo review của user, repo phải self-contained, các agent ngoài
Claude cũng có entry point, benchmark V03-V05 không được đặt cứng khi chưa có
file model gốc, và manifest là xương sống MVP nên phải first-class trong
checklist.

---

## 2026-05-29 — Plan rev9 chốt + project tracking files

**Quyết định**:
- Tổ chức tracking với **4 file md ở root repo**:
  - `README.md` (cho người mới vào repo, tiếng Việt)
  - `CLAUDE.md` (auto-load cho Claude, single source of truth về kiến trúc)
  - `PROJECT_STATUS.md` (snapshot hiện tại, update khi đổi version/milestone)
  - `TASK_LOG.md` (history append-only, file này)
- Quyết định chọn phương án A "3 file gọn" + README riêng (qua AskUserQuestion).
- Lý do: tránh phân mảnh và mâu thuẫn nội dung như khi có 7 file (TASK_CURRENT
  + TASK_NEXT + SCOPE riêng).

**Đã làm**:
- Tạo `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn\`
- Tạo `README.md`, `CLAUDE.md`, `PROJECT_STATUS.md`, `TASK_LOG.md`

---

## 2026-05-29 — Plan rev8: MVP chốt với Midas Civil 2022

**Quyết định**:
- `midas_version: "2022"` mặc định (KHÔNG 2024/NX).
- Reverse-engineer MCT bắt buộc từ Midas Civil 2022.
- **Civil NX/API → v1.2+ future**, KHÔNG nằm trong MVP.
- `runner.py` optional ngoài MVP, không trong acceptance.
- Thêm vào `generated/midas/`:
  - `generation_manifest.json` — map case → train/velocity/CSV expected/stations/nodes
  - `export_instructions.md` — hướng dẫn user export từ Midas thủ công
  - `result_export_template.xlsx` — template để chuẩn hóa CSV ingest
- `case_split: grouped_by_train` default → ~10-11 file MCT cho 500 cases
  (gộp velocities cùng train), file tên `case_th_hslm_a1.mct` không
  `case_th_hslm_a1_v140.mct`.
- Pipeline `[8]` đổi "Eurocode checks" → "checks (dispatch theo
  standards_profile)".
- Pipeline `[9]` PDF "13 mục" (không 11).
- UI status sửa "Generated 11 .mct files / 510 cases (grouped_by_train)".

**Lý do**: anh xác nhận có license Midas Civil 2022, không có Civil NX. Yêu cầu
MVP chỉ sinh model + user chạy tay + ingest CSV.

---

## 2026-05-29 — Plan rev7: Consistency

**Quyết định**:
- TCVN 13594-4 mặc định **2022** (override "2023" nếu cần). Tra VSQI: TCVN
  13594-4:2022 còn hiệu lực.
- `dynamic_required.py` comment trung tính: "kiểm tra theo TCVN 13594 profile";
  clause map qua `version_registry.py` (3:2022 Hình 31 hoặc 4 §5.1 tùy bản).
- Đổi `postprocessor/checks_eurocode.py` → `postprocessor/checks.py` (dispatch
  theo `standards_profile`).
- `moving_load_strategy: time_history_function` default cho Midas Civil 2022,
  `rail_track_analysis` experimental (cần verify cú pháp/ý nghĩa).
- UI wireframe: "Damping [EN 1991-2]" → "Damping [standards_profile]" (label
  động).
- Catalog file names trung lập: `hslm_catalog.xlsx`, `static_train_loads.xlsx`,
  `real_trains.xlsx` (bỏ prefix `eurocode_` hoặc `tcvn_`).
- Acceptance v0.2-v0.3 mềm hơn: với HSR-CG/HS2/KD-Railway → kiểm tra **xu
  hướng + critical speed approximate + report layout + postprocess logic**
  thay vì ±3%/±5% cứng (vì chưa có file model gốc).
- Report PDF nhất quán **13 mục** (đã sửa từ "11 mục" còn sót).

---

## 2026-05-29 — Plan rev6: Vietnam standards flat structure

**Quyết định**:
- Đổi `standards/vn/tcvn_13594/part_X/` → `standards/vietnam/tcvn13594/` flat.
- Files theo capability: `dynamic_required.py`, `train_loads.py`,
  `hslm_rules.py`, `speed_range.py`, `damping.py`, `acceleration.py`,
  `resonance.py`, `load_actions.py`, `load_distribution.py`, `combinations.py`,
  `version_registry.py`.
- Thêm vào `project.yaml`:
  - `standards_profile: vietnam_tcvn13594`
  - `tcvn13594_versions` block (đọc năm xuất bản theo project)
  - `design` block (design_speed_kmh, max_analysis_speed_factor, track_type)
  - `dynamic` block (check_required_method, damping_method, resonance_check,
    time_step_method)
- Benchmark V09 — HSR-CG typical span với giá trị cụ thể từ bản tính PDF:
  - Solver: MIDAS Civil 2025, HSLM-A, ξ=1%, dt=0.001s
  - Vtk=350 km/h, Vmax=420 km/h
  - **f_bending ≈ 5.9312 Hz**, **f_torsion ≈ 16.35 Hz**, **Vcr ≈ 384.34 km/h**
  - Tolerance: soft (vì chưa có file model MIDAS gốc).
- Report PDF thêm mục: Vcr theo k=1..4, f_bending/f_torsion highlight, bảng
  Vmin/Vtk/Vmax, phản ứng tại Vtk + Vmax, biểu đồ xu hướng gia tốc theo vận
  tốc, kiểm tra điều kiện cần phân tích động.
- KHÔNG hard-code năm TCVN trong source code.

---

## 2026-05-29 — Plan rev5: TCVN làm tiêu chuẩn chính

**Quyết định**:
- Đọc bản tính HSR HCM-CG (575 trang) → liệt kê bộ TCVN 13594:2022-2023:
  - TCVN 13594-3:2022 (Tải trọng) — cốt lõi
  - TCVN 13594-4 (Phân tích) — cốt lõi
  - + TCVN 13594-5/6/7/8/9/10 + TCVN 2737/5574/9386/10304
- Tiêu chuẩn **chính = TCVN 13594**, Eurocode = tham chiếu kỹ thuật.
- Tải trọng đoàn tàu mở rộng: LM71 + SW/0 + SW/2 + HSLM-A1..A10 + HSLM-B +
  Tàu rỗng + Đoàn tàu thực + custom.
- Tải trọng phụ: kéo/hãm (QLAK, QLBK), ly tâm, lắc ngang, khí động học.
- Tổ hợp tải trọng theo Bảng A.1 TCVN 13594-3 (ψ0/ψ1/ψ2) + ULS + SLS +
  Accidental.
- Damping theo Bảng 18 TCVN 13594-3 (≡ EN 1991-2 6.4.6.3 Table 6.6).
- Acceleration limit 3.5/5.0 m/s² theo TCVN 13594-4 (≡ EN 1990 A2.4.4.2).

---

## 2026-05-29 — Plan rev4: 3 nguyên tắc MVP first-class

**Quyết định**:
- Đưa 3 nguyên tắc MVP lên đầu plan như ràng buộc cứng:
  1. MVP = 5 module nền cho Midas (MCT gen + Excel import + reader +
     postprocess + report).
  2. RM Bridge: skeleton + schema-ready, Phase 2.
  3. KHÔNG tự viết solver. Midas/RM là engine.
- Bất kỳ tính năng nào vi phạm 3 nguyên tắc → out of scope.

---

## 2026-05-29 — Plan rev3: Pre+Post processor cho Midas/RM Bridge

**Quyết định** (qua AskUserQuestion):
- Vai trò cốt lõi = **Pre + Post processor cho Midas Civil + RM Bridge**, không
  có solver nội bộ.
- Solver target = **Cả Midas Civil + RM Bridge** (Rolling Stock module).
- Result IO = User export CSV/Excel từ Midas/RM → app đọc.
- Input format = Excel/CSV.
- Project workspace = folder-based.
- Storage = **Parquet + SQLite combo** (TH → Parquet, envelope/meta →
  SQLite).
- UI = Desktop PySide6 + CLI Typer.
- Ngôn ngữ = tiếng Việt.
- Catalog HSLM/real trains mặc định **EMPTY**; user import Excel (tránh bản
  quyền EN).
- Architecture: tách `core/` (trung lập) + `standards/` (tiêu chuẩn có
  version) + `integrations/` (Midas/RM coupling) + `services/orchestration` +
  `ui/cli interface`.
- Data model bổ sung: ElementRelease, ElasticLink, RigidLink, NodalMass,
  ElementDistributedMass, StructureGroup, BoundaryGroup, LoadGroup,
  CoordinateSystem, ResultStation, UnitSystem.
- Capability-based MCT blocks naming (geometry/properties/boundary/...) thay
  vì MCT-keyword-based.

---

## 2026-05-29 — Plan rev1-rev2: Khám phá phương án

**Đã làm**:
- Đọc `docs/[Final]Dynamic Analysis for High Speed Two (HS2).pdf` (40 trang
  MIDAS UK Tutorial). Tóm tắt:
  - Eurocode flowchart NA.12 (BS EN 1991-2)
  - Eigenvalue + modal superposition
  - ERRI D214 time-step formula: `dt = min(1/(8fmax), Lmin/(200v),
    Lmin/(4nv), 0.001s)`
  - Damping EN 1991-2 6.4.6.3 Table 6.6
  - HSLM-A (A1..A10) + HSLM-B + 12 real trains
  - Load distribution 3 rail pads (EN 1991-2 6.3.6.3)
  - Acceleration limit 3.5/5.0 m/s²
- Xem 8 snapshot KD-Railway → hiểu UX panels (Structural Properties, Load
  HSLM, Options, Calculation toolbar).
- Web search: KD-Railway (UTT Vietnam, Cast3M backend, C#/.NET WinForms),
  CALDINTAV, OpenSeesPy.

**Phương án ban đầu** (đã được thay thế bởi rev3+): solver nội bộ OpenSeesPy
+ MCT export. → Sau khi user feedback "thống nhất Midas/RM làm engine" →
chuyển sang Pre+Post processor architecture.

---

## Quy ước viết log entry

```markdown
## YYYY-MM-DD — Tiêu đề ngắn

**Quyết định** (nếu có):
- Bullet list

**Đã làm**:
- Bullet list

**Lý do** (nếu non-obvious):
- ...

**Blockers mới phát sinh** (nếu có):
- B# - mô tả
```
