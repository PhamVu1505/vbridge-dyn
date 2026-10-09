"""Project — root schema gắn tất cả lại.

File `project.yaml` ánh xạ trực tiếp sang `Project` model.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from vbridge_dyn.core.schemas.analysis import AnalysisOptions, VelocityRange
from vbridge_dyn.core.schemas.bridge import Bridge
from vbridge_dyn.core.schemas.result_station import ResultStation
from vbridge_dyn.core.schemas.tendon import PrestressConfig
from vbridge_dyn.core.schemas.track import Track
from vbridge_dyn.core.schemas.train import TrainModel


class ProjectMeta(BaseModel):
    name: str
    author: str = ""
    description: str = ""
    created_at: date = Field(default_factory=date.today)
    schema_version: str = "1.0"
    locale: str = "vi-VN"


class TCVN13594Versions(BaseModel):
    """Năm xuất bản từng phần TCVN 13594 — KHÔNG hard-code trong source."""

    part_3: str = "2022"
    part_4: str = "2022"  # override "2023" nếu dự án dùng bản mới
    part_5: str = "2023"
    part_10: str = "2023"


class DesignParams(BaseModel):
    design_speed_kmh: float = Field(default=350.0, gt=0)
    max_analysis_speed_factor: float = Field(default=1.2, ge=1.0)
    track_type: Literal["ballasted", "ballastless"] = "ballasted"
    track_gauge_mm: int = 1435


class DynamicConfig(BaseModel):
    """Cấu hình neutral cho phần dynamic — clause map qua version_registry."""

    check_required_method: str = "tcvn13594_dynamic_required"
    damping_method: str = "tcvn13594_3_table_18"
    resonance_check: bool = True
    time_step_method: str = "erri_d214"


class TargetMidasConfig(BaseModel):
    enabled: bool = True
    midas_version: str = "2022"
    units: dict[str, str] = Field(
        default_factory=lambda: {"force": "kN", "length": "m", "mass": "ton", "time": "s"},
    )
    export_mode: Literal["mct"] = "mct"
    case_split: Literal["grouped_by_train", "one_file_per_case", "single_file"] = "grouped_by_train"
    output_dir: str = "generated/midas"
    moving_load_strategy: Literal["time_history_function", "rail_track_analysis"] = (
        "time_history_function"
    )
    time_dependent_concrete: "TimeDependentConcreteConfig" = Field(
        default_factory=lambda: TimeDependentConcreteConfig()
    )


class TimeDependentConcreteConfig(BaseModel):
    """Midas CEB-FIP time-dependent material settings for concrete."""

    enabled: bool = False
    code: Literal["CEB"] = "CEB"
    elasticity_code: Literal["CEB-FIP"] = "CEB-FIP"
    relative_humidity_percent: float = Field(default=70.0, gt=0, le=100)
    notional_size: float = Field(default=1.0, gt=0)
    cement_type: Literal["NR", "RS", "SL"] = "NR"
    age_days: float = Field(default=3.0, gt=0)
    include_materials: list[str] = Field(default_factory=list)
    strengths: dict[str, float] = Field(default_factory=dict)


class TargetRMBridgeConfig(BaseModel):
    enabled: bool = False  # Phase 2
    rm_version: str = "12.x"
    units: dict[str, str] = Field(
        default_factory=lambda: {"force": "kN", "length": "m", "mass": "ton", "time": "s"},
    )
    export_mode: Literal["tcl"] = "tcl"
    output_dir: str = "generated/rm_bridge"
    rolling_stock_module: str = "standard"


class Targets(BaseModel):
    midas_civil: TargetMidasConfig = Field(default_factory=TargetMidasConfig)
    rm_bridge: TargetRMBridgeConfig = Field(default_factory=TargetRMBridgeConfig)


class ReportConfig(BaseModel):
    template: str = "full_report"
    language: str = "vi-VN"
    engine: Literal["reportlab", "weasyprint"] = "reportlab"
    output: str = "reports/{date}_full_report.pdf"


class ChecksConfig(BaseModel):
    standards: list[str] = Field(
        default_factory=lambda: [
            "tcvn13594_4_dynamic_check",
            "tcvn13594_4_acceleration_limit",
            "tcvn13594_4_deflection_limit",
            "tcvn13594_4_daf",
        ],
    )
    cross_check: list[str] = Field(default_factory=lambda: ["en1990_a2_4_4_2"])
    custom_limits: str | None = None


class Project(BaseModel):
    """Root schema cho 1 project — ánh xạ 1-1 với `project.yaml`."""

    meta: ProjectMeta
    standards_profile: Literal["vietnam_tcvn13594", "eurocode_pure"] = "vietnam_tcvn13594"
    tcvn13594_versions: TCVN13594Versions = Field(default_factory=TCVN13594Versions)
    design: DesignParams = Field(default_factory=DesignParams)
    dynamic: DynamicConfig = Field(default_factory=DynamicConfig)

    bridge: Bridge
    tracks: list[Track] = Field(default_factory=list)
    trains: list[TrainModel] = Field(default_factory=list)
    velocity_range: VelocityRange = Field(default_factory=VelocityRange)
    analysis: AnalysisOptions = Field(default_factory=AnalysisOptions)
    prestress: PrestressConfig = Field(default_factory=PrestressConfig)
    result_stations: list[ResultStation] = Field(default_factory=list)

    targets: Targets = Field(default_factory=Targets)
    checks: ChecksConfig = Field(default_factory=ChecksConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)
