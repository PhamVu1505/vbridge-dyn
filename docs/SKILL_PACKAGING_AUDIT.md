# Skill Packaging Audit - VBridge-Dyn

Ngay lap tuc nen xem skill nhu "onboarding + loop guardrail" cho cac tac vu lap lai,
khong phai noi copy toan bo research. Repo hien da co 4 skill HSR trong Codex:

- `hsr-bridge-project-navigator`: vao workspace, doc status/log, dinh vi BXD/HCM-CG.
- `hsr-mct-dynamic-hardener`: sua/kiem MCT time-history cho BXD/HCM-CG.
- `hsr-midas-output-reviewer`: doc OUT/XLS/BMP MIDAS dynamic result.
- `hsr-dynamic-report-builder`: build Word report dynamic BXD tu harness.

Bon skill nay dung tot cho BXD dynamic single-case HSLM-A1 @ 330 km/h. De harness va
loop de goi nhanh hon, nen bo sung cac skill duoi day.

## Status 2026-07-08

Da tao va validate 9 skill moi trong `C:\Users\vupq.CITEC\.codex\skills`:

- `hsr-vbridge-harness-loop`
- `hsr-bxd-static-countercheck-loop`
- `hsr-bxd-dynamic-sweep-loop`
- `hsr-hcm-cg-model-builder`
- `hsr-dxf-section-tendon-loop`
- `hsr-tcvn-standards-loop`
- `hsr-midas-result-ingest-loop`
- `hsr-rm-to-midas-conversion-loop`
- `hsr-report-style-loop`

Tat ca pass `skill-creator/scripts/quick_validate.py`. Hai helper scripts da duoc
test dry-run:

- `hsr-vbridge-harness-loop/scripts/run_vbridge_harness.py`
- `hsr-bxd-dynamic-sweep-loop/scripts/collect_bxd_dynamic_sweep.py`

## Uu tien dong goi

| Priority | Skill de xuat | Ly do |
|---|---|---|
| P0 | `hsr-vbridge-harness-loop` | Mot lenh tu duy chung: chon dung test/harness theo loai thay doi, tranh moi lan phai nho pytest nao/script nao. |
| P0 | `hsr-bxd-static-countercheck-loop` | Static BXD 32.6 m co nhieu script, file export va quy uoc so sanh muc 5.1/5.2/5.8; hien chua co skill rieng. |
| P0 | `hsr-bxd-dynamic-sweep-loop` | Existing skill cover single dynamic case, nhung viec lap toc do 290-340/A1-A10 va gom peak/resonance can loop rieng. |
| P1 | `hsr-hcm-cg-model-builder` | HCM-CG co research ngoai repo, nhieu TODO_CONFIRM va logic sub girder rieng; nen dong goi de khong ap dung nham BXD one-girder logic. |
| P1 | `hsr-dxf-section-tendon-loop` | DXF section/tendon import la workflow mong manh: layer, axis order, ARC/bulge, DBUSER SR/SB, tendon layer numeric. |
| P1 | `hsr-tcvn-standards-loop` | v0.2/v0.3 can TCVN 13594 damping, speed range, dynamic_required, resonance, HSLM rules va tests parity. |
| P2 | `hsr-midas-result-ingest-loop` | Chuan hoa doc OUT/Excel/CSV, header row MIDAS, manifest -> storage; nen tach khi vao ingest/envelope v0.3. |
| P2 | `hsr-rm-to-midas-conversion-loop` | Can dung/port `refer/Converte_RM_to_Midas`; huu ich cho Phase 2 RM Bridge va section/ECC validation. |
| P2 | `hsr-report-style-loop` | Neu tiep tuc sinh Word/PDF nhieu dang report, tach style/layout/RM-style/docx conventions khoi dynamic report builder. |

## Candidate Details

### `hsr-vbridge-harness-loop`

Trigger:

- User noi "run harness", "kiem loop", "verify sau khi sua", "test BXD/HCM-CG",
  "audit output", "regression".

Nen doc:

- `AGENTS.md`, `PROJECT_STATUS.md`, newest `TASK_LOG.md`.
- `pyproject.toml` markers va current test layout.
- Relevant task skill neu co: MCT hardener, output reviewer, report builder.

Nen dong goi:

- Reference `references/harness-matrix.md`: mapping thay doi -> lenh test/script.
- Script wrapper optional `scripts/run_vbridge_harness.py` voi modes:
  `unit`, `mct`, `dxf`, `bxd-static`, `bxd-dynamic`, `report`.

Core loops:

- Code schema/Excel/DXF/MCT: chay narrow test truoc, sau do `pytest tests/unit -q`.
- BXD static: generate MCT -> rebuild comparison -> build Word/calculation report.
- BXD dynamic: generate/check MCT -> verify OUT/XLS result folder -> report harness.
- HCM-CG: validate project -> generate base MCT -> compare known counts/modal targets when available.

### `hsr-bxd-static-countercheck-loop`

Trigger:

