"""Pydantic schemas — data model trung lập.

Sub-modules:
- units, geometry, properties, boundary, mass, groups
- track, train, analysis, result_station, project, results
"""

from vbridge_dyn.core.schemas.boundary import ElasticLink, RigidLink, Support
from vbridge_dyn.core.schemas.bridge import Bridge
from vbridge_dyn.core.schemas.geometry import CoordinateSystem, Element, Node
from vbridge_dyn.core.schemas.groups import BoundaryGroup, LoadGroup, StructureGroup
from vbridge_dyn.core.schemas.manifest import (
    CaseEntry,
    GenerationManifest,
    StationRef,
)
from vbridge_dyn.core.schemas.mass import ElementDistributedMass, NodalMass
from vbridge_dyn.core.schemas.project import Project, ProjectMeta
from vbridge_dyn.core.schemas.properties import ElementRelease, FrameSection, Material
from vbridge_dyn.core.schemas.result_station import ResultStation
from vbridge_dyn.core.schemas.track import LoadDistribution, Track
from vbridge_dyn.core.schemas.train import Axle, TrainModel
from vbridge_dyn.core.schemas.units import UnitSystem

__all__ = [
    "Axle",
    "BoundaryGroup",
    "Bridge",
    "CaseEntry",
    "CoordinateSystem",
    "ElasticLink",
    "Element",
    "ElementDistributedMass",
    "ElementRelease",
    "FrameSection",
    "GenerationManifest",
    "LoadDistribution",
    "LoadGroup",
    "Material",
    "NodalMass",
    "Node",
    "Project",
    "ProjectMeta",
    "ResultStation",
    "RigidLink",
    "StationRef",
    "StructureGroup",
    "Support",
    "Track",
    "TrainModel",
    "UnitSystem",
]
