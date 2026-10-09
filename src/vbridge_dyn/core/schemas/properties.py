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

    `A/Iy/Iz/J/Asy/Asz` là fallback stiffness-only.

    Nếu có `outer_boundary`, MCT writer dùng pipeline polygon theo repo
    Converte_RM_to_Midas: tính properties bằng sectionproperties rồi sinh
    `*SECT-PSCVALUE` kèm `OPOLY/IPOLY` và stress check points STIFF3.
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
    outer_boundary: list[tuple[float, float]] | None = Field(
        default=None,
        description="Polygon ngoài theo tọa độ local section Y-Z (m).",
    )
    holes: list[list[tuple[float, float]]] = Field(
        default_factory=list,
        description="Các polygon lỗ rỗng theo tọa độ local section Y-Z (m).",
    )
    mesh_size: float = Field(
        default=0.05,
        gt=0,
        description="Mesh size dùng cho sectionproperties khi sinh section polygon.",
    )
    midas_offset: Literal["CC", "CT", "CB"] | None = Field(
        default=None,
        description="Override offset prefix Midas. None = tự detect từ centroid.",
    )
    taper_start_section_id: str | None = Field(
        default=None,
        description="Section tại đầu i cho mặt cắt tapered.",
    )
    taper_end_section_id: str | None = Field(
        default=None,
        description="Section tại đầu j cho mặt cắt tapered.",
    )

    @model_validator(mode="after")
    def _check_polygon_inputs(self) -> "FrameSection":
        has_taper_start = self.taper_start_section_id not in (None, "")
        has_taper_end = self.taper_end_section_id not in (None, "")
        if has_taper_start != has_taper_end:
            msg = f"Section '{self.id}' tapered phải có đủ start và end section"
            raise ValueError(msg)
        if self.outer_boundary is not None and len(self.outer_boundary) < 3:
            msg = f"Section '{self.id}' outer_boundary phải có ít nhất 3 điểm"
            raise ValueError(msg)
        for i, hole in enumerate(self.holes, start=1):
            if len(hole) < 3:
                msg = f"Section '{self.id}' hole #{i} phải có ít nhất 3 điểm"
                raise ValueError(msg)
        return self


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