- "BXD static", "dam 32.6", "muc 5.1/5.2/5.8", "LM71", "fatigue", "stage",
  "comparison_bxd_32_6", "bao cao tinh toan MIDAS".

Source anchors:

- `examples/bxd/static_countercheck_32_6.yaml`
- `src/vbridge_dyn/integrations/midas/mct/static_countercheck.py`
- `examples/bxd/generated/midas/rebuild_comparison_bxd_32_6.py`
- `examples/bxd/generated/midas/build_bxd_32_6_word_report.py`
- `examples/bxd/generated/midas/build_bxd_32_6_calculation_report.py`
- `examples/bxd/generated/midas/README.md`

Guardrails:

- G1 self-weight comes from MIDAS geometry/material; do not re-add report G1 as beam load.
- G2 report load is explicit and also enters mass where required.
- LM71 static moving load uses Eurocode moving load blocks; Phi here is static dynamic factor, not time-history.
- Stress convention: `Cb1/Cb2` top, `Cb3/Cb4` bottom; service stress uses max at midspan node, not all/min.

### `hsr-bxd-dynamic-sweep-loop`

Trigger:

- "sweep toc do", "A1-A10", "resonance", "tim peak", "dynamic 5.7",
  "290-340", "330 km/h khong khop", "mass/stiffness sensitivity".

Source anchors:

- `src/vbridge_dyn/integrations/midas/mct/dynamic_countercheck.py`
- `examples/bxd/static_countercheck_32_6.yaml`
- `examples/bxd/generated/midas/AGENT_HANDOFF_DYNAMIC.md`
- `examples/bxd/generated/midas/dynamic_result_review_2026_06_24.md`
- Existing result folders under `examples/bxd/generated/midas/model_dynamic_countercheck_32_6_*`

Guardrails:

- `span_index` is report span; `span_indices` is dynamic load path.
- Current chain case expects all `Girder1..Girder5`, 155 dynamic nodal loads,
  `dt=0.001 s`, `ETIME=8.142545455 s` for HSLM-A1 @ 330 km/h.
- Always compare node `100016` and global maxima separately.
- For modal participation, cumulate mode cluster 1-5 for UZ instead of trusting mode 1 alone.

Nen dong goi script:

- `scripts/collect_bxd_dynamic_sweep.py`: scan speed result folders, parse OUT/eigen/disp/accel,
  produce `sweep_summary.xlsx` and `sweep_summary.md`.

### `hsr-hcm-cg-model-builder`

Trigger:

- "HCM-CG", "Can Gio", "V09", "5 span", "sub girder", "Train Load Generator",
  "dynamic track line", "build bridge.xlsx from research".

Source anchors:

- `projects/hcm_cg/input_parameters.yaml`
- `projects/hcm_cg/MODEL_UNDERSTANDING.md`
- `projects/hcm_cg/SUB_GIRDER_RESEARCH.md`
- `examples/hcm_cg/project.yaml`, `examples/hcm_cg/bridge.xlsx`, `examples/hcm_cg/dxf/`
- `examples/hcm_cg/generated/midas/hcm_cg_midas_dynamic_logic_review_2026_06_24.md`

Guardrails:

- Do not assume BXD one-girder countercheck applies to HCM-CG.
- Main girder = structural beam; sub girder likely = dynamic track/dummy beam line
  for Train Load Generator.
- Static `*LINELANE` track can use element list + eccentricity; dynamic time-history
  strategy likely needs sub-girder beam line and rigid links.
- Treat all `TODO_CONFIRM` in `input_parameters.yaml` as unresolved unless a newer local model/export proves otherwise.

### `hsr-dxf-section-tendon-loop`

Trigger:

- "DXF section", "MG_01", "Pilecap", "tendon.dxf", "OPOLY/IPOLY",
  "ARC", "bulge", "DBUSER", "sectionproperties", "STIFF2/STIFF3".

Source anchors:

- `src/vbridge_dyn/importers/dxf/section_reader.py`
- `src/vbridge_dyn/importers/dxf/tendon_reader.py`
- `src/vbridge_dyn/integrations/midas/mct/sections.py`
- `src/vbridge_dyn/integrations/midas/mct/tendons.py`
- `tests/unit/test_dxf_section_reader.py`
- `tests/unit/test_tendon_dxf_reader.py`
- `tests/unit/test_mct_generation.py`
- `refer/Converte_RM_to_Midas/src/core/geometry.py`

Guardrails:

- Preserve collinear DXF polygon points for MCT OPOLY/IPOLY when required.
- Respect `dxf_layer` and `dxf_axis_order`.
- Tessellate ARC/CIRCLE/LWPOLYLINE bulge deterministically.
- Detect simple round/solid rectangle as MIDAS DBUSER SR/SB when correct.
- Tendon DXF BXD convention is project-specific; keep generalization explicit.

### `hsr-tcvn-standards-loop`

Trigger:

- "TCVN 13594", "damping", "dynamic_required", "speed_range", "resonance",
  "HSLM rules", "Vcr", "ERRI D214", "Eurocode parity".

Source anchors:

