"""Khối lượng node + phân bố (ballast/rail/sleeper theo group)."""

from pydantic import BaseModel, Field


class NodalMass(BaseModel):
    """Khối lượng tập trung tại node.

    Đơn vị: kg cho khối lượng tịnh tiến, kg·m² cho moment quán tính khối lượng.
    Midas MCT: `*NODALMASS` (m, m, m, Ixx, Iyy, Izz) — đơn vị target chuyển bởi
    exporter (vd ton trong Midas).
    """

    node_id: int = Field(ge=1)
    m: float = Field(ge=0, description="Khối lượng tịnh tiến (kg) — áp cho cả 3 phương")
    Ixx: float = Field(default=0.0, ge=0)
    Iyy: float = Field(default=0.0, ge=0)
    Izz: float = Field(default=0.0, ge=0)


class ElementDistributedMass(BaseModel):
    """Khối lượng bổ sung phân bố theo chiều dài element (ballast/rail/sleeper).

    Áp lên một `StructureGroup` (vd 'Track 1 ballast') với giá trị kg/m.
    Cho phép nhiều entry cùng group cộng dồn (ballast + sleeper + rail).
    """

    target_group: str
    mass_per_length: float = Field(gt=0, description="kg/m")
    note: str = ""
