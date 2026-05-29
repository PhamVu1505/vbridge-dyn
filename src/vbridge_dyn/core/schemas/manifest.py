"""Generation Manifest — mapping case ↔ MCT file ↔ expected CSV ↔ stations/nodes.

Là **xương sống** của workflow MVP (không có API): user export CSV từ Midas
thủ công, tên CSV phải khớp `expected_csv_name` để ingest tự động map về case
gốc. Sinh ra ở `generated/midas/generation_manifest.json` cùng các `.mct`.

Schema được khóa từ v0.1 (Acceptance v0.1 yêu cầu) để v0.2 builder có hợp đồng
ổn định.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CaseKind = Literal["modal", "time_history", "static_envelope"]
Signal = Literal["disp_z", "accel_z", "moment_y", "shear_z", "moment_x", "moment_z"]


class StationRef(BaseModel):
    """Vị trí xuất kết quả + node/element ID đã resolve sẵn.

    Map từ `ResultStation` (target=node|element|track) sang ID cụ thể trong
    model Midas đã sinh. Một station có thể tương ứng 1 node hoặc 1 element
    (nội suy bilinear cho track ngoài node).
    """

    station_id: str
    name: str = ""
    midas_node_ids: list[int] = Field(default_factory=list)
    midas_element_ids: list[int] = Field(default_factory=list)
    interpolation: Literal["direct", "linear"] = "direct"
    eta: float | None = Field(default=None, ge=0.0, le=1.0)


class CaseEntry(BaseModel):
    """Một case trong manifest — 1 dòng bảng tra cứu sau khi user chạy Midas."""

    case_name: str = Field(description="vd 'case_th_hslm_a1_v140' hoặc 'case_modal'")
    case_kind: CaseKind
    mct_file: str = Field(description="Tên file .mct chứa case này (relative tới output_dir)")
    expected_csv_name: str = Field(description="Tên CSV user phải đặt khi export từ Midas")

    train_id: str | None = None
    velocity_kmh: float | None = Field(default=None, ge=0.0)

    stations: list[StationRef] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)

    midas_load_case_name: str = Field(
        default="",
        description="Tên load case bên trong Midas (vd 'TH_HSLM_A1_v140')",
    )
    time_history_case_name: str | None = Field(
        default=None,
        description="Tên *TIME-HISTORY-CASE block nếu case_kind=time_history",
    )

    notes: str = ""


class GenerationManifest(BaseModel):
    """Manifest sinh kèm khi `vbdyn generate --target midas`.

    Lưu ở `<output_dir>/generation_manifest.json`. `vbdyn ingest` đọc file này
    để biết:
    - Mỗi CSV trong `solver_outputs/midas/` thuộc case nào, train/velocity nào.
    - Mỗi cột trong CSV map về station/signal nào.
    - Case nào còn thiếu CSV (chưa export hoặc đặt sai tên).
    """

    schema_version: str = "1.0"
    target: Literal["midas_civil", "rm_bridge"]
    target_version: str = Field(description="vd '2022' cho Midas Civil")

    run_id: str = Field(description="UUID hoặc timestamp định danh lần generate")
    generated_at: datetime = Field(default_factory=datetime.now)
    vbridge_dyn_version: str

    project_name: str
    project_hash: str = Field(
        default="",
        description="SHA-256 ngắn của project.yaml + bridge.xlsx — detect mismatch khi ingest",
    )

    case_split_strategy: Literal["grouped_by_train", "one_file_per_case", "single_file"]
    moving_load_strategy: Literal["time_history_function", "rail_track_analysis"]

    cases: list[CaseEntry]

    output_dir: str = Field(description="Relative tới project folder, vd 'generated/midas'")
    expected_solver_outputs_dir: str = Field(
        default="solver_outputs/midas",
        description="User paste CSV vào đây để ingest đọc",
    )

    @property
    def n_cases(self) -> int:
        return len(self.cases)

    @property
    def trains_covered(self) -> list[str]:
        return sorted({c.train_id for c in self.cases if c.train_id})

    @property
    def velocities_kmh(self) -> list[float]:
        return sorted({c.velocity_kmh for c in self.cases if c.velocity_kmh is not None})
