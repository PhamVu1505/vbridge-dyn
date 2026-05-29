"""Tham số phân tích: dải vận tốc + analysis options."""

from typing import Literal

from pydantic import BaseModel, Field


class VelocityRange(BaseModel):
    """Dải vận tốc quét theo TCVN 13594-3 (≡ EN 1991-2 6.4.6.2).

    `v_max_kmh` = 1.2 × V_design_kmh (mặc định). User có thể override.
    """

    v_min_kmh: float = Field(default=140.0, gt=0)
    v_max_kmh: float = Field(default=420.0, gt=0)
    v_line_design_kmh: float = Field(default=350.0, gt=0)
    step_kmh: float = Field(default=5.0, gt=0)
    refine_near_resonance: bool = True


class DampingConfig(BaseModel):
    """Cấu hình damping.

    `standard` neutral key, mapping qua `version_registry`:
    - 'tcvn13594_3_table_18' → standards/vietnam/tcvn13594/damping.py
    - 'en1991_2_6_4_6_3'      → standards/eurocode/en1991_2/damping.py
    """

    standard: str = "tcvn13594_3_table_18"
    bridge_type: Literal["steel", "composite", "prestressed_concrete", "reinforced_concrete"] = (
        "prestressed_concrete"
    )
    additional_damping_zeta_a: float | None = None  # eq 6.15 EN 1991-2


class TimeStepConfig(BaseModel):
    """Cấu hình time-step (ERRI D214 mặc định)."""

    method: Literal["erri_d214", "user"] = "erri_d214"
    user_dt: float | None = Field(default=None, gt=0, description="dt user-defined (s)")


class AnalysisOptions(BaseModel):
    """Tổng hợp tham số phân tích."""

    n_modes: int = Field(default=30, ge=1)
    fmax_target_hz: float | None = None  # None = auto: max(30 Hz, 1.5·n0, n3)
    damping: DampingConfig = Field(default_factory=DampingConfig)
    time_step: TimeStepConfig = Field(default_factory=TimeStepConfig)
    integration: Literal["modal_superposition", "newmark_direct"] = "modal_superposition"
