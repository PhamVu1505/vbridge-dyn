"""Mô hình tải trọng đoàn tàu (axle list).

Hỗ trợ: LM71, SW/0, SW/2, HSLM-A1..A10, HSLM-B, Thalys, ICE, EMU, custom.
Catalog **không** ship sẵn (bản quyền TCVN/EN); user import từ Excel.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Axle(BaseModel):
    """Một trục bánh xe trên đoàn tàu (đơn vị SI: m, N)."""

    position: float = Field(ge=0, description="Vị trí dọc trục tàu, gốc tại đầu tàu (m)")
    load: float = Field(gt=0, description="Lực trục (N)")


TrainKind = Literal["LM71", "SW0", "SW2", "HSLM_A", "HSLM_B", "real", "custom"]


class TrainModel(BaseModel):
    """Mô hình đoàn tàu (axle list).

    `id`: vd "HSLM-A1", "Thalys-Single", "Custom-001", "LM71-alpha-1.0".
    `kind`: phân loại để áp đúng tổ hợp ψ (TCVN 13594-3 Bảng A.1) và DAF.
    `catalog_meta`: lưu thông tin gốc (N axles, d, D, P cho HSLM; alpha cho LM71)
      để truy vết và regenerate khi cần.
    """

    id: str
    name: str
    kind: TrainKind
    axles: list[Axle] = Field(min_length=1)
    length: float = Field(gt=0, description="Tổng chiều dài đoàn tàu (m)")
    catalog_meta: dict[str, Any] = Field(default_factory=dict)
