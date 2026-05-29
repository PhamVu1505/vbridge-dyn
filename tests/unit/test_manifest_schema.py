"""Khóa schema GenerationManifest v0.1 (acceptance).

Test đảm bảo schema có đầy đủ trường cần thiết để ingest workflow chạy được
ở v0.2/v0.3 mà không phải sửa schema breaking.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from vbridge_dyn.core.schemas.manifest import (
    CaseEntry,
    GenerationManifest,
    StationRef,
)


def _sample_manifest() -> GenerationManifest:
    return GenerationManifest(
        target="midas_civil",
        target_version="2022",
        run_id="20260529-001",
        vbridge_dyn_version="0.1.0.dev0",
        project_name="HSR HCM-CG",
        project_hash="abc12345",
        case_split_strategy="grouped_by_train",
        moving_load_strategy="time_history_function",
        output_dir="generated/midas",
        cases=[
            CaseEntry(
                case_name="case_modal",
                case_kind="modal",
                mct_file="case_modal.mct",
                expected_csv_name="case_modal.csv",
                signals=["disp_z"],
            ),
            CaseEntry(
                case_name="case_th_hslm_a1_v140",
                case_kind="time_history",
                mct_file="case_th_hslm_a1.mct",
                expected_csv_name="case_th_hslm_a1_v140.csv",
                train_id="HSLM-A1",
                velocity_kmh=140.0,
                midas_load_case_name="TH_HSLM_A1_v140",
                time_history_case_name="TH1",
                stations=[
                    StationRef(
                        station_id="S1",
                        name="Giữa nhịp 1",
                        midas_node_ids=[125],
                        interpolation="direct",
                    ),
                    StationRef(
                        station_id="S2",
                        name="Element mid",
                        midas_element_ids=[5],
                        interpolation="linear",
                        eta=0.5,
                    ),
                ],
                signals=["disp_z", "accel_z", "moment_y", "shear_z"],
            ),
        ],
    )


class TestGenerationManifestSchema:
    def test_minimal_required_fields(self) -> None:
        m = _sample_manifest()
        assert m.schema_version == "1.0"
        assert m.target == "midas_civil"
        assert m.target_version == "2022"
        assert m.n_cases == 2
        assert isinstance(m.generated_at, datetime)

    def test_trains_covered(self) -> None:
        m = _sample_manifest()
        assert m.trains_covered == ["HSLM-A1"]

    def test_velocities_kmh(self) -> None:
        m = _sample_manifest()
        assert m.velocities_kmh == [140.0]

    def test_case_kinds_supported(self) -> None:
        m = _sample_manifest()
        kinds = {c.case_kind for c in m.cases}
        assert "modal" in kinds
        assert "time_history" in kinds

    def test_station_ref_interpolation_modes(self) -> None:
        m = _sample_manifest()
        th_case = m.cases[1]
        assert th_case.stations[0].interpolation == "direct"
        assert th_case.stations[1].interpolation == "linear"
        assert th_case.stations[1].eta == 0.5

    def test_serializable_to_json_and_back(self, tmp_path: Path) -> None:
        m = _sample_manifest()
        json_str = m.model_dump_json(indent=2)
        loaded = GenerationManifest.model_validate_json(json_str)
        assert loaded.n_cases == m.n_cases
        assert loaded.target == m.target
        assert loaded.cases[1].train_id == "HSLM-A1"

        # Roundtrip qua file
        path = tmp_path / "manifest.json"
        path.write_text(json_str, encoding="utf-8")
        reloaded = GenerationManifest.model_validate_json(path.read_text(encoding="utf-8"))
        assert reloaded.cases[1].velocity_kmh == 140.0

    def test_grouped_by_train_strategy(self) -> None:
        """Trong grouped mode, nhiều case có thể chung 1 mct_file."""
        m = _sample_manifest()
        # case_modal và case_th_hslm_a1_v140 ở 2 file riêng (modal tách)
        # Nhưng nếu thêm v150 cho HSLM-A1, mct_file phải = case_th_hslm_a1.mct
        m.cases.append(
            CaseEntry(
                case_name="case_th_hslm_a1_v150",
                case_kind="time_history",
                mct_file="case_th_hslm_a1.mct",  # cùng file với v140
                expected_csv_name="case_th_hslm_a1_v150.csv",
                train_id="HSLM-A1",
                velocity_kmh=150.0,
                signals=["disp_z", "accel_z"],
            ),
        )
        mct_files = {c.mct_file for c in m.cases if c.train_id == "HSLM-A1"}
        assert mct_files == {"case_th_hslm_a1.mct"}, "grouped_by_train: cùng train → 1 file"

    def test_velocity_must_be_non_negative(self) -> None:
        with pytest.raises(ValidationError):
            CaseEntry(
                case_name="x",
                case_kind="time_history",
                mct_file="x.mct",
                expected_csv_name="x.csv",
                velocity_kmh=-10.0,
            )

    def test_eta_must_be_in_unit_interval(self) -> None:
        with pytest.raises(ValidationError):
            StationRef(station_id="S", eta=1.5)
