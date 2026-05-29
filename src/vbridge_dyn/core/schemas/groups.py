"""Group: structure / boundary / load.

Midas MCT có 3 loại group tương ứng:
- *GROUP (Structure Group)
- *BNDR-GROUP (Boundary Group)
- *LOAD-GROUP (Load Group)
"""

from pydantic import BaseModel, Field


class StructureGroup(BaseModel):
    """Nhóm structure: gồm elements và/hoặc nodes."""

    id: str
    name: str
    element_ids: list[int] = Field(default_factory=list)
    node_ids: list[int] = Field(default_factory=list)


class BoundaryGroup(BaseModel):
    """Nhóm boundary (supports, links)."""

    id: str
    name: str


class LoadGroup(BaseModel):
    """Nhóm load (cho phép apply/remove combinations)."""

    id: str
    name: str
