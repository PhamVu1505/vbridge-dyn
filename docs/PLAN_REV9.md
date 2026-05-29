# VBridge-Dyn — Phần mềm tự động hóa phân tích động cầu HSR

> **Vai trò**: lớp tự động hóa (modeling + case setup + report) cho **Midas Civil** (MVP) và **RM Bridge** (Phase 2), không có solver nội bộ.
> Working dir: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges`
> **Phiên bản plan**: rev9 — thêm section **Project tracking files** (4 file md ở root repo: `README.md`, `CLAUDE.md`, `PROJECT_STATUS.md`, `TASK_LOG.md`) để dự án dài không mất context giữa các phiên Claude/người làm. rev8 — chốt MVP (Midas Civil **2022** mặc định; loại Civil NX/API khỏi MVP roadmap; runner.py optional, không nằm trong acceptance; thêm `generation_manifest.json` + `export_instructions.md` + `result_export_template.xlsx` trong generated/; fix các inconsistency: TCVN checks, 13 mục, grouped_by_train naming `case_th_hslm_a1.mct`, UI status sửa số file; tiêu chuẩn TCVN 13594-4:2022 mặc định).
>
> **MVP chốt**: (1) Sinh `.mct` cho **MIDAS Civil 2022**. (2) User import/run/export CSV **thủ công**. (3) App ingest CSV → tìm case bất lợi → vẽ envelope/time-history → xuất PDF tiếng Việt. (4) **Không API, không NX, không solver nội bộ, không RM thật** trong MVP.

---

## Nguyên tắc MVP — ĐÃ CHỐT

> Ba ràng buộc cứng cho mọi quyết định kiến trúc & lộ trình:

1. **MVP = 5 module nền cho Midas**: MIDAS MCT generator + Excel importer + Midas result CSV reader + postprocessor + PDF report.
   Mọi tính năng ngoài 5 module này đều **không** thuộc MVP.
2. **RM Bridge: skeleton + schema-ready, triển khai Phase 2.**
   Ở MVP chỉ tạo thư mục `integrations/rm_bridge/` với skeleton + đảm bảo `core/schemas` đủ trường để Phase 2 không phải refactor. **Không** viết writer/reader RM thật ở MVP.
3. **Không tự viết solver. Engine tính toán = phần mềm thương mại (Midas Civil ở MVP, RM Bridge ở Phase 2).**
   Phần mềm là automation + reporting layer thuần. **Không có** OpenSeesPy / Cast3M / Code_Aster / hand-rolled FEM trong bất kỳ phase nào.

Bất kỳ pull request hoặc đề xuất nào vi phạm 3 nguyên tắc trên đều được coi là out-of-scope và phải tách project riêng.

---

## Context

Phát triển phần mềm Windows desktop (UI/báo cáo tiếng Việt) để **tự động hóa pipeline phân tích động lực học cầu đường sắt tốc độ cao**. Vai trò cốt lõi:

- **Modeling nhanh** cầu khung 3D bằng cách sinh model file cho **Midas Civil** (MCT) và **RM Bridge** (TCL/cmd) — Midas trước, RM sau.
- **Khai báo nhanh** các case: modal, moving-load Eurocode HSLM/real train, velocity sweep, time-history.
- **Xếp tải trọng tàu** tự động với phân bố 3 rail pads (EN 1991-2 6.3.6.3).
- **Tự động setup** time-step (ERRI D214), damping (EN 1991-2 6.4.6.3), eigenvalue control, output extraction.
- **Đọc kết quả** Midas/RM CSV/Excel mà user export → vẽ envelope, time-history → **PDF report tiếng Việt vector**.
- User workflow: mở phần mềm → input → Generate → mở MCT/TCL trong Midas/RM → chạy → export CSV → Ingest → Report.

**Phần mềm KHÔNG có solver nội bộ**. Midas/RM là engine; phần mềm là **automation + reporting layer**.

### Tham chiếu đã đọc

| Nguồn | Vai trò |
|---|---|
| `refer\202512-23_HSR-CG Ban Tinh Tong The H7H15m.pdf` (575 trang, bản tính HSR Hồ Chí Minh - Cần Giờ, bước Thiết kế kỹ thuật) | **Cốt lõi**: liệt kê đầy đủ bộ TCVN 13594 áp dụng, các tải LM71/SW/0/SW/2/HSLM, hệ số tổ hợp ψ0/ψ1/ψ2 (TCVN 13594-3 Bảng A.1), Bảng 18 damping, mô hình 5 nhịp Main+Sub Girder cho dynamic investigation, output sheets Midas (UHRI 301_I..316_J + Bending/Shear/Torsional/Stress/Crack/Tendon) |
| `docs\[Final]Dynamic Analysis for High Speed Two (HS2).pdf` (40 trang MIDAS UK Tutorial HS2) | Mapping Eurocode → MCT directives, ERRI time-step, damping table, HSLM, acc check, flowchart NA.12, benchmark |
| `refer\KD_Railway_software\Snapshot\*.JPG` | UX inspiration (panels, train models definition, options) |
| github.com/lekhuong/KD-Railway | File format `.trmd`, `SectionData.csv`, `VelocitiesData.csv` |

### Tiêu chuẩn áp dụng (theo bản tính HSR HCM-CG)

**Việt Nam — CHÍNH** (theo TCVN 13594, dẫn xuất từ Eurocode 0/1/2/3/4 với điều chỉnh khổ 1435mm, vận tốc đến 350 km/h):

| Mã | Tên |
|---|---|
| **TCVN 13594-1:2022** | Thiết kế cầu đường sắt khổ 1435 mm, vận tốc đến 350 km/h - Phần 1: Yêu cầu chung |
| TCVN 13594-2:2022 | Phần 2 |
| **TCVN 13594-3:2022** | **Phần 3: Tải trọng và tác động** — **cốt lõi cho VBridge-Dyn** (LM71, SW/0, SW/2, HSLM-A, HSLM-B, lực kéo/hãm, ly tâm, lắc ngang, hệ số ψ, damping Bảng 18) |
| **TCVN 13594-4:2022** *(hoặc phiên bản dự án khai báo)* | **Phần 4: Phân tích và đánh giá kết cấu** — **cốt lõi** (kiểm tra điều kiện phân tích động, modal, time-history, acceleration check) |
| TCVN 13594-5:2023 | Phần 5: Kết cấu bê tông |
| TCVN 13594-6:2023 | Phần 6: Kết cấu thép |
| TCVN 13594-7:2023 | Phần 7: Kết cấu thép hợp tác BTCT |
| TCVN 13594-8:2023 | Phần 8: Gối cầu, khe co giãn, lan can |
| TCVN 13594-9:2023 | Phần 9: Đặc tả kỹ thuật và nghiệm thu |
| TCVN 13594-10:2023 | Phần 10: Cầu chịu tác động của động đất |
| TCVN 2737:2023 | Tải trọng và tác động — Tiêu chuẩn thiết kế |
| TCVN 5574:2022 | Kết cấu BT và BTCT — Tiêu chuẩn thiết kế |
| TCVN 9386:2012 | Thiết kế công trình chịu động đất |
| TCVN 10304:2015 | Móng cọc |

**Châu Âu — THAM CHIẾU KỸ THUẬT** (TCVN 13594 dẫn xuất, dùng để cross-check khi cần):

EN 1990:2002+A1:2005, EN 1991-1-1, EN 1991-1-4 (gió), EN 1991-1-5 (nhiệt), EN 1991-1-6 (thi công), EN 1991-1-7 (sự cố), **EN 1991-2:2003** (traffic), EN 1992-1-1, **EN 1992-2** (cầu BT), EN 1993-1-1, EN 1994-1-1, **EN 1994-2** (composite cầu).

### Quyết định đã chốt

| Chủ đề | Lựa chọn |
|---|---|
| Vai trò phần mềm | Pre + Post processor cho Midas Civil (MVP) + RM Bridge (Phase 2) |
| Result IO | User export CSV/Excel từ Midas/RM → phần mềm đọc |
| Input format | Excel/CSV + UI desktop song hành |
| Project workspace | Folder-based (project.yaml + workbook + outputs + storage + reports) |
| VBI | Giai đoạn 3 (modelled bên Midas/RM) |
| Storage MVP | **SQLite** (metadata/envelope/checks) + **Parquet** (time-history); DuckDB query thêm sau |
| UI | Desktop PySide6 + CLI Typer |
| Ngôn ngữ | Tiếng Việt |
| Tiêu chuẩn chính | **TCVN 13594-3:2022 + TCVN 13594-4:2023** cho HSR; TCVN 2737:2023 + TCVN 9386:2012 + TCVN 5574:2022 cho phần chung |
| Tiêu chuẩn tham chiếu | EN 1990, EN 1991-2, EN 1992-2, EN 1994-2 (cross-check khi TCVN không rõ) |
| Tải trọng đoàn tàu | **LM71 + SW/0 + SW/2 + HSLM-A1..A10 + HSLM-B + Tàu rỗng + Đoàn tàu thực** + custom (theo Bảng 15 và Bảng A.1 TCVN 13594-3:2022) |
| Tải trọng phụ | Lực kéo/hãm (QLAK, QLBK), lực ly tâm, lực lắc ngang, hiệu ứng khí động học (theo TCVN 13594-3:2022 mục 11.4.x) |
| Tổ hợp tải trọng | ULS (Cường độ), SLS (Sử dụng), Sự cố (Accidental) — hệ số ψ0, ψ1, ψ2 theo TCVN 13594-3:2022 Bảng A.1 |
| Damping | TCVN 13594-3:2022 Bảng 18 (≡ EN 1991-2 6.4.6.3 Table 6.6) |
| Acceleration limit | 3.5 m/s² ballasted; 5.0 m/s² ballastless (TCVN 13594-4:2023, ≡ EN 1990 A2.4.4.2) |
| Eurocode features kỹ thuật | Load distribution 3 rail pads + ERRI D214 dt + flowchart NA.12 (giữ vì TCVN tham chiếu trực tiếp các điều khoản này) |
| **Catalog HSLM/LM71/SW/0/SW/2/real trains** | **Mặc định EMPTY**; user import từ Excel template. Catalog dựng sẵn chỉ ship khi xác nhận license/quyền sử dụng TCVN 13594-3 & EN 1991-2. |

---

## Tên gọi & định danh

- Đề xuất: **VBridge-Dyn** — anh có thể đổi.
- Package: `vbridge_dyn`
- Folder project: bất kỳ tên, có `project.yaml` ở root.
- License: Apache-2.0.

---

## Nguyên tắc kiến trúc

Phản ánh nhận xét của anh:

1. **`core/` thật sạch** — chỉ chứa mô hình trung lập (schemas, validation, mode classifier). Không phụ thuộc Eurocode/TCVN/UIC, không phụ thuộc Midas/RM.
2. **`standards/` riêng** — tiêu chuẩn có vòng đời, version, national annex. Tách ra để dễ thêm TCVN/UIC/AREMA sau.
3. **`integrations/` cho phần mềm thương mại** — tất cả những gì coupling với Midas/RM (writer, reader, runner) gom 1 chỗ.
4. **Capability-based blocks**, không phải MCT-keyword-based. Tên module phản ánh **ý nghĩa kỹ thuật**, không phải lệnh thô — vì cú pháp MCT/TCL còn phải verify với version thật.
5. **MVP tập trung Midas**, RM giữ skeleton + schema-ready để Phase 2 chỉ cần fill in.
6. **Runner là plugin tùy chọn**, không nằm trong workflow chính. Workflow mặc định: user mở Midas/RM tay.
7. **Storage MVP tinh giản**: SQLite + Parquet thuần; DuckDB là enhancement không bắt buộc.
8. **Report chốt 1 hướng** cho MVP (đề xuất ReportLab vì kiểm soát layout + Unicode tiếng Việt tốt nhất); WeasyPrint là option v1.1.

---

## Cấu trúc package (rev3 — theo đề xuất)

```
vbridge_dyn/
├── core/                          # MÔ HÌNH TRUNG LẬP, KHÔNG PHỤ THUỘC TIÊU CHUẨN/SOLVER
│   ├── schemas/                   # pydantic models
│   │   ├── project.py
│   │   ├── bridge.py
│   │   ├── geometry.py            # Node, Element, CoordinateSystem, local axes
│   │   ├── properties.py          # Material, FrameSection, ElementRelease
│   │   ├── boundary.py            # Support, ElasticLink, RigidLink
│   │   ├── mass.py                # NodalMass, ElementMass, distributed mass spec
│   │   ├── groups.py              # StructureGroup, BoundaryGroup, LoadGroup
│   │   ├── track.py               # Track, RailLine, LoadDistribution
│   │   ├── train.py               # TrainModel, Axle, VehicleTemplate (VBI v0.4+)
│   │   ├── analysis.py            # AnalysisCase, VelocityRange, ModalOptions, THOptions
│   │   ├── result_station.py      # ResultStation: map tới node OR element OR track-station
│   │   ├── units.py               # UnitSystem: nội bộ SI, exporter đổi sang Midas/RM units
│   │   └── results.py             # ModalResult, EnvelopeRow, TimeSeriesMeta
│   ├── validation/                # validators không phụ thuộc tiêu chuẩn
│   │   ├── geometry_checks.py     # node duplicate, element zero-length, disconnected
│   │   ├── reference_checks.py    # material_id, section_id, node_id consistency
│   │   └── unit_checks.py         # unit consistency across project
│   ├── mode_classifier.py         # vertical / torsional / lateral từ mass participation
│   └── grid/
│       ├── velocity.py            # uniform grid + refine near v_res = f_n0·D/k
│       └── time.py                # T = (L_bridge + L_train) / v + tail
├── standards/                     # TIÊU CHUẨN — NAMESPACE THEO QUỐC GIA/HỆ, FLAT STRUCTURE
│   ├── vietnam/                   # TIÊU CHUẨN VIỆT NAM (CHÍNH)
│   │   ├── tcvn13594/             # bộ HSR 1435mm/350km/h (KHÔNG hard-code năm)
│   │   │   ├── dynamic_required.py     # kiểm tra điều kiện có cần phân tích động theo TCVN 13594 profile (clause map qua version_registry.py: 3:2022 Hình 31 hoặc 4 §5.1)
│   │   │   ├── train_loads.py          # LM71, SW/0, SW/2, empty train, HSLM hooks (catalog rỗng mặc định)
│   │   │   ├── hslm_rules.py           # quy tắc chọn HSLM-A vs HSLM-B theo loại kết cấu/nhịp (Bảng 15)
│   │   │   ├── speed_range.py          # Vmax_analysis = 1.2 × V_design
│   │   │   ├── damping.py              # Bảng 18 TCVN 13594-3 (≡ EN 1991-2 Table 6.6)
│   │   │   ├── acceleration.py         # 3.5 / 5.0 m/s² + comfort categories
│   │   │   ├── resonance.py            # Vcr = D·f/n cho các harmonic k=1..4
│   │   │   ├── load_actions.py         # kéo/hãm QLAK/QLBK, ly tâm, lắc ngang, khí động học (cho static cases)
│   │   │   ├── load_distribution.py    # phân bố 3 rail pads (longitudinal)
│   │   │   ├── combinations.py         # Bảng A.1 — ψ0/ψ1/ψ2 + nhóm tổ hợp 11-31, ULS/SLS/Accidental
│   │   │   └── version_registry.py     # ánh xạ năm xuất bản theo phần (3:2022, 4:2022 hoặc 2023, 5:2023, 10:2023) — đọc từ project.yaml
│   │   ├── tcvn2737/                   # Tải trọng và tác động chung
│   │   ├── tcvn5574/                   # BT/BTCT
│   │   └── tcvn9386/                   # Động đất chung
│   ├── eurocode/                  # THAM CHIẾU KỸ THUẬT (dùng cross-check khi TCVN không rõ)
│   │   ├── en1991_2/              # 6.3, 6.4 (HSLM, damping, distribution)
│   │   ├── en1990/                # A2.4.4.2 accel limit
│   │   ├── en1992_2/              # cầu BT
│   │   └── en1994_2/              # composite cầu
│   ├── international/             # ERRI/UIC chung
│   │   └── erri_d214/             # time-step formula (TCVN 13594-3 tham chiếu trực tiếp)
│   └── project_limits/            # giới hạn project-specific (override standard khi cần)
│       └── custom_limits.py
├── importers/
│   ├── excel/
│   │   ├── workbook_reader.py
│   │   ├── train_catalog_reader.py  # CHO PHÉP user import HSLM/real từ Excel để tránh license
│   │   └── templates/             # *.xlsx mẫu (có comment + validation cell)
│   │       ├── bridge_template.xlsx
│   │       ├── train_template.xlsx
│   │       └── velocity_template.xlsx
│   └── csv/
├── integrations/                  # MỌI THỨ PHỤ THUỘC PHẦN MỀM THƯƠNG MẠI
│   ├── midas/
│   │   ├── mct/
│   │   │   ├── writer.py          # orchestrate
│   │   │   ├── blocks/            # CAPABILITY-BASED, KHÔNG NAME-BY-MCT-KEYWORD
│   │   │   │   ├── geometry.py        # → *NODE, *ELEMENT
│   │   │   │   ├── properties.py      # → *MATERIAL, *SECTION, *THICKNESS
│   │   │   │   ├── boundary.py        # → *CONSTRAINT, *ELASTICLINK, *RIGIDLINK
│   │   │   │   ├── mass.py            # → *NODALMASS, *ELEMENT-MASS
│   │   │   │   ├── groups.py          # → *GROUP, *BNDR-GROUP, *LOAD-GROUP
│   │   │   │   ├── moving_load.py     # → train load function + Rail Track Analysis
│   │   │   │   ├── time_history.py    # → *TIME-HISTORY-FUNCTION/*-LOAD/*-CASE
│   │   │   │   ├── analysis_control.py # → *EIGEN-CTRL, *MODAL-DAMPING
│   │   │   │   └── result_request.py  # → *OUTPUT-CTRL, *EXPORT-RESULT
│   │   │   └── templates/         # Jinja2 header/footer/comments
│   │   ├── readers/
│   │   │   ├── modal_csv.py       # parse Midas Civil Eigenvalue Result CSV
│   │   │   ├── time_history_csv.py  # parse Time History Result CSV export
│   │   │   ├── envelope_csv.py    # parse Moving Load Envelope CSV
│   │   │   └── column_mapping.yaml  # cho phép user override khi format đổi giữa version
│   │   └── runner.py              # OPTIONAL — NGOÀI MVP. Stub không invoke gì; future v1.2+ sẽ tích hợp Civil NX/API. KHÔNG nằm trong acceptance MVP.
│   └── rm_bridge/                 # PHASE 2 — chỉ skeleton ở MVP, đủ cho schema chuẩn bị sẵn
│       ├── tcl/
│       │   ├── writer.py          # skeleton
│       │   └── blocks/            # cùng capability-based naming
│       ├── readers/
│       └── runner.py              # optional
├── postprocessor/
│   ├── envelope.py                # max/min per (train, v, station, signal)
│   ├── timeseries.py              # filter, downsample, sync
│   ├── checks.py                  # dispatch theo standards_profile → standards/<profile>/... (acc/deflection/DAF/dynamic_required)
│   └── animation.py               # animate mode shapes / deflection vs time
├── storage/
│   ├── sqlite_store.py            # metadata + envelope + checks + run history
│   ├── parquet_store.py           # time-history partitioned by (train, v, station)
│   └── (duckdb_query.py — v1.1)
├── report/
│   ├── builder.py                 # ReportLab orchestration (MVP chọn ReportLab)
│   ├── templates/                 # Jinja2 cho phần text (cover, narratives, checklist)
│   ├── plots/                     # matplotlib SVG/PDF factories
│   └── fonts/                     # Noto Sans / Times có Unicode tiếng Việt
├── services/
│   ├── project_service.py         # CRUD project folder, validate
│   ├── generate_service.py        # orchestrate: schema → MCT files (per target)
│   ├── ingest_service.py          # import CSV → SQLite + Parquet
│   ├── analyze_service.py         # envelope + checks
│   └── report_service.py          # build PDF
├── ui/                            # PySide6
│   ├── main_window.py
│   ├── panels/                    # (xem wireframe phía dưới)
│   ├── dialogs/
│   ├── widgets/
│   └── resources/
├── cli/                           # Typer
│   └── commands/
└── tests/
    ├── unit/                      # schemas, eurocode formulas, file parsers
    ├── integration/               # generate → ingest cycle với sample MCT
    └── benchmarks/                # HS2 + KD-Railway compare
