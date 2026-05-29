"""Hình học: Node, Element, CoordinateSystem.

Midas convention: X dọc, Y ngang, Z đứng.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CoordinateSystem(BaseModel):
    """Hệ tọa độ local. id='global' luôn tồn tại mặc định."""

    id: str
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    x_axis: tuple[float, float, float] = (1.0, 0.0, 0.0)
    y_axis: tuple[float, float, float] = (0.0, 1.0, 0.0)


class Node(BaseModel):
    """Nút (đơn vị: SI mét)."""

    id: int = Field(ge=1)
    x: float
    y: float
    z: float
    csys_id: str = "global"


class Element(BaseModel):
    """Phần tử 1D (BEAM hoặc TRUSS).

    `structure_group` để gom nhóm chức năng (vd 'Main Girder', 'Sub Girder',
    'Pier', 'Cross Beam'). Map sang Midas `*GROUP`.

    `local_axis_csys_id` chỉ dùng khi cần override local axis của beam (vd cột
    đặt nghiêng); để None thì Midas tự tính.
    """

    id: int = Field(ge=1)
    type: Literal["BEAM", "TRUSS"] = "BEAM"
    n1: int = Field(ge=1)
    n2: int = Field(ge=1)
    material_id: str
    section_id: str
    structure_group: str = ""
    local_axis_csys_id: str | None = None