- `docs/PLAN_REV9.md`
- `CLAUDE.md` sections on standards and benchmarks.
- `projects/hcm_cg/input_parameters.yaml` dynamic reference values.
- Future package target: `src/vbridge_dyn/standards/vietnam/tcvn13594/`.

Guardrails:

- TCVN is primary; Eurocode is cross-check.
- Do not hard-code publication years; read `project.yaml > tcvn13594_versions`.
- Do not ship copyrighted train catalog tables as built-in data; use user-imported Excel or manually provided project data.
- V06/V07 parity should be hard tests; V09 remains soft until original model exists.

### `hsr-midas-result-ingest-loop`

Trigger:

- "ingest", "CSV/Excel export", "generation_manifest", "envelope",
  "column mapping", "MIDAS export format", "storage".

Source anchors:

- Existing `hsr-midas-output-reviewer`.
- `core/schemas/manifest.py`, `tests/unit/test_manifest_schema.py`.
- `examples/bxd/generated/midas/build_dynamic_analysis_report.py` parser patterns.
- `examples/bxd/generated/midas/rebuild_comparison_bxd_32_6.py` parser patterns.

Guardrails:

- MIDAS Excel response exports usually have header row at index 1 and data from row index 3.
- Response value/time columns are paired; node column usually index 2, load column usually index 3.
- Always cite exact local files and values for result claims.
- Keep manifest as source of case/station mapping; do not infer solely from filenames.

### `hsr-rm-to-midas-conversion-loop`

Trigger:

- "RM Bridge", "TCL", "Converte_RM_to_Midas", "ECC to rigid link",
  "section ID mapping", "STIFF3", "SPC", "MCT from RM".

Source anchors:

- `refer/Converte_RM_to_Midas/README.md`
- `refer/Converte_RM_to_Midas/WORKFLOW.md`
- `refer/Converte_RM_to_Midas/ARCHITECTURE.md`
- `refer/Converte_RM_to_Midas/CLAUDE.md`
- `projects/cau_song_duong/SongDuong/`

Guardrails:

- RM axis convention differs from MIDAS; preserve Y/Z swap.
- RM ECC must become MIDAS rigid links.
- STIFF3 stress points use max Euclidean distance from centroid per quadrant in the validated converter.
- Phase 2 only for VBridge-Dyn; do not pull RM writer into MVP unless scope changes.

### `hsr-report-style-loop`

Trigger:

- "bao cao Word/PDF", "RM style", "calculation report", "phu luc Excel",
  "captions", "layout 13 muc".

Source anchors:

- `examples/bxd/generated/midas/build_dynamic_analysis_report.py`
- `examples/bxd/generated/midas/build_bxd_32_6_calculation_report.py`
- `examples/bxd/generated/midas/phuong_an_trinh_bay_bao_cao_rm_style.md`
- `examples/bxd/generated/midas/report refer RM bridge/report.pdf`

Guardrails:

- Keep long tables in appendix workbook.
- Report text is Vietnamese.
- Report claims must be traceable to exact MCT/OUT/XLS inputs.
- Do not mix "comparison report" and "independent calculation report" deliverables silently.

## Nen cap nhat skill hien co

1. `hsr-bridge-project-navigator`
   - Add note that `references/project-map.md` is inside the skill folder.
   - Add current dirty/generated BXD artifact map and HCM-CG research anchors.

2. `hsr-mct-dynamic-hardener`
   - Keep as single-case MCT repair/audit skill.
   - Link to `hsr-bxd-dynamic-sweep-loop` once created for velocity sweep/aggregation.

3. `hsr-midas-output-reviewer`
   - Keep as result review skill.
   - Move reusable pandas parser snippets into scripts or references if result review becomes frequent.

4. `hsr-dynamic-report-builder`
   - Keep focused on `build_dynamic_analysis_report.py`.
   - Avoid expanding it to static report/style; create `hsr-report-style-loop` or `hsr-bxd-static-countercheck-loop`.

## Khong nen dong goi thanh skill rieng

- Tung PDF/DOCX goc rieng le: nen de trong references/project docs, chi mo khi can.
- Pure code implementation details cua moi module: nen de tests/docstrings; skill chi nen tro den narrow files.
- Generated MIDAS binary/cache files: skill nen chi biet folder/canonical file, khong nap noi dung.
- One-off owner confirmations: ghi vao `PROJECT_STATUS.md`/`TASK_LOG.md` thay vi skill.

## Thu tu lam de co loi nhanh

1. Tao `hsr-vbridge-harness-loop`.
2. Tao `hsr-bxd-static-countercheck-loop`.
3. Tao `hsr-bxd-dynamic-sweep-loop`.
4. Tao `hsr-hcm-cg-model-builder`.
5. Tao `hsr-dxf-section-tendon-loop`.
6. Tao `hsr-tcvn-standards-loop`.
7. Sau khi v0.3 ingest bat dau, tao `hsr-midas-result-ingest-loop`.
8. Khi Phase 2 RM Bridge bat dau, tao `hsr-rm-to-midas-conversion-loop`.