```

---

## Data model (bổ sung theo nhận xét anh)

```python
# core/schemas/units.py
class UnitSystem(BaseModel):
    """Internal là SI. Exporter chịu trách nhiệm convert sang đơn vị target."""
    length: Literal["m"] = "m"
    force: Literal["N"] = "N"
    mass: Literal["kg"] = "kg"
    time: Literal["s"] = "s"
    # exporter target units khai báo trong project.yaml targets.* section

# core/schemas/geometry.py
class CoordinateSystem(BaseModel):
    id: str
    origin: tuple[float, float, float]
    x_axis: tuple[float, float, float]  # unit vector
    y_axis: tuple[float, float, float]

class Node(BaseModel):
    id: int
    x: float; y: float; z: float
    csys_id: str = "global"

class Element(BaseModel):
    id: int
    type: Literal["BEAM", "TRUSS"]
    n1: int; n2: int
    material_id: str
    section_id: str
    structure_group: str = ""
    local_axis_csys_id: str | None = None  # override default beam local axis

# core/schemas/properties.py
class ElementRelease(BaseModel):
    """Release at start/end of beam element (Mz=0 for moment hinge, etc.)."""
    element_id: int
    end: Literal["i", "j"]
    dofs: list[Literal["Fx","Fy","Fz","Mx","My","Mz"]]

