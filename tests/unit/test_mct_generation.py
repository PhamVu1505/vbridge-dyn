"""Tests for initial Midas MCT generation."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from vbridge_dyn.cli.main import app
from vbridge_dyn.core.schemas.properties import FrameSection, Material
from vbridge_dyn.integrations.midas.mct import generate_midas_mct
from vbridge_dyn.integrations.midas.mct.sections import (
    _translated_mesh_extents,
    build_polygon_section_lines,
    build_tapered_section_lines,
)
from vbridge_dyn.integrations.midas.mct.writer import _material_line
from vbridge_dyn.io.project_io import load_project_folder

runner = CliRunner()


def _point_count(poly_line: str) -> int:
    coords = poly_line.split("=", 1)[1].split(",")
    return len(coords) // 2


def test_generate_midas_mct_from_init_template(tmp_path: Path) -> None:
    project_dir = tmp_path / "test_project"
    init_result = runner.invoke(app, ["init", str(project_dir), "--name", "Test"])
    assert init_result.exit_code == 0, init_result.output

    project = load_project_folder(project_dir)
    result = generate_midas_mct(project, project_dir)

    text = result.mct_path.read_text(encoding="utf-8")
    assert "*NODE" in text
    assert "*ELEMENT" in text
    assert "*MATERIAL" in text
    assert "*SECT-PSCVALUE" in text
    # GEN section luôn phải có OPOLY (kể cả fallback chữ nhật) mới hiển thị trong Midas
    assert "OPOLY=" in text
    assert "*CONSTRAINT" in text
    assert "   1, 111000, " in text
    assert "*BNDR-GROUP" in text
    assert "Bearings, 0" in text
    assert "*STLDCASE" in text
    assert "*SELFWEIGHT" in text
    assert "*EIGEN-CTRL" in text
    assert "*ENDDATA" in text
    assert result.manifest_path.exists()


def test_cli_generate_midas_creates_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "test_project"
    runner.invoke(app, ["init", str(project_dir), "--name", "Test"])

    result = runner.invoke(app, ["generate", str(project_dir), "--target", "midas"])

    assert result.exit_code == 0, result.output
    assert (project_dir / "generated" / "midas" / "model_base.mct").exists()
    assert (project_dir / "generated" / "midas" / "generation_manifest.json").exists()


def test_polygon_section_writer_matches_converter_shape_contract() -> None:
    pytest.importorskip("shapely")
    pytest.importorskip("sectionproperties")

    section = FrameSection(
        id="RECT",
        name="Rectangle",
        material_id="C40",
        A=4.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=[(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)],
        mesh_size=0.2,
    )
    material = Material(id="C40", name="C40", E=3.4e10, rho=2500.0, kind="CONC")

    lines = build_polygon_section_lines(section, material, midas_id=7)

    assert lines[0].startswith("SECT=   7, VALUE")
    assert lines[1].startswith("4.0000,")
    assert len([line for line in lines if line.startswith("OPOLY=")]) == 1


def test_polygon_section_writer_preserves_collinear_dxf_points() -> None:
    pytest.importorskip("shapely")
    pytest.importorskip("sectionproperties")

    outer = [
        (-2.0, -1.0),
        (-1.0, -1.0),
        (0.0, -1.0),
        (1.0, -1.0),
        (2.0, -1.0),
        (2.0, 1.0),
        (0.0, 1.0),
        (-2.0, 1.0),
    ]
    hole = [
        (-0.8, -0.4),
        (0.0, -0.4),
        (0.8, -0.4),
        (0.8, 0.4),
        (0.0, 0.4),
        (-0.8, 0.4),
    ]
    section = FrameSection(
        id="COLLINEAR",
        name="Collinear points",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=outer,
        holes=[hole],
        mesh_size=0.2,
    )
    material = Material(id="C40", name="C40", E=3.4e10, rho=2500.0, kind="CONC")

    lines = build_polygon_section_lines(section, material, midas_id=8)
    opoly = next(line for line in lines if line.startswith("OPOLY="))
    ipoly = next(line for line in lines if line.startswith("IPOLY="))

    assert _point_count(opoly) == len(outer)
    assert _point_count(ipoly) == len(hole)


def test_tapered_section_writer_uses_yes_no_polygons() -> None:
    pytest.importorskip("shapely")
    pytest.importorskip("sectionproperties")

    start = FrameSection(
        id="PIER_TOP",
        name="Pier top",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=[(-1.0, -0.5), (1.0, -0.5), (1.0, 0.5), (-1.0, 0.5)],
        mesh_size=0.2,
    )
    end = FrameSection(
        id="PIER_BOT",
        name="Pier bottom",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=[(-1.5, -0.8), (1.5, -0.8), (1.5, 0.8), (-1.5, 0.8)],
        mesh_size=0.2,
    )
    taper = FrameSection(
        id="PIER_TAPER",
        name="Pier taper",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        taper_start_section_id="PIER_TOP",
        taper_end_section_id="PIER_BOT",
    )
    material = Material(id="C40", name="C40", E=3.4e10, rho=2500.0, kind="CONC")

    lines = build_tapered_section_lines(taper, start, end, material, midas_id=9)

    assert lines[0].startswith("SECT=   9, TAPERED")
    assert any(line.startswith("OPOLY=YES,") for line in lines)
    assert any(line.startswith("OPOLY=NO,") for line in lines)


def test_material_line_uses_short_midas_name() -> None:
    material = Material(
        id="PC270",
        name="Thép dự ứng lực 270 low-relaxation",
        E=1.97e11,
        rho=7850.0,
        kind="STEEL",
    )

    line = _material_line(material, midas_id=6)
    mname = line.split(",")[2].strip()

    assert mname == "PC270"
    assert len(mname) <= 16
    assert "low-relaxation" not in line


def test_stiff2_extents_use_mesh_vertices_when_available() -> None:
    class DummySectionModel:
        def __init__(self) -> None:
            self.mesh = {"vertices": [(-2.0, -1.0), (2.0, 1.0), (0.0, 2.0)]}

    y_max, y_min, z_max, z_min = _translated_mesh_extents(
        DummySectionModel(),
        cy=0.5,
        cz=-0.5,
        fallback_points=[(-1.0, -1.0), (1.0, 1.0)],
    )

    assert y_max == pytest.approx(1.5)
    assert y_min == pytest.approx(-2.5)
    assert z_max == pytest.approx(2.5)
    assert z_min == pytest.approx(-0.5)


def test_circular_section_emits_dbuser(tmp_path: Path) -> None:
    import math

    from vbridge_dyn.core.schemas.bridge import Bridge
    from vbridge_dyn.core.schemas.geometry import Element, Node
    from vbridge_dyn.core.schemas.project import Project, ProjectMeta
    from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct

    n = 36
    radius = 0.75  # D = 1.5 m (cọc khoan nhồi)
    circle = [
        (
            round(radius * math.cos(2 * math.pi * k / n), 6),
            round(radius * math.sin(2 * math.pi * k / n), 6),
        )
        for k in range(n)
    ]
    section = FrameSection(
        id="PILE",
        name="Coc D1500",
        material_id="C30",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=circle,
        kind="pier",
    )
    bridge = Bridge(
        nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=0, y=0, z=-10)],
        elements=[Element(id=1, type="BEAM", n1=1, n2=2, material_id="C30", section_id="PILE")],
        materials=[Material(id="C30", name="C30", E=3.0e10, rho=2500.0, kind="CONC")],
        sections=[section],
    )
    project = Project(meta=ProjectMeta(name="pile"), bridge=bridge)

    out = tmp_path / "pile.mct"
    write_base_model_mct(project, out)
    text = out.read_text(encoding="utf-8")

    assert "*SECTION" in text
    assert "DBUSER" in text
    assert "SR ," in text  # solid round, không phải GEN polygon
    assert "*SECT-PSCVALUE" not in text  # chỉ có mặt cắt tròn → không có khối PSC


def test_solid_rectangle_section_emits_builtin_sb(tmp_path: Path) -> None:
    from vbridge_dyn.core.schemas.bridge import Bridge
    from vbridge_dyn.core.schemas.geometry import Element, Node
    from vbridge_dyn.core.schemas.project import Project, ProjectMeta
    from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct

    section = FrameSection(
        id="PILECAP",
        name="Pilecap 7.5x10.5",
        material_id="C30",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=[(-3.75, -5.25), (3.75, -5.25), (3.75, 5.25), (-3.75, 5.25)],
        kind="pier",
    )
    bridge = Bridge(
        nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=0, y=0, z=2.5)],
        elements=[Element(id=1, type="BEAM", n1=1, n2=2, material_id="C30", section_id="PILECAP")],
        materials=[Material(id="C30", name="C30", E=3.0e10, rho=2500.0, kind="CONC")],
        sections=[section],
    )
    project = Project(meta=ProjectMeta(name="pilecap"), bridge=bridge)

    out = tmp_path / "pilecap.mct"
    write_base_model_mct(project, out)
    text = out.read_text(encoding="utf-8")

    assert "*SECTION" in text
    assert "DBUSER" in text
    assert "SB , 2, 7.5, 10.5" in text
    assert "*SECT-PSCVALUE" not in text
    assert "IPOLY=" not in text


def test_tapered_section_group_and_elastic_link_blocks(tmp_path: Path) -> None:
    from vbridge_dyn.core.schemas.boundary import ElasticLink
    from vbridge_dyn.core.schemas.bridge import Bridge
    from vbridge_dyn.core.schemas.geometry import Element, Node
    from vbridge_dyn.core.schemas.project import Project, ProjectMeta
    from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct

    small = FrameSection(
        id="S_SMALL",
        name="Small",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=[(-1.0, -0.5), (1.0, -0.5), (1.0, 0.5), (-1.0, 0.5)],
    )
    large = FrameSection(
        id="S_LARGE",
        name="Large",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        outer_boundary=[(-2.0, -1.0), (2.0, -1.0), (2.0, 1.0), (-2.0, 1.0)],
    )
    taper = FrameSection(
        id="S_TAPER",
        name="Taper",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
        taper_start_section_id="S_SMALL",
        taper_end_section_id="S_LARGE",
    )
    bridge = Bridge(
        nodes=[
            Node(id=1, x=0, y=0, z=0),
            Node(id=2, x=0, y=0, z=1),
            Node(id=3, x=0, y=0, z=2),
            Node(id=10, x=0, y=0, z=3),
            Node(id=11, x=0, y=0, z=4),
        ],
        elements=[
            Element(
                id=1001,
                type="BEAM",
                n1=1,
                n2=2,
                material_id="C40",
                section_id="S_TAPER",
                structure_group="P1",
            ),
            Element(
                id=1002,
                type="BEAM",
                n1=2,
                n2=3,
                material_id="C40",
                section_id="S_TAPER",
                structure_group="P1",
            ),
        ],
        materials=[Material(id="C40", name="C40", E=3.4e10, rho=2500.0, kind="CONC")],
        sections=[small, large, taper],
        elastic_links=[
            ElasticLink(
                id=1,
                n1=10,
                n2=11,
                kx=0,
                ky=0,
                kz=0,
                krx=0,
                kry=0,
                krz=0,
                boundary_group="bearing_01",
                dof_mask="111000",
            )
        ],
    )
    project = Project(meta=ProjectMeta(name="links"), bridge=bridge)

    out = tmp_path / "links.mct"
    write_base_model_mct(project, out)
    text = out.read_text(encoding="utf-8")

    assert "*BNDR-GROUP" in text
    assert "bearing_01, 0" in text
    assert "*TS-GROUP" in text
    assert "P1, 1001to1002,  LINEAR" in text
    assert "*ELASTICLINK" in text
    assert "YES, YES, YES, NO, NO, NO" in text


def test_distributed_mass_emits_beamload(tmp_path: Path) -> None:
    from vbridge_dyn.core.schemas.bridge import Bridge
    from vbridge_dyn.core.schemas.geometry import Element, Node
    from vbridge_dyn.core.schemas.groups import StructureGroup
    from vbridge_dyn.core.schemas.mass import ElementDistributedMass
    from vbridge_dyn.core.schemas.project import Project, ProjectMeta
    from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct

    section = FrameSection(
        id="S1",
        name="Rect",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
    )
    bridge = Bridge(
        nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=10, y=0, z=0)],
        elements=[
            Element(
                id=1,
                type="BEAM",
                n1=1,
                n2=2,
                material_id="C40",
                section_id="S1",
                structure_group="TrackLoads",
            )
        ],
        materials=[Material(id="C40", name="C40", E=3.4e10, rho=2500.0, kind="CONC")],
        sections=[section],
        structure_groups=[StructureGroup(id="TrackLoads", name="Track Loads", element_ids=[1])],
        distributed_masses=[
            ElementDistributedMass(target_group="TrackLoads", mass_per_length=1000.0)
        ],
    )
    project = Project(meta=ProjectMeta(name="loads"), bridge=bridge)

    out = tmp_path / "loads.mct"
    warnings = write_base_model_mct(project, out)
    text = out.read_text(encoding="utf-8")

    assert not [warning for warning in warnings if "DistributedMass" in warning]
    assert "DW TrackLoads, D" in text
    assert "*LOADTOMASS" in text
    assert "DW TrackLoads, 1" in text
    assert "*USE-STLD, DW TrackLoads" in text
    assert "*BEAMLOAD" in text
    assert "0, -9.806, 1, -9.806" in text


def test_time_dependent_concrete_blocks_link_concrete_materials(tmp_path: Path) -> None:
    from vbridge_dyn.core.schemas.bridge import Bridge
    from vbridge_dyn.core.schemas.geometry import Element, Node
    from vbridge_dyn.core.schemas.project import Project, ProjectMeta
    from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct

    section = FrameSection(
        id="S1",
        name="Rect",
        material_id="C40",
        A=1.0,
        Iy=1.0,
        Iz=1.0,
        J=1.0,
    )
    bridge = Bridge(
        nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=1, y=0, z=0)],
        elements=[Element(id=1, type="BEAM", n1=1, n2=2, material_id="C40", section_id="S1")],
        materials=[
            Material(id="C40", name="Concrete C40", E=3.4e10, rho=2500.0, kind="CONC", grade="C40"),
            Material(id="S", name="Steel", E=2.0e11, rho=7850.0, kind="STEEL"),
        ],
        sections=[section],
    )
    project = Project(meta=ProjectMeta(name="tdm"), bridge=bridge)
    project.targets.midas_civil.time_dependent_concrete.enabled = True

    out = tmp_path / "tdm.mct"
    warnings = write_base_model_mct(project, out)
    text = out.read_text(encoding="utf-8")

    assert "*TDM-TYPE" in text
    assert "NAME=C40, CEB, 40000, 70, 1, NR, 3, 0" in text
    assert "*TDM-ELAST" in text
    assert "NAME=C40, CODE, CEB-FIP, 40000, 2" in text
    assert "*TDM-LINK" in text
    assert "   1, C40, C40" in text
    assert "Đã link time-dependent concrete cho C40(mat 1)." in warnings
