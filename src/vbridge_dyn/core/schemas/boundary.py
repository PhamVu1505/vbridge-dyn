"""Liên kết biên: Support, ElasticLink, RigidLink."""

from pydantic import BaseModel, Field, model_validator


class Support(BaseModel):
    """Gối tựa tại node. constraint = [Ux, Uy, Uz, Rx, Ry, Rz], 1=fixed, 0=free."""

    node_id: int = Field(ge=1)
    constraint: list[int] = Field(min_length=6, max_length=6)
    boundary_group: str = ""

    @model_validator(mode="after")
    def _check_binary(self) -> "Support":
        if any(c not in (0, 1) for c in self.constraint):
            msg = f"Support.constraint phải chứa 0 hoặc 1: {self.constraint}"
            raise ValueError(msg)
        return self


class ElasticLink(BaseModel):
    """Liên kết đàn hồi 6-DOF giữa 2 node (gối cầu, isolator).

    Đơn vị stiffness: N/m cho tịnh tiến, N·m/rad cho xoay.
    """

    id: int = Field(ge=1)
    n1: int = Field(ge=1)
    n2: int = Field(ge=1)
    kx: float = Field(ge=0)
    ky: float = Field(ge=0)
    kz: float = Field(ge=0)
    krx: float = Field(ge=0)
    kry: float = Field(ge=0)
    krz: float = Field(ge=0)
    boundary_group: str = ""


class RigidLink(BaseModel):
    """Master-slave rigid link (rigid arm, deck-girder offset).

    Midas MCT: `*RIGIDLINK` với DOF mask 111111 cho all-DOF.
    """

    id: int = Field(ge=1)
    master: int = Field(ge=1)
    slaves: list[int] = Field(min_length=1)
    boundary_group: str = ""
    dof_mask: str = Field(default="111111", min_length=6, max_length=6)

    @model_validator(mode="after")
    def _check_dof_mask(self) -> "RigidLink":
        if any(c not in "01" for c in self.dof_mask):
            msg = f"RigidLink.dof_mask phải gồm 0/1 (6 ký tự): {self.dof_mask}"
            raise ValueError(msg)
        return self