# core/schemas/boundary.py
class Support(BaseModel):
    node_id: int
    constraint: list[int]  # [Ux,Uy,Uz,Rx,Ry,Rz]
    boundary_group: str = ""

class ElasticLink(BaseModel):
    """Đàn hồi node-to-node với 6 DOF stiffness (gối cầu, isolator)."""
    id: int
    n1: int; n2: int
    kx: float; ky: float; kz: float
    krx: float; kry: float; krz: float
    boundary_group: str = ""

class RigidLink(BaseModel):
    """Master-slave rigid (rigid arm, deck-to-girder offset)."""
    id: int
    master: int
    slaves: list[int]
    boundary_group: str = ""

# core/schemas/mass.py
class NodalMass(BaseModel):
    node_id: int
    m: float
    Ixx: float = 0; Iyy: float = 0; Izz: float = 0

class ElementDistributedMass(BaseModel):
    """Khối lượng ballast/rail/sleeper áp lên một set element (theo group)."""
    target_group: str
    mass_per_length: float  # kg/m
    note: str = ""          # vd "ballast 0.3m saturated"

# core/schemas/groups.py
class StructureGroup(BaseModel):
    id: str; name: str
    element_ids: list[int] = []
    node_ids: list[int] = []

class BoundaryGroup(BaseModel):
    id: str; name: str

class LoadGroup(BaseModel):
    id: str; name: str

# core/schemas/result_station.py
class ResultStation(BaseModel):
    """Vị trí xuất kết quả. Map tới NODE, ELEMENT (mid-span), hoặc TRACK station."""
    id: str
    name: str
    target: Literal["node", "element", "track"]
    node_id: int | None = None
    element_id: int | None = None
    element_eta: float | None = None      # 0..1 nội suy dọc element
    track_id: str | None = None
    track_x: float | None = None          # station theo chiều dài track

# core/schemas/bridge.py
class Bridge(BaseModel):
    units: UnitSystem = UnitSystem()
    coordinate_systems: list[CoordinateSystem] = []
    nodes: list[Node]
    elements: list[Element]
    materials: list[Material]
    sections: list[FrameSection]
    element_releases: list[ElementRelease] = []
    supports: list[Support]
    elastic_links: list[ElasticLink] = []
    rigid_links: list[RigidLink] = []
    nodal_masses: list[NodalMass] = []
    distributed_masses: list[ElementDistributedMass] = []  # KHÔNG còn distributed_mass_extra float
    structure_groups: list[StructureGroup] = []
    boundary_groups: list[BoundaryGroup] = []
    load_groups: list[LoadGroup] = []
```

`distributed_mass_extra: float` cũ đã được thay bằng `distributed_masses: list[ElementDistributedMass]` — ballast/rail/sleeper áp theo group thật, không phải hằng toàn cầu.

---

## project.yaml — target-specific config

```yaml
meta:
  name: "HSR HCM - Cần Giờ Nhịp Điển Hình"
  author: "Vũ"
  created_at: 2026-05-29
  schema_version: "1.0"
  locale: vi-VN

# Profile tiêu chuẩn áp dụng cho project — KHÔNG hard-code trong source
standards_profile: vietnam_tcvn13594
tcvn13594_versions:                # cấu hình theo project, không gắn cứng trong source
  part_3: "2022"                   # TCVN 13594-3:2022 — Tải trọng và tác động
  part_4: "2022"                   # TCVN 13594-4:2022 — Phân tích và đánh giá kết cấu (override "2023" nếu dự án dùng bản mới)
  part_5: "2023"
  part_10: "2023"

design:
  design_speed_kmh: 350
  max_analysis_speed_factor: 1.2   # → V_max_analysis = 420 km/h
  track_type: ballastless          # ballasted | ballastless
  track_gauge_mm: 1435

