"""Generate Midas Civil `.mct` input files."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from vbridge_dyn import __version__
from vbridge_dyn.core.schemas.manifest import CaseEntry, GenerationManifest, StationRef
from vbridge_dyn.core.schemas.project import Project
from vbridge_dyn.integrations.midas.mct.writer import write_base_model_mct


@dataclass(frozen=True)
class MctGenerationResult:
    """Output bundle from a Midas MCT generation run."""

    mct_path: Path
    manifest_path: Path
    warnings: list[str]


def generate_midas_mct(project: Project, project_folder: Path) -> MctGenerationResult:
    """Generate the initial Midas Civil input package for a project."""
    target = project.targets.midas_civil
    if not target.enabled:
        msg = "targets.midas_civil.enabled=false, không sinh MCT"
        raise ValueError(msg)

    output_dir = project_folder / target.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    mct_path = output_dir / "model_base.mct"
    warnings = write_base_model_mct(project, mct_path, project_folder=project_folder)

    manifest = _build_manifest(project, project_folder=project_folder, mct_file=mct_path.name)
    manifest_path = output_dir / "generation_manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    return MctGenerationResult(mct_path=mct_path, manifest_path=manifest_path, warnings=warnings)


def _build_manifest(project: Project, *, project_folder: Path, mct_file: str) -> GenerationManifest:
    target = project.targets.midas_civil
    return GenerationManifest(
        target="midas_civil",
        target_version=target.midas_version,
        run_id=datetime.now().strftime("%Y%m%d-%H%M%S"),
        vbridge_dyn_version=__version__,
        project_name=project.meta.name,
        project_hash=_project_hash(project_folder),
        case_split_strategy=target.case_split,
        moving_load_strategy=target.moving_load_strategy,
        output_dir=target.output_dir,
        cases=[_modal_case(mct_file, project)],
    )


def _modal_case(mct_file: str, project: Project) -> CaseEntry:
    return CaseEntry(
        case_name="case_modal_base",
        case_kind="modal",
        mct_file=mct_file,
        expected_csv_name="case_modal_base.csv",
        stations=_station_refs(project),
        signals=["disp_z"],
        midas_load_case_name="MODAL_BASE",
        notes=(
            "Base geometry/properties/boundary MCT. Dynamic train-load blocks are generated "
            "after HSLM catalog and Sub Girder load-path definition are confirmed."
        ),
    )


def _station_refs(project: Project) -> list[StationRef]:
    refs: list[StationRef] = []
    for station in project.result_stations:
        if station.target == "node" and station.node_id is not None:
            refs.append(
                StationRef(
                    station_id=station.id,
                    name=station.name,
                    midas_node_ids=[station.node_id],
                    interpolation="direct",
                ),
            )
        elif station.target == "element" and station.element_id is not None:
            refs.append(
                StationRef(
                    station_id=station.id,
                    name=station.name,
                    midas_element_ids=[station.element_id],
                    interpolation="linear",
                    eta=station.element_eta,
                ),
            )
        else:
            refs.append(StationRef(station_id=station.id, name=station.name))
    return refs


def _project_hash(project_folder: Path) -> str:
    digest = hashlib.sha256()
    for name in ("project.yaml", "bridge.xlsx"):
        path = project_folder / name
        if path.exists():
            digest.update(name.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]
