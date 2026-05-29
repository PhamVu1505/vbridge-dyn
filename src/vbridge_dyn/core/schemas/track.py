"""Đường ray (track) và phân bố tải trọng trục.

Tham chiếu: TCVN 13594-3 ≡ EN 1991-2 6.3.6.3 (longitudinal 3 rail pads).
"""

from typing import Literal

from pydantic import BaseModel, Field


class LoadDistribution(BaseModel):
    """Phân bố tải trọng trục theo TCVN 13594-3 / EN 1991-2 6.3.6.3.

    Mỗi axle phân thành 3 điểm gối ray dọc với hệ số (0.25, 0.5, 0.25).
    Khoảng cách giữa các sleeper mặc định 0.6 m, khoảng cách ray 1.435 m.
    """

    rail_spacing_trans: float = Field(default=1.435, gt=0, description="Khoảng cách 2 ray (m)")
    sleeper_spacing_long: float = Field(default=0.6, gt=0, description="Khoảng cách sleeper (m)")
    factors: tuple[float, float, float] = (0.25, 0.5, 0.25)


class Track(BaseModel):
    """Đường ray trên cầu.

    `centerline_y`: vị trí tim ray ngang so với tim cầu (m, sang trái âm).
    `ballast_type` quyết định acceleration limit:
    - ballasted: 3.5 m/s² (TCVN 13594-4 ≡ EN 1990 A2.4.4.2.1)
    - ballastless: 5.0 m/s²
    """

    id: str
    name: str = "Track 1"
    centerline_y: float = 0.0
    rail_height_above_deck: float = Field(
        default=0.0, ge=0, description="Cao độ ray so với mặt deck (m) — cho eccentricity"
    )
    distribution: LoadDistribution = Field(default_factory=LoadDistribution)
    ballast_type: Literal["ballasted", "ballastless"] = "ballasted"

    @property
    def accel_limit(self) -> float:
        """Giới hạn gia tốc đứng (m/s²)."""
        return 3.5 if self.ballast_type == "ballasted" else 5.0