dynamic:
  check_required_method: tcvn13594_dynamic_required  # neutral key — `version_registry.py` ánh xạ sang clause (3:2022 Hình 31 hoặc 4 §5.1 tùy phiên bản dự án)
  damping_method: tcvn13594_3_table_18               # → standards/vietnam/tcvn13594/damping.py
  resonance_check: true                              # tính Vcr = D·f/n cho k=1..4 và refine velocity grid quanh Vcr
  time_step_method: erri_d214

bridge:
  workbook: bridge.xlsx
  sheets:
    nodes: Nodes
    elements: Elements
    materials: Materials
    sections: Sections
    element_releases: Releases
    supports: Supports
    elastic_links: ElasticLinks
    rigid_links: RigidLinks
    nodal_masses: NodalMasses
    distributed_masses: DistributedMasses
    structure_groups: StructureGroups
    boundary_groups: BoundaryGroups
    load_groups: LoadGroups
    coordinate_systems: CSys
    tracks: Tracks

trains:
  catalogs:
    - trains/hslm_catalog.xlsx         # HSLM-A/B (data theo standards_profile — TCVN hoặc EN)
    - trains/static_train_loads.xlsx   # LM71, SW/0, SW/2 (data theo standards_profile)
    - trains/real_trains.xlsx          # đoàn tàu thực (Thalys, ICE, EMU...)
    - trains/custom_train_A.xlsx
  selected:
    static_models:                     # cho check tổ hợp ψ
      - LM71
      - SW/0
    hslm: [A1, A2, A3, A4, A5, A6, A7, A8, A9, A10]
    real: [Thalys-Single, Thalys-Double, EMU-VN]
    custom: [Custom-001]
    empty_train: true                  # tàu rỗng cho check ổn định ngang

velocity_range:
  v_min_kmh: 140
  v_max_kmh: 420                       # = 1.2 × 350 km/h (v_design HSR HCM-CG)
  v_line_design_kmh: 350
  step_kmh: 5
  refine_near_resonance: true

analysis:
  n_modes: 30
  fmax_target: auto                    # auto = max(30 Hz, 1.5·n0, n3)
  damping:
    standard: tcvn_13594_3_bang_18     # ≡ EN 1991-2 6.4.6.3 Table 6.6
    bridge_type: prestressed_concrete  # cầu BTCT DƯL
  time_step:
    standard: erri_d214
  integration: modal_superposition

combinations:
  standard: tcvn_13594_3_bang_a1
  cases:
    - { id: ULS, kind: ultimate, family: "11+13" }       # LM71+SW/0 dọc max + kéo/hãm
    - { id: ULS_HSLM, kind: ultimate, family: "HSLM" }
    - { id: SLS, kind: serviceability, family: "11+15" } # ổn định ngang tàu rỗng
    - { id: ACC_NoEarthquake, kind: accidental, family: "derailment" }

result_stations:
  - { id: S1, target: track, track_id: T1, track_x: 10.0, name: "1/4 nhịp 1" }
  - { id: S2, target: track, track_id: T1, track_x: 17.5, name: "giữa nhịp 1" }
  - { id: S3, target: node, node_id: 105, name: "gối trung gian" }

targets:
  midas_civil:
    enabled: true
    midas_version: "2022"                # mặc định MVP — reverse-engineer MCT từ Midas Civil 2022
    units: { force: kN, length: m, mass: ton, time: s }
    export_mode: mct
    case_split: grouped_by_train    # default — gộp các vận tốc cùng train vào 1 file (giảm số file MCT)
                                    # options: one_file_per_case (chỉ dùng debug), single_file (tất cả vào 1)
    output_dir: generated/midas
    moving_load_strategy: time_history_function   # default — explicit TIME-HISTORY-FUNCTION per axle
                                                  # experimental: rail_track_analysis (cần verify cú pháp/ý nghĩa MIDAS phiên bản dùng)
  rm_bridge:
    enabled: false                  # bật khi vào Phase 2
    rm_version: "12.x"
    units: { force: kN, length: m, mass: ton, time: s }
    export_mode: tcl
    output_dir: generated/rm_bridge
    rolling_stock_module: standard

checks:
  standards:
    - tcvn_13594_4_dynamic_check       # 5.1 kiểm tra cần phân tích động
    - tcvn_13594_4_acceleration_limit  # 3.5/5.0 m/s²
    - tcvn_13594_4_deflection_limit
    - tcvn_13594_4_daf
  cross_check:                         # tham chiếu thêm khi cần
    - en1990_a2_4_4_2
  custom_limits: project_limits/extra.yaml   # tùy chọn

report:
  template: full_report
  language: vi-VN
  engine: reportlab               # MVP; weasyprint v1.1
  output: reports/{date}_full_report.pdf
```

---

## Folder workspace

```
my_bridge_project/
├── project.yaml
├── bridge.xlsx
├── trains/
│   ├── hslm_catalog.xlsx           # user-imported HSLM (data fill theo standards_profile)
│   ├── static_train_loads.xlsx     # LM71, SW/0, SW/2
│   ├── real_trains.xlsx
│   ├── custom_train_A.xlsx
│   └── velocity_sets.csv
├── generated/
│   ├── midas/                      # MVP target — Midas Civil 2022
│   │   ├── case_modal.mct
│   │   ├── case_th_hslm_a1.mct     # grouped_by_train: 1 file/train, nhiều *TIME-HISTORY-CASE bên trong
│   │   ├── case_th_hslm_a2.mct
│   │   ├── case_th_thalys_single.mct
│   │   ├── ...
│   │   ├── generation_manifest.json    # map: train, velocity_kmh, case_name, expected_csv_name, result_stations, node/element IDs
│   │   ├── export_instructions.md      # hướng dẫn user tay: mở MCT → Run → Export bảng nào → đặt CSV vào đâu
│   │   └── result_export_template.xlsx # template Excel cho user paste/CSV ingest đồng nhất
│   └── rm_bridge/                  # Phase 2
├── solver_outputs/
│   ├── midas/                      # user paste CSV export ở đây
│   └── rm_bridge/
├── storage/
│   ├── meta.sqlite                 # envelope + checks + run history
│   └── timeseries.parquet/         # partition by (train, v, station)
├── figures/                        # vector plots SVG/PDF
└── reports/
    └── 2026-05-29_full_report.pdf
```

---

## Pipeline workflow (user perspective)

```
[1] vbdyn init my_bridge_project       # tạo folder + project.yaml + bridge.xlsx template
[2] Mở bridge.xlsx → nhập nodes/elements/sections/.../groups → save.
    (Hoặc dùng UI tables; save Excel ra.)
[3] Import train catalogs (HSLM/real/static từ Excel theo standards_profile — đảm bảo quyền sử dụng catalog).
    Chọn trains + velocity range + analysis case trong UI/YAML.
[4] vbdyn validate                     # check geometry/references/units
[5] vbdyn generate --target midas      # sinh .mct + generation_manifest.json + export_instructions.md
                                       # + result_export_template.xlsx vào generated/midas/
[6] Mở .mct trong Midas Civil 2022 → Run → Export Time History + Eigenvalue Result theo
    export_instructions.md. Paste CSV vào solver_outputs/midas/ với tên match
    generation_manifest.json (HOẶC dùng result_export_template.xlsx để chuẩn hóa).
[7] vbdyn ingest --target midas        # đọc generation_manifest.json để map case → CSV →
                                       # parse → SQLite (meta+envelope) + Parquet (TH)
[8] vbdyn envelope                     # extract envelope + chạy postprocessor/checks
                                       # (dispatch theo standards_profile, default TCVN 13594)
[9] vbdyn report --pdf reports/...     # PDF tiếng Việt 13 mục
```

---

## Capability-based blocks (MCT — verify khi implement)

Block module dùng tên capability, ánh xạ động sang MCT directive thật:

| Block | MCT directive(s) (cần verify với Midas version) |
|---|---|
| `geometry.py` | `*NODE`, `*ELEMENT` |
| `properties.py` | `*MATERIAL`, `*SECTION`, `*THICKNESS` |
| `boundary.py` | `*CONSTRAINT`, `*ELASTICLINK`, `*RIGIDLINK` (kiểm tra cú pháp) |
| `mass.py` | `*NODALMASS`, `*ELEMENT-MASS` |
| `groups.py` | `*GROUP`, `*BNDR-GROUP`, `*LOAD-GROUP` |
| `moving_load.py` | `*RAIL-TRACK-ANALYSIS-MODEL` (nếu bật) hoặc kết hợp `*TIME-HISTORY-FUNCTION` từng axle |
| `time_history.py` | `*TIME-HISTORY-FUNCTION`, `*TIME-HISTORY-LOAD`, `*TIME-HISTORY-CASE` |
| `analysis_control.py` | `*EIGEN-CTRL`, `*MODAL-DAMPING` |
| `result_request.py` | `*OUTPUT-CTRL`, `*EXPORT-RESULT` |

**Quy ước**: mỗi block class có `def render(ctx) -> str`, nhận `RenderContext` chứa Project + UnitConverter + naming registry (đảm bảo node_id không trùng group_id, v.v.). Writer chính gọi từng block theo thứ tự yêu cầu của Midas.

**Cú pháp MCT cụ thể**: verify bằng cách export 1 model nhỏ trực tiếp từ Midas Civil → đọc lại MCT → reverse-engineer block format. Đây là việc làm ngay đầu v0.1.

---

## MIDAS CSV reader

Mỗi reader theo format export chuẩn của Midas Civil (Time History Result, Eigenvalue Result, Moving Load Envelope). Cấu hình `column_mapping.yaml` cho phép user override:

```yaml
# integrations/midas/readers/column_mapping.yaml
midas_version: "2022"               # mặc định MVP; override khi project khác phiên bản
time_history:
  time_column: "Time(sec)"
  node_disp_pattern: "N{node_id}_DZ"       # regex để identify
  node_accel_pattern: "N{node_id}_AZ"
  element_moment_pattern: "E{elem_id}_MY"
  element_shear_pattern: "E{elem_id}_FZ"
