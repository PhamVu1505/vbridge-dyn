"""Bridge — tập hợp toàn bộ mô hình cấu trúc."""

from pydantic import BaseModel, Field, model_validator

from vbridge_dyn.core.schemas.boundary import ElasticLink, RigidLink, Support
from vbridge_dyn.core.schemas.geometry import CoordinateSystem, Element, Node
from vbridge_dyn.core.schemas.groups import BoundaryGroup, LoadGroup, StructureGroup
from vbridge_dyn.core.schemas.mass import ElementDistributedMass, NodalMass
from vbridge_dyn.core.schemas.properties import ElementRelease, FrameSection, Material
from vbridge_dyn.core.schemas.units import UnitSystem


class Bridge(BaseModel):
    """Mô hình cầu khung 3D đầy đủ (nodes + elements + properties + boundary + groups)."""

    units: UnitSystem = Field(default_factory=UnitSystem)
    coordinate_systems: list[CoordinateSystem] = Field(default_factory=list)

    nodes: list[Node]
    elements: list[Element]
    materials: list[Material]
    sections: list[FrameSection]

    element_releases: list[ElementRelease] = Field(default_factory=list)
    supports: list[Support] = Field(default_factory=list)
    elastic_links: list[ElasticLink] = Field(default_factory=list)
    rigid_links: list[RigidLink] = Field(default_factory=list)

    nodal_masses: list[NodalMass] = Field(default_factory=list)
    distributed_masses: list[ElementDistributedMass] = Field(default_factory=list)

    structure_groups: list[StructureGroup] = Field(default_factory=list)
    boundary_groups: list[BoundaryGroup] = Field(default_factory=list)
    load_groups: list[LoadGroup] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_refs(self) -> "Bridge":
        # Material IDs
        mat_ids = {m.id for m in self.materials}
        sect_ids = {s.id for s in self.sections}
        node_ids = {n.id for n in self.nodes}

        # Sections phải tham chiếu material hợp lệ
        for s in self.sections:
            if s.material_id not in mat_ids:
                msg = f"Section '{s.id}' tham chiếu material không tồn tại: '{s.material_id}'"
                raise ValueError(msg)
            for taper_ref in (s.taper_start_section_id, s.taper_end_section_id):
                if taper_ref and taper_ref not in sect_ids:
                    msg = (
                        f"Section '{s.id}' tham chiếu tapered section không tồn tại: '{taper_ref}'"
                    )
                    raise ValueError(msg)

        # Elements phải tham chiếu material + section + 2 node hợp lệ
        for e in self.elements:
            if e.material_id not in mat_ids:
                msg = f"Element {e.id} tham chiếu material không tồn tại: '{e.material_id}'"
                raise ValueError(msg)
            if e.section_id not in sect_ids:
                msg = f"Element {e.id} tham chiếu section không tồn tại: '{e.section_id}'"
                raise ValueError(msg)
            if e.n1 not in node_ids or e.n2 not in node_ids:
                msg = f"Element {e.id} tham chiếu node không tồn tại: n1={e.n1}, n2={e.n2}"
                raise ValueError(msg)
            if e.n1 == e.n2:
                msg = f"Element {e.id} có n1 == n2 = {e.n1}"
                raise ValueError(msg)

        # Supports phải gán vào node hợp lệ
        for sup in self.supports:
            if sup.node_id not in node_ids:
                msg = f"Support tham chiếu node không tồn tại: {sup.node_id}"
                raise ValueError(msg)

        return self
