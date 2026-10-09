"""Prestress tendon configuration for Midas Civil export."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TendonMaterialConfig(BaseModel):
    """Midas material values for prestressing strand in project units.

    Current Midas export uses kN, m, so elastic modulus is kN/m2 and unit
    weight is kN/m3.
    """

    name: str = "Strand1860"
    elastic_modulus: float = Field(default=1.97e8, gt=0)
    poisson: float = Field(default=0.3, ge=0, lt=0.5)
    thermal: float = 1.17e-5
    unit_weight: float = Field(default=78.5, ge=0)
    damping_ratio: float = Field(default=0.0, ge=0)


class TendonPropertyConfig(BaseModel):
    """Midas `*TDN-PROPERTY` record."""

    name: str
    area: float = Field(gt=0)
    duct_diameter: float = Field(gt=0)
    relaxation_method: float = 1
    relaxation_coefficient: float = 5
    friction: float = Field(default=0.25, ge=0)
    wobble: float = Field(default=0.0066, ge=0)
    ultimate_strength: float = Field(default=1.86e6, gt=0)
    yield_strength: float = Field(default=1.674e6, gt=0)
    anchor_slip_begin: float = Field(default=0.006, ge=0)
    anchor_slip_end: float = Field(default=0.006, ge=0)
    bonded: bool = True
    angle_disp: float = Field(default=2.64e-5, ge=0)


class TendonDxfConfig(BaseModel):
    """How to turn a tendon DXF into Midas tendon profiles."""

    file: str
    property: str
    tendon_group: str = "Tendon"
    load_group: str = "Prestress"
    load_case: str = "Prestress"
    mirror_half_span: bool = True
    span_group_regex: str = r"^Girder\d+$"
    layer_regex: str = r"^\d{4}$"
    profile_name_template: str = "G{span}-T{layer}"
    curve: Literal["SPLINE", "ROUND"] = "SPLINE"
    input_type: Literal["3D"] = "3D"


class TendonPrestressLoadConfig(BaseModel):
    """Midas `*TDN-PRESTRESS` jacking values."""

    type: Literal["FORCE", "STRESS"] = "FORCE"
    jacking: Literal["BEGIN", "END", "BOTH"] = "BOTH"
    begin: float = Field(gt=0)
    end: float = Field(gt=0)


class PrestressConfig(BaseModel):
    """Root prestress configuration block."""

    enabled: bool = False
    material: TendonMaterialConfig = Field(default_factory=TendonMaterialConfig)
    properties: list[TendonPropertyConfig] = Field(default_factory=list)
    dxf: TendonDxfConfig | None = None
    load: TendonPrestressLoadConfig | None = None