modal:
  mode_column: "Mode"
  freq_column: "Frequency(Hz)"
  participation_columns: ["MX(%)", "MY(%)", "MZ(%)", "RX(%)", "RY(%)", "RZ(%)"]
```

Khi Midas đổi format ở version khác, user chỉ cần chỉnh `column_mapping.yaml`, không phải sửa code.

---

## Storage (MVP — tinh giản)

**SQLite** (`storage/meta.sqlite`):
```sql
-- envelope per (train, v, station, signal)
CREATE TABLE envelope (
    train_id TEXT, v_kmh REAL, station_id TEXT, signal TEXT,
    max_value REAL, min_value REAL, t_max REAL, t_min REAL,
    UNIQUE(train_id, v_kmh, station_id, signal)
);

-- modal results
CREATE TABLE modal (
    target TEXT, mode INTEGER, freq_hz REAL, period_s REAL,
    type TEXT, mx REAL, my REAL, mz REAL, rx REAL, ry REAL, rz REAL
);

-- checks results
CREATE TABLE checks (
    standard TEXT, criterion TEXT, station_id TEXT, train_id TEXT,
    v_kmh REAL, value REAL, limit_value REAL, pass INTEGER
);

-- run history
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY, target TEXT, started_at TEXT,
    finished_at TEXT, status TEXT, notes TEXT
);
```

**Parquet** (`storage/timeseries.parquet/`):
- Partition by `train`, `v_kmh`, `station_id`
- Schema: `time (float32), uz (float32), az (float32), my (float32), fz (float32)`
- Compression: snappy (default) hoặc gzip
- Đọc bằng `pyarrow.parquet.read_table(...)`

**DuckDB query layer**: hoãn sang v1.1. MVP đọc bằng pandas đơn thuần.

---

## Report (MVP — chọn ReportLab)

Lý do: kiểm soát layout chính xác, embed PDF từ matplotlib trực tiếp qua `Image` hoặc `Drawing`, Unicode tiếng Việt qua `pdfmetrics.registerFont(TTFont("NotoSans", "fonts/NotoSans-Regular.ttf"))` ổn định, không phụ thuộc browser engine (WeasyPrint cần Chromium-class renderer).

WeasyPrint (HTML→PDF) cân nhắc lại ở v1.1 nếu yêu cầu CSS styling phức tạp hơn.

13 mục report (cấu trúc phản ánh layout bản tính HSR HCM-CG):

1. Bìa (logo + tên dự án + ngày + author + version + standards_profile)
2. Mục lục (auto bookmarks)
3. Tóm tắt input (meta + bridge isometric + bảng materials/sections + Main Girder vs Sub Girder element ranges)
4. Tải trọng đoàn tàu (axle diagrams vector cho LM71, SW/0, SW/2, HSLM-A1..A10, real, custom)
5. Cấu hình phân tích:
   - Damping ξ% theo TCVN 13594-3 Bảng 18 (kèm công thức rút ra cho kiểu cầu + L)
   - dt theo ERRI D214 (in đủ 4 candidate, dt = min)
   - n_modes, fmax target
   - **Bảng Vmin / Vtk / Vmax = 1.2·Vtk** (km/h và m/s)
6. **Kiểm tra điều kiện có cần phân tích động** — TCVN 13594-4 §5.1 flowchart, kết luận YES/NO
7. Kết quả modal:
   - Bảng đầy đủ N modes (freq, period, mass participation, classification vert/torsion/lateral)
   - **Tần số uốn đầu tiên f_bending (Hz)** — highlight
   - **Tần số xoắn đầu tiên f_torsion (Hz)** — highlight
   - Mode shape vector plots: 1 mode uốn + 1 mode xoắn minh họa
8. **Vận tốc nguy hiểm cộng hưởng**:
   - Bảng Vcr = D·f_n / k cho k=1..4 theo từng đoàn tàu (D đặc trưng axle spacing repeat)
   - Highlight Vcr nào rơi trong [Vmin, Vmax]
9. Envelope vs Speed (chart per signal × station):
   - Chuyển vị max/min theo vận tốc
   - Gia tốc max/min theo vận tốc — kèm đường giới hạn 3.5 / 5.0 m/s² (theo `track_type`)
   - Nội lực max/min theo vận tốc
   - **Biểu đồ xu hướng gia tốc theo vận tốc** (highlight cell vượt ngưỡng)
10. Phản ứng tại các vận tốc đặc biệt:
    - **Tại Vtk** (vd 350 km/h): bảng + chart chuyển vị + gia tốc
    - **Tại Vmax** (vd 420 km/h): bảng + chart
    - Tại Vcr (vận tốc nguy hiểm): bảng + chart
11. Time history (compare theo train + theo velocity tại các station đã chọn)
12. **Kết luận**:
    - Kiểm tra TCVN 13594-4 acceleration limit → ĐẠT / KHÔNG ĐẠT
    - Kiểm tra deflection limit → ĐẠT / KHÔNG ĐẠT
    - Kiểm tra DAF → ĐẠT / KHÔNG ĐẠT
    - Kết luận tổng thể: có vận tốc giới hạn nào cần đặt cho khai thác không
13. Phụ lục (project.yaml dump + paths + versions Midas/RM/VBridge-Dyn + tcvn13594_versions đã dùng)

---

## UI desktop (PySide6) — wireframe (rút gọn)

```
+==============================================================================+
|  VBridge-Dyn 1.0                                              -  []  X       |
|  Project  Bridge  Trains  Cases  Generate  Ingest  Analyze  Report  Help     |
+------------------------------------------------------------------------------+
| [New][Open][Save]  |  Target: (•) Midas Civil  ( ) RM Bridge (Phase 2)       |
|                    |  [Generate ▾] [Open in Midas] [Ingest CSV] [Report]     |
+--------------------+-----------------------------+----------------------------+
| PROJECT TREE       |  CENTER (tabs)              | OPTIONS                    |
|                    |                              |                            |
| my_bridge_project/ |  [Bridge][Tracks][Loads]    | fmax (Hz)   [auto]         |
|  ├ project.yaml    |  [Cases][Generate][Results] |   = max(30, 1.5·n0, n3)    |
|  ├ bridge.xlsx     |  [Report]                   |                            |
|  ├ trains/         |                              | Damping  [standards_profile]
|  ├ generated/      |  ┌── Bridge tab ──────────┐ |  vd: tcvn13594_3_table_18 |
|                    |                              |  type: PSC, L=35m         |
|  ├ solver_outputs/ |  │ Nodes / Elements /      │ |  ξ = 1.27% (computed)     |
|  ├ storage/        |  │ Materials / Sections /  │ |                            |
|  ├ figures/        |  │ Releases / Supports /   │ | dt (s)  [ERRI D214]       |
|  └ reports/        |  │ ElasticLinks / RigidLk /│ |   = 1.25 ms (computed)    |
|                    |  │ NodalMasses / Distrib / │ |                            |
| [Refresh]          |  │ StructureGroups / ... / │ | Result Stations           |
|                    |  │ CSys / Tracks tables    │ |  S1 (track T1, x=10.0)    |
|                    |  │ [Open Excel][Reload]    │ |  S2 (track T1, x=17.5)    |
|                    |  │ [Validate]              │ |  S3 (node 105)            |
|                    |  │ Status: ✓ no errors     │ | [Edit...]                 |
|                    |  └──────────────────────────┘ |                            |
|                    |  3D Preview (pyvista)        | Velocity (km/h)           |
|                    |  [Reset View][Animate Mode▾] |  Min  [140] Max [420]     |
|                    |                              |  Step [5]                 |
|                    |                              |  [✓] refine v_res         |
+--------------------+------------------------------+----------------------------+
| LOAD MODELS                                                                    |
| HSLM: [Import Excel...] (catalog rỗng mặc định vì lý do bản quyền)             |
|       [✓]A1 [_]A2 [_]A3 ... (sau khi import)                                   |
| Real: [Import Excel...] [✓]Thalys-Single [_]Thalys-Double                      |
| Custom: [Train Models Definition...] (CRUD dialog)                              |
+----------------------------------------------------------------------------+---+
| OUTPUTS                                                                    |   |
| [✓] Envelope Disp [✓] Envelope Accel [✓] Env. Bending [✓] Env. Shear      |   |
| [✓] TH per Train  [✓] TH per Velocity  [✓] DAF [✓] Acc check  [✓] Report  |   |
+----------------------------------------------------------------------------+---+
| Status: Generated 11 .mct files / 510 cases (grouped_by_train) + manifest. Mở Midas Civil 2022 để chạy. |
+==============================================================================+
```

---

## Lộ trình MVP (đã chuyển RM về Phase 2)

| Version | Tuần | Deliverables | Acceptance |
|---|---|---|---|
| **v0.1 — Foundation** | 1-3 | Repo + CI, `core/schemas/*` đầy đủ (bao gồm release/link/mass/group/station/units, Main+Sub girder distinction), `core/validation/*`, project.yaml IO, Excel template + reader (`importers/excel`), reverse-engineer 1 file MCT từ Midas thật để hiệu chuẩn block syntax, schema cho LoadCombination (ψ0/ψ1/ψ2) | `vbdyn init` + `vbdyn validate` chạy được; load Excel ra `Project` model không lỗi; sample MCT minh họa được parse bằng tay đối chiếu |
| **v0.2 — Midas MCT skeleton** | 4-6 | `integrations/midas/mct/{writer,blocks/*}` cho geometry + properties + boundary + mass + groups + analysis_control; sinh được `case_modal.mct` mở được trong Midas; **standards TCVN 13594-3 (LM71, SW/0, HSLM, damping Bảng 18, ψ Bảng A.1) + dynamic_required + ERRI dt**; cross-check Eurocode | (Cứng) V01-V03 + parity tests V06-V07 pass. (Mềm) Sinh MCT modal cho **HSR HCM-CG nhịp điển hình** (Main+Sub girder), Midas chạy không lỗi syntax, eigenvalue mode đầu cùng order-of-magnitude với bản tính PDF (~5.9 Hz). Không đặt tolerance cứng vì chưa có file model gốc. |
| **v0.3 — Moving load + ingest** | 7-10 | MCT moving_load (strategy: time_history_function default, rail_track_analysis experimental) + time_history + result_request (cho cả LM71 và HSLM); `integrations/midas/readers/*` (modal_csv, time_history_csv); storage SQLite + Parquet; CLI `generate`/`ingest`/`envelope`; `postprocessor/envelope` + `postprocessor/checks` (dispatch theo standards_profile) | (Cứng) V01-V03 envelope khớp analytical/Frýba. (Mềm) Reproduce **xu hướng** envelope HSR HCM-CG/HS2/KD-Railway: peak velocity location + critical speed approximate, report layout + postprocess logic đúng. Tolerance cụ thể chỉ áp dụng khi có file model gốc. |
| **v0.4 — UI + Report v1** | 11-14 | PySide6 UI (panels Bridge/Tracks/Loads/Cases/Generate/Results/Report); Train Models Definition dialog (LM71/SW/0/SW/2/HSLM/real/custom); ReportLab **PDF 13 mục** tiếng Việt; mode classifier; **TCVN 13594 checks**: DAF + acc check + dynamic_required + Vcr resonance | End-to-end UI workflow ra PDF cho HSR HCM-CG case; PDF mở trong Adobe Reader đúng font tiếng Việt, vector zoom rõ, đầy đủ 13 mục với f_bending/f_torsion/Vcr highlight, dẫn chứng điều khoản TCVN qua `version_registry`. |
| **v0.5 — RM Bridge skeleton** | 15-17 | `integrations/rm_bridge/tcl/{writer,blocks/*}` capability-based; reverse-engineer TCL từ sample RM file; reader skeleton | Sinh được TCL modal-only cho cầu nhỏ, RM Bridge chạy không lỗi syntax |
| **v0.6 — RM Bridge full** | 18-21 | RM TCL moving load + Rolling Stock module + time history; RM CSV reader; dashboard so sánh Midas vs RM | RM cho ra eigenvalue ±2% so với Midas trên cùng project |
| **v0.7 — VBI** | 22-25 | Vehicle template Excel (mass-spring-damper xe), track irregularity Excel, sinh MCT/TCL với train interaction module, DAF VBI vs moving-load | VBI HSLM-A1 @ 220 km/h khớp VBI paper reference ±10% |
| **v1.0 — Polish + installer** | 26-28 | PyInstaller MSI Windows, user manual PDF tiếng Việt, refine resonance auto, sensitivity study (damping ±20%, mass ±5%), regression test suite V01-V09 (V09 weekly on-demand vì cần Midas) | Installer cài trên máy sạch chạy được full workflow; HSR HCM-CG case end-to-end ra PDF hoàn chỉnh |
| **v1.1+** | — | DuckDB query layer, WeasyPrint engine option, MP4 animation export, multi-project compare | — |
| **v1.2+** | — | **Future MIDAS API / Civil NX integration** (headless run, kết quả binary đọc trực tiếp), cầu cable-stayed/treo, gió ngang EN 1991-1-4 Annex B, optimization "worst velocity finder" | — |

---

## Verification & Validation

Phân thành **2 nhóm rõ ràng** (theo quyết định rev7 + review P2):

### Hard benchmarks (có analytical/parity rõ — tolerance cứng, CI gate)

| ID | Case | Reference | Tolerance |
|---|---|---|---|
| V01 | Simple beam static point load | `δ = PL³/48EI` analytical | ±0.5% |
| V02 | Simple beam single moving load | Frýba 1972 analytical | ±2% |
| V06 | TCVN damping vs EN damping cross-check | parity (Bảng 18 TCVN 13594-3 ≡ Table 6.6 EN 1991-2) | exact |
| V07 | TCVN ψ factors vs EN ψ factors | parity (Bảng A.1 vs EN 1990 A2.4) | exact |
| V08 | MCT vs TCL parity (Phase 2 RM Bridge) | cùng project, 2 targets | ±2% |
| V10 | VBI HSLM-A1 @ 220 km/h (Phase 3) | Yang/Zhang VBI paper | ±10% |

### Reference comparisons (soft — chỉ kiểm tra xu hướng + order-of-magnitude)

Chỉ chuyển sang tolerance cứng khi có **file model gốc** của reference trong
repo. Đến lúc đó V03-V05/V09 sẽ được nâng cấp lên Hard benchmarks.

| ID | Case | Reference | Soft acceptance |
|---|---|---|---|
| V03 | KD-Railway Chapter6_Example | KD-Railway output CSV (chưa có file model) | Xu hướng peak velocity + critical speed approximate + report layout đúng |
| V04 | HS2 case eigenvalues (concrete C45) | docs HS2 PDF p.30 (chỉ PDF, không có file model) | f_1 cùng order (~6 Hz), N modes đầu cùng chiều biến |
| V05 | HS2 envelope HSLM-A1..A10 | docs HS2 PDF p.36 (chỉ PDF) | Peak velocity ≈ ±20 km/h; accel trend qualitative giống |
| **V09** | **HSR HCM-CG typical span** | `refer/202512-23_HSR-CG Ban Tinh Tong The H7H15m.pdf` (Midas Civil 2025, HSLM-A, ξ=1%, dt=0.001 s, Vtk=350 km/h, Vmax=420 km/h, **f_bending ≈ 5.9312 Hz**, **f_torsion ≈ 16.35 Hz**, **Vcr ≈ 384.34 km/h**) | f_bending cùng order (~6 Hz), f_torsion cùng order (~16 Hz), Vcr ±20 km/h, report layout đầy đủ 13 mục |

### CI chính sách

- **Mỗi PR (< 5 min)**: chạy V01-V02 (analytical) + V06-V07 (standards parity).
- **Weekly / on-demand**: chạy V03-V05 + V09 (reference comparisons — cần
  Midas hoặc reference data).
- **Phase 2 / Phase 3 mới chạy**: V08 (RM Bridge parity), V10 (VBI paper).

---

## Mapping Standard → module

Năm xuất bản KHÔNG hard-code; đọc từ `project.yaml > tcvn13594_versions`.

| TCVN (CHÍNH) | EN tương ứng (THAM CHIẾU) | Module trong `standards/` | Function |
|---|---|---|---|
| TCVN 13594-3 Điều 11.4.3.1 (LM71) | EN 1991-2 6.3.2 | `vietnam/tcvn13594/train_loads.py` | `build_lm71(alpha)` |
| TCVN 13594-3 Điều 11.4.3.2 (SW/0) | EN 1991-2 6.3.3 | `vietnam/tcvn13594/train_loads.py` | `build_sw0()` |
| TCVN 13594-3 Điều 11.4.3.3 (SW/2) | EN 1991-2 6.3.3 | `vietnam/tcvn13594/train_loads.py` | `build_sw2()` |
| TCVN 13594-3 Bảng 15 (HSLM-A/B) | EN 1991-2 6.4.6.1.1 + Annex E | `vietnam/tcvn13594/hslm_rules.py` | `choose_hslm_set(L, structure)`, `build_hslm_a(variant)`, `build_hslm_b(L)` |
| TCVN 13594-3 Bảng 18 (damping) | EN 1991-2 6.4.6.3 Table 6.6 | `vietnam/tcvn13594/damping.py` | `damping_zeta(bridge_type, L)` |
| TCVN 13594-3 Mục 11.4.5.x (ly tâm, lắc ngang, kéo/hãm) | EN 1991-2 6.5.x | `vietnam/tcvn13594/load_actions.py` | `centrifugal(...)`, `nosing(...)`, `traction(L)`, `braking(L)` |
| TCVN 13594-3 Mục 11.6.6 (khí động học) | EN 1991-2 6.6 | `vietnam/tcvn13594/load_actions.py` | `aerodynamic_pressure(V)` |
| TCVN 13594-3 Bảng A.1 (hệ số ψ) | EN 1990 A2.4 | `vietnam/tcvn13594/combinations.py` | `psi(load_kind, ψ_index)`, build_group(11..31) |
| TCVN 13594-3 phân bố qua 3 rail pads | EN 1991-2 6.3.6.3 | `vietnam/tcvn13594/load_distribution.py` | `distribute_axle_3pads(...)` |
| TCVN 13594-3 v_max_analysis = 1.2·v_design | EN 1991-2 6.4.6.2 | `vietnam/tcvn13594/speed_range.py` | `build_velocity_grid(v_design)` |
| TCVN 13594-3 Vcr cộng hưởng | EN 1991-2 6.4.6.1.1 (eq 6.9) | `vietnam/tcvn13594/resonance.py` | `critical_speeds(f_n, D, k_max=4)` |
| TCVN 13594-4 §5.1 (kiểm tra cần phân tích động) | BS EN 1991-2 Figure NA.12 | `vietnam/tcvn13594/dynamic_required.py` | `is_dynamic_required(v, L, n0, ...)` |
| TCVN 13594-4 (acc limit + comfort) | EN 1990 A2.4.4.2 | `vietnam/tcvn13594/acceleration.py` | `check_acc(envelope, track)`, `comfort_category(...)` |
| TCVN 13594-4 (deflection) | EN 1990 A2.4.4 | `vietnam/tcvn13594/acceleration.py` (cùng module checks) hoặc `deflection.py` | `check_deflection(...)` |
| ERRI D214 1999 (time step) | EN 1991-2 Annex E | `international/erri_d214/time_step.py` | `erri_d214_dt(fmax, l_min, v_max, n_modes)` |

**Quy ước**: code mặc định gọi `standards/vietnam/tcvn13594/...` khi `project.yaml > standards_profile: vietnam_tcvn13594`. Khi cấu hình `eurocode_pure` thì gọi `standards/eurocode/...` thay thế. Cùng API signature giữa 2 namespace để swap dễ.

---

## Rủi ro & Trade-offs

1. **Số file MCT lớn**: 50 velocities × 10 trains = 500 cases. Default `case_split: grouped_by_train` → ~10-11 file MCT (mỗi file 1 train, nhiều `*TIME-HISTORY-CASE` bên trong). User mở từng file/Run/Export — cần `generation_manifest.json` để map case → CSV.
2. **Format CSV Midas đổi giữa version**: mặc định `midas_version: "2022"`. `column_mapping.yaml` cho phép user override khi project sang version khác (2023/2024/NX).
3. **MCT syntax phải verify thật**: bắt buộc v0.1 export 1 model từ **Midas Civil 2022** (không phải 2024/NX) → reverse-engineer block format trước khi viết writer. Không deadline-cứng block names khi chưa có sample.
4. **VBI bên Midas/RM**: Midas có "Rail-Bridge Interaction", RM có "Rolling Stock". v0.7 cần sample file đầu vào — đề xuất anh chuẩn bị 1 file mẫu cho v0.7.
5. **Headless run Midas**: NGOÀI MVP. v1.2+ mới xét tích hợp Civil NX/API. MVP user chạy thủ công theo `export_instructions.md`.
6. **Vietnamese PDF**: bắt buộc CI test glyph (ă, â, ê, ơ, ư, đ, ...).
7. **Bản quyền EN 1991-2 HSLM/real trains catalog**: ship rỗng; user import Excel; cung cấp template format chuẩn. Tránh distribute dữ liệu bản quyền EN.
8. **License stack**: BSD/MIT/LGPL/Apache → đóng gói thương mại được.
9. **User error Excel input**: validation ngay khi load (pydantic + cell highlight), summary errors trong UI.
10. **RM Bridge TCL sample**: chưa có sample chuẩn → đề nghị anh cung cấp 1 file mẫu cho v0.5.

---

## Critical files (sẽ tạo khi implement)

- `pyproject.toml`, `uv.lock`
- `src/vbridge_dyn/core/schemas/project.py`
- `src/vbridge_dyn/core/schemas/bridge.py` (đã có release/link/mass/group/station)
- `src/vbridge_dyn/core/schemas/units.py`
- `src/vbridge_dyn/core/schemas/result_station.py`
- `src/vbridge_dyn/standards/vietnam/tcvn13594/dynamic_required.py` (§5.1 ≡ Figure NA.12)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/train_loads.py` (LM71, SW/0, SW/2, empty, HSLM hooks)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/hslm_rules.py` (chọn HSLM-A/B theo nhịp/kết cấu)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/speed_range.py` (Vmax = 1.2·Vtk)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/damping.py` (Bảng 18)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/acceleration.py` (3.5/5.0 m/s² + comfort)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/resonance.py` (Vcr = D·f/n, k=1..4)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/load_actions.py` (kéo/hãm/ly tâm/lắc ngang/khí động)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/load_distribution.py` (3 rail pads)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/combinations.py` (Bảng A.1 — ψ0/ψ1/ψ2)
- `src/vbridge_dyn/standards/vietnam/tcvn13594/version_registry.py` (đọc năm xuất bản từ project.yaml)
- `src/vbridge_dyn/standards/eurocode/en1991_2/__init__.py` (cross-check)
- `src/vbridge_dyn/standards/international/erri_d214/time_step.py`
- `src/vbridge_dyn/importers/excel/workbook_reader.py` + `templates/bridge_template.xlsx`
- `src/vbridge_dyn/importers/excel/train_catalog_reader.py` + `templates/train_template.xlsx`
- `src/vbridge_dyn/integrations/midas/mct/writer.py` + `blocks/{geometry,properties,boundary,mass,groups,moving_load,time_history,analysis_control,result_request}.py`
- `src/vbridge_dyn/integrations/midas/mct/manifest_writer.py` — sinh `generation_manifest.json` mapping case → CSV expected
- `src/vbridge_dyn/integrations/midas/mct/export_guide.py` — sinh `export_instructions.md` + `result_export_template.xlsx` cho user
- `src/vbridge_dyn/integrations/midas/readers/{modal_csv,time_history_csv}.py` + `column_mapping.yaml` (default midas_version: 2022)
- `src/vbridge_dyn/postprocessor/envelope.py` + `checks.py` (dispatch theo standards_profile)
- `src/vbridge_dyn/storage/sqlite_store.py` + `parquet_store.py`
- `src/vbridge_dyn/report/builder.py` (ReportLab) + `templates/full_report.j2`
- `src/vbridge_dyn/ui/main_window.py` + panels
- `src/vbridge_dyn/cli/main.py` + commands
- `examples/hsr_hcm_can_gio/project.yaml` + `bridge.xlsx` — **benchmark V09 (CHÍNH)** với standards_profile=vietnam_tcvn13594
- `examples/hs2_case_study/project.yaml` + `bridge.xlsx` — benchmark V04-V05 (cross-check Eurocode pure)
- `tests/integration/test_hsr_hcm_can_gio.py` — V09 regression (kiểm tra f_bending ~5.93 Hz, f_torsion ~16.35 Hz, Vcr ~384 km/h)
- `tests/integration/test_hs2_case.py` — V04, V05 regression
- `tests/unit/test_tcvn_vs_eu_parity.py` — V06, V07 parity tests (damping + ψ factors)

---

## Cách verify khi cài v1.0

```powershell
vbdyn --version
vbdyn init my_test_project
# Mở bridge.xlsx, nhập sample 1 nhịp; chỉnh project.yaml chọn trains
vbdyn validate my_test_project
vbdyn generate --target midas my_test_project
# → generated/midas/ chứa: case_modal.mct + case_th_*.mct + generation_manifest.json
#   + export_instructions.md + result_export_template.xlsx

# (Thủ công) Mở case_modal.mct trong Midas Civil 2022 → Run → Export theo
# export_instructions.md. Lặp cho từng case_th_*.mct.
# Paste CSV vào solver_outputs/midas/ với tên match generation_manifest.json

vbdyn ingest --target midas my_test_project
vbdyn envelope my_test_project
vbdyn report --pdf reports/test_report.pdf my_test_project
# Hoặc dùng desktop:
.\dist\VBridge-Dyn.exe
```

---

## Project tracking files (root repo)

Dự án dài (~28 tuần), nhiều phiên Claude + nhiều người. 4 file md đảm bảo không mất context:

```
vbridge-dyn/
├── README.md                # Cho người mới vào repo
├── CLAUDE.md                # Auto-load khi Claude làm việc — context cốt lõi
├── PROJECT_STATUS.md        # Snapshot hiện tại — update khi đổi version/milestone
├── TASK_LOG.md              # History append-only — không sửa cũ, chỉ thêm mới
└── ...
```

### 1. `README.md` (cho người mới, tiếng Việt)

Ngắn (≤ 200 dòng):
- 1 đoạn giới thiệu (VBridge-Dyn là gì, ai dùng, tại sao)
- Quick start: cài đặt + `vbdyn init` + `vbdyn generate` + `vbdyn report`
- Yêu cầu hệ thống: Windows 10+, Python 3.11+ (cho dev), Midas Civil 2022 (cho run analysis)
- Tham chiếu CLAUDE.md cho dev, PROJECT_STATUS.md cho theo dõi tiến độ
- License + contact

### 2. `CLAUDE.md` (auto-load cho Claude, nguồn duy nhất cho context)

Cấu trúc đề xuất:

```markdown
# VBridge-Dyn — Context cho Claude

## Vai trò phần mềm (KHÔNG THAY ĐỔI)
[copy từ "Nguyên tắc MVP — ĐÃ CHỐT" section trong plan]

## Stack & kiến trúc tóm tắt
[copy "Stack công nghệ" + sơ đồ tổng quan]

## Tiêu chuẩn áp dụng
[copy "Tiêu chuẩn áp dụng" section — TCVN chính, Eurocode tham chiếu]

## Quyết định kiến trúc đã chốt
[bullet list các quyết định lớn từ AskUserQuestion + feedback rev1..rev9]
- Backend: KHÔNG có solver nội bộ. Midas Civil 2022 + RM Bridge (Phase 2)
- Tiêu chuẩn chính: vietnam_tcvn13594
- Folder workspace + Excel input + Parquet/SQLite storage + ReportLab PDF
- 4 file md tracking ở root
- ...

## Module roadmap (snapshot)
[copy bảng v0.1-v1.2+ table từ "Lộ trình MVP"]

## Conventions
- Tiếng Việt cho UI, comment, error message
- Không hard-code năm TCVN
- standards_profile dispatch trong postprocessor/checks.py
- pydantic v2, ruff + mypy + pre-commit
- Test V01-V09 (V09 weekly on-demand)

## Khi bắt đầu phiên mới
1. Đọc PROJECT_STATUS.md để biết đang ở version nào, đang làm gì
2. Đọc TASK_LOG.md mục cuối để xem context gần nhất
3. Trước khi sửa: check standards_profile, không vi phạm 3 nguyên tắc MVP

## Handoff
Nếu chuyển dự án cho người/AI khác:
1. Cập nhật PROJECT_STATUS.md với hiện trạng
2. Append vào TASK_LOG.md đoạn "## Handoff <date>" liệt kê todo + blockers
3. Commit với message "handoff: <ngày>"
```

### 3. `PROJECT_STATUS.md` (snapshot — update khi đổi)

```markdown
# Project Status — VBridge-Dyn

> Last updated: 2026-05-29

## Current version
**v0.1 — Foundation** (tuần 1/3)

## Active focus
- [ ] Reverse-engineer 1 file MCT từ Midas Civil 2022
- [ ] Pydantic schemas: Bridge, Span, Section, Material, Support, Track, TrainModel
- [ ] Excel template + reader: bridge_template.xlsx
- [x] Repo + CI setup (ruff, mypy, pytest)
- [x] uv + pyproject.toml

## Milestones (next 3)
- v0.1 complete (acceptance: `vbdyn init` + `vbdyn validate` chạy được)  — week 3
- v0.2 complete (acceptance: sinh MCT modal cho HSR HCM-CG, Midas chạy không lỗi syntax) — week 6
- v0.3 complete (acceptance: xu hướng envelope khớp HSR HCM-CG/HS2) — week 10

## Blockers
- Cần file MCT sample từ Midas Civil 2022 (chưa có → đề nghị anh export 1 file mẫu)
- Cần catalog HSLM/LM71 dạng Excel (chưa có → đề nghị nhập từ TCVN 13594-3 Bảng 15)

## Decisions log pointer
Quyết định gần nhất: xem TASK_LOG.md mục "## 2026-05-29 — Plan rev9 chốt"
```

### 4. `TASK_LOG.md` (append-only history)

```markdown
# Task Log — VBridge-Dyn

> Append-only. KHÔNG sửa entry cũ. Mỗi entry là 1 mốc thời gian/quyết định/task done.

## 2026-05-29 — Plan rev9 chốt
- 4 file tracking root: README/CLAUDE/PROJECT_STATUS/TASK_LOG (phương án A)
- Cách tổ chức: CLAUDE.md auto-load, PROJECT_STATUS snapshot, TASK_LOG history
- Quyết định kèm theo: ...

## 2026-05-29 — Plan rev8 — Midas 2022 default
- midas_version: "2022" mặc định, không 2024/NX
- Civil NX → v1.2+ future
- Thêm generation_manifest.json + export_instructions.md
- ...

## 2026-05-29 — Plan rev7 — Consistency
- TCVN 13594-4:2022 default (override "2023" nếu cần)
- dynamic_required.py neutral
- checks.py thay checks_eurocode.py
- ...

## 2026-05-29 — Plan rev6 — Vietnam standards flat
- standards/vietnam/tcvn13594/ flat, file theo capability
- Thêm standards_profile + design + dynamic blocks trong project.yaml
- Benchmark V09: f_bending=5.9312 Hz, f_torsion=16.35 Hz, Vcr=384.34 km/h
- ...

## 2026-05-29 — Plan rev5 — TCVN chính
- TCVN 13594-3:2022 + TCVN 13594-4 làm chính
- Eurocode làm tham chiếu kỹ thuật
- ...
```

### Quy tắc cập nhật

| File | Khi nào update | Ai update |
|---|---|---|
| `README.md` | Khi major API/install thay đổi | Maintainer |
| `CLAUDE.md` | Khi quyết định kiến trúc thay đổi | Cẩn thận — chỉ khi 1 quyết định lớn được khóa |
| `PROJECT_STATUS.md` | Mỗi khi đóng/mở task lớn, đổi version, gặp blocker | Mọi người |
| `TASK_LOG.md` | Append cuối ngày làm việc HOẶC khi có quyết định | Mọi người |

`CLAUDE.md` là **duy nhất** (single source of truth) — nếu PROJECT_STATUS.md và CLAUDE.md mâu thuẫn, ưu tiên CLAUDE.md cho con người, nhưng phải đồng bộ trong cùng commit.

---

## 5 module nền MVP (theo đề xuất anh)

Build theo thứ tự:

1. **`core/schemas/*`** — pydantic + validation
2. **`importers/excel/*`** — workbook reader + templates
3. **`integrations/midas/mct/*`** — writer + blocks capability-based
4. **`integrations/midas/readers/*`** — modal_csv + time_history_csv
5. **`report/*` + `postprocessor/*`** — PDF tiếng Việt vector + envelope/checks

Sau khi một model Midas nhỏ chạy được end-to-end → mở rộng RM Bridge (Phase 2) và automation runner.
