"""Unit tests cho pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from vbridge_dyn.core.schemas.boundary import RigidLink, Support
from vbridge_dyn.core.schemas.bridge import Bridge
from vbridge_dyn.core.schemas.geometry import Element, Node
from vbridge_dyn.core.schemas.project import Project, ProjectMeta
from vbridge_dyn.core.schemas.properties import ElementRelease, FrameSection, Material
from vbridge_dyn.core.schemas.result_station import ResultStation
from vbridge_dyn.core.schemas.track import Track


def _minimal_bridge() -> Bridge:
    return Bridge(
        nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=10, y=0, z=0)],
        elements=[
            Element(id=1, type="BEAM", n1=1, n2=2, material_id="C40", section_id="S1"),
        ],
        materials=[Material(id="C40", name="C40", E=3.4e10, rho=2500.0, kind="CONC")],
        sections=[
            FrameSection(
                id="S1",
                name="MainGirder",
                material_id="C40",
                A=8.97,
                Iy=10.09,
                Iz=18.5,
                J=12.3,
            ),
        ],
        supports=[Support(node_id=1, constraint=[1, 1, 1, 0, 0, 0])],
    )


class TestBridgeRefs:
    def test_minimal_bridge_ok(self) -> None:
        bridge = _minimal_bridge()
        assert len(bridge.nodes) == 2
        assert len(bridge.elements) == 1

    def test_element_unknown_material_raises(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Bridge(
                nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=10, y=0, z=0)],
                elements=[Element(id=1, n1=1, n2=2, material_id="MISSING", section_id="S1")],
                materials=[Material(id="C40", name="C40", E=3.4e10, rho=2500.0)],
                sections=[
                    FrameSection(id="S1", name="S1", material_id="C40", A=1, Iy=1, Iz=1, J=1),
                ],
                supports=[Support(node_id=1, constraint=[1, 1, 1, 1, 1, 1])],
            )
        assert "material không tồn tại" in str(exc.value)

    def test_element_unknown_section_raises(self) -> None:
        with pytest.raises(ValidationError):
            Bridge(
                nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=10, y=0, z=0)],
                elements=[Element(id=1, n1=1, n2=2, material_id="C40", section_id="MISSING")],
                materials=[Material(id="C40", name="C40", E=3.4e10, rho=2500.0)],
                sections=[
                    FrameSection(id="S1", name="S1", material_id="C40", A=1, Iy=1, Iz=1, J=1),
                ],
                supports=[Support(node_id=1, constraint=[1, 1, 1, 1, 1, 1])],
            )

    def test_element_self_loop_raises(self) -> None:
        with pytest.raises(ValidationError):
            Bridge(
                nodes=[Node(id=1, x=0, y=0, z=0)],
                elements=[Element(id=1, n1=1, n2=1, material_id="C40", section_id="S1")],
                materials=[Material(id="C40", name="C40", E=3.4e10, rho=2500.0)],
                sections=[
                    FrameSection(id="S1", name="S1", material_id="C40", A=1, Iy=1, Iz=1, J=1),
                ],
                supports=[Support(node_id=1, constraint=[1, 1, 1, 1, 1, 1])],
            )

    def test_support_unknown_node_raises(self) -> None:
        with pytest.raises(ValidationError):
            Bridge(
                nodes=[Node(id=1, x=0, y=0, z=0)],
                elements=[],
                materials=[Material(id="C40", name="C40", E=3.4e10, rho=2500.0)],
                sections=[
                    FrameSection(id="S1", name="S1", material_id="C40", A=1, Iy=1, Iz=1, J=1),
                ],
                supports=[Support(node_id=999, constraint=[1, 1, 1, 1, 1, 1])],
            )


class TestSupport:
    def test_invalid_binary_constraint(self) -> None:
        with pytest.raises(ValidationError):
            Support(node_id=1, constraint=[1, 2, 0, 1, 1, 1])

    def test_constraint_length(self) -> None:
        with pytest.raises(ValidationError):
            Support(node_id=1, constraint=[1, 1, 1])


class TestRigidLink:
    def test_dof_mask_default_111111(self) -> None:
        link = RigidLink(id=1, master=1, slaves=[2, 3])
        assert link.dof_mask == "111111"

    def test_invalid_dof_mask(self) -> None:
        with pytest.raises(ValidationError):
            RigidLink(id=1, master=1, slaves=[2], dof_mask="123456")


class TestElementRelease:
    def test_empty_dofs_raises(self) -> None:
        with pytest.raises(ValidationError):
            ElementRelease(element_id=1, end="i", dofs=[])

    def test_valid_release(self) -> None:
        r = ElementRelease(element_id=1, end="j", dofs=["My", "Mz"])
        assert r.end == "j"


class TestTrack:
    def test_ballasted_limit(self) -> None:
        t = Track(id="T1", name="Track 1", ballast_type="ballasted")
        assert t.accel_limit == 3.5

    def test_ballastless_limit(self) -> None:
        t = Track(id="T1", name="Track 1", ballast_type="ballastless")
        assert t.accel_limit == 5.0

    def test_default_distribution(self) -> None:
        t = Track(id="T1", name="Track 1")
        assert t.distribution.rail_spacing_trans == 1.435
        assert t.distribution.factors == (0.25, 0.5, 0.25)


class TestResultStation:
    def test_track_target_requires_track_fields(self) -> None:
        with pytest.raises(ValidationError):
            ResultStation(id="S1", target="track")

    def test_node_target_ok(self) -> None:
        rs = ResultStation(id="S1", target="node", node_id=5)
        assert rs.node_id == 5

    def test_element_target_requires_eta(self) -> None:
        with pytest.raises(ValidationError):
            ResultStation(id="S1", target="element", element_id=1)
        # Đầy đủ
        rs = ResultStation(id="S1", target="element", element_id=1, element_eta=0.5)
        assert rs.element_eta == 0.5


class TestProject:
    def test_minimal_project(self) -> None:
        project = Project(
            meta=ProjectMeta(name="Test", author="x"),
            bridge=_minimal_bridge(),
        )
        assert project.standards_profile == "vietnam_tcvn13594"
        assert project.tcvn13594_versions.part_4 == "2022"
        assert project.design.design_speed_kmh == 350.0
        assert project.targets.midas_civil.midas_version == "2022"
        assert project.targets.midas_civil.moving_load_strategy == "time_history_function"
        assert project.targets.midas_civil.case_split == "grouped_by_train"
        assert project.targets.rm_bridge.enabled is False
