"""Vật liệu, mặt cắt, release đầu phần tử."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Material(BaseModel):
    """Vật liệu (SI: Pa, kg/m³, 1/°C)."""

    id: str
    name: str
    E: float = Field(gt=0, description="Young modulus (Pa)")
    nu: float = Field(ge=0.0, le=0.5, default=0.2)
    rho: float = Field(gt=0, description="Mật độ khối lượng (kg/m³)")
    alpha_T: float = Field(default=1.0e-5, description="Hệ số giãn nở nhiệt (1/°C)")
    damping_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    kind: Literal["CONC", "STEEL", "SRC", "USER"] = "CONC"
    grade: str | None = None  # ví dụ "C40", "S345"; informational


class FrameSection(BaseModel):
    """Mặt cắt khung (1D beam properties).

    Cho v0.1 chỉ hỗ trợ SECT-GENERAL với 6 đặc trưng cơ bản. Section coordinates
    (outer boundary) sẽ thêm ở v0.2 cùng với sectionproperties pipeline để tự
    sinh `*SECT-GENERAL` block đầy đủ (kèm Asy/Asz, Cy/Cz, Y1..4/Z1..4 cho
    stress check).
    """

    id: str
    name: str
    material_id: str
    A: float = Field(gt=0, description="Diện tích mặt cắt (m²)")
    Iy: float = Field(gt=0, description="Moment quán tính quanh trục y (m⁴)")
    Iz: float = Field(gt=0, description="Moment quán tính quanh trục z (m⁴)")
    J: float = Field(gt=0, description="Moment xoắn (m⁴)")
    Asy: float | None = Field(default=None, description="Diện tích chịu cắt theo y (m²)")
    Asz: float | None = Field(default=None, description="Diện tích chịu cắt theo z (m²)")
    kind: Literal["girder", "pier", "cross_beam", "truss", "other"] = "girder"


class ElementRelease(BaseModel):
    """Release đầu phần tử (vd moment hinge cuối dầm).

    `dofs` liệt kê các DOF bị release: 'Fx','Fy','Fz','Mx','My','Mz' (theo local
    axis của element).
    """

    element_id: int = Field(ge=1)
    end: Literal["i", "j"]
    dofs: list[Literal["Fx", "Fy", "Fz", "Mx", "My", "Mz"]]

    @model_validator(mode="after")
    def _check_non_empty(self) -> "ElementRelease":
        if not self.dofs:
            msg = "ElementRelease.dofs phải chứa ít nhất 1 DOF"
            raise ValueError(msg)
        return self
