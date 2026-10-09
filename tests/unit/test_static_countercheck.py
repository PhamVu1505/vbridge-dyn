"""Tests for BXD static report countercheck MCT generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from vbridge_dyn.integrations.midas.mct.dynamic_countercheck import (
    generate_bxd_32_6_dynamic_countercheck,
)
from vbridge_dyn.integrations.midas.mct.static_countercheck import (
    generate_bxd_32_6_static_countercheck,
)

pytest.importorskip("ezdxf")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_bxd_static_countercheck_generates_report_load_cases(tmp_path: Path) -> None:
    project_dir = _repo_root() / "examples" / "bxd"
    if (
        not (project_dir / "bridge.xlsx").exists()
        or not (project_dir / "dxf" / "tendon.dxf").exists()
    ):
        pytest.skip("BXD fixtures are not available")

    result = generate_bxd_32_6_static_countercheck(
        project_dir,
        output_path=tmp_path / "model_static_countercheck_32_6.mct",
    )
    text = result.mct_path.read_text(encoding="utf-8")

    assert "Pilecap" not in text
    assert "Pier shaft" not in text
    assert "0, 1, 1, NO, YES, 9.806" in text
    assert "*TDN-PROFILE" in text
    assert "PT_20T15.2_D110" in text
    assert "G1_REPORT, D" not in text
    assert "G2_REPORT, D" in text
    assert "*MVLDCODE" in text
    assert "CODE=EUROCODE" in text
    assert "*MVLDCASE(EURO)" in text
    assert "*MVLDCASE   ; Moving Load Cases" not in text
    assert "nLCTYPE" not in text
    assert "NAME=Load Model 71, 1, 5, Load Model 71, 80, 0, 0.8, 80, 0, 0.8, 0.9" in text
    assert "NAME=Load Model 71 Fatigue, 1, 5, Load Model 71, 80, 0, 0.8, 80, 0, 0.8, 1" in text
    assert "NAME=LM71_2T, NO, 5, , 1, 0.8, 0.7, 0.6, YES, 1, 1, 0.75, 0" in text
    assert "Load Model 71, 1, 0, 2, T1, T2" in text
    assert "NAME=LM71_2T_PHI" in text
    assert "Load Model 71, 1.129, 0, 2, T1, T2" in text
    assert "NAME=LM71_FAT_2T_PHI" in text
    assert "Load Model 71 Fatigue, 1.129, 0, 2, T1, T2" in text
    assert "*STAGE    ; Define Construction Stage" in text
    assert "NAME=CS1_Prestress_3d, 0, YES, YES, NO, 5" in text
    assert "NAME=CS2_G2_36d, 33, YES, YES, NO, 5" in text
    assert "NAME=CS3_LongTerm_100y, 36464, YES, YES, NO, 5" in text
    assert "AELEM=Girder1, 3" in text
    assert "100002, 111100, Support" in text
    assert "100030, 011100, Support" in text
    assert "ABNDR=Support, ORIGINAL" in text
    assert "ALOAD=SelfWeight, FIRST, PS-BXD, FIRST" in text
    assert "ALOAD=G2-BXD, LAST" in text
    assert "*STAGE-CTRL" in text
    assert "*TS-GROUP" in text
    assert "1-3," in text
    assert "3-1," in text
    assert "TRANSPORT_DYN, D" in text
    assert "WIND_Y_REPORT, D" in text
    assert "*LOADCOMB" in text
    assert "NAME=ULS_LM71" in text
    assert "ST, SelfWeight, 1.35" in text
    assert "MV, LM71_2T_PHI, 1.45" in text
    assert "NAME=ULS_TRANSPORT" in text
    assert "NAME=SLS_TRANSPORT_P" in text
    assert "ST, SelfWeight, 1, ST, Prestress, 1, ST, TRANSPORT_DYN, 1" in text
    assert "NAME=FATIGUE_LM71_EN" in text
    assert "MV, LM71_FAT_2T_PHI, 1.04" in text
    assert "ST, SelfWeight, 1.35, ST, TRANSPORT_DYN, 1.5" in text
    assert "ST, SelfWeight, 1.35, ST, G2_REPORT, 1.35, ST, TRANSPORT_DYN, 1.5" not in text
    assert "214.1" not in text
    assert "106.75" in text
    assert "3906" in text
    assert result.lm71_start_m is None
    assert result.transport_start_m == pytest.approx(-4.25)


def test_bxd_dynamic_countercheck_generates_hslm_time_history(tmp_path: Path) -> None:
    project_dir = _repo_root() / "examples" / "bxd"
    if (
        not (project_dir / "bridge.xlsx").exists()
        or not (project_dir / "dxf" / "tendon.dxf").exists()
    ):
        pytest.skip("BXD fixtures are not available")

    result = generate_bxd_32_6_dynamic_countercheck(
        project_dir,
        output_path=tmp_path / "model_dynamic_countercheck_32_6_A1_330.mct",
    )
    text = result.mct_path.read_text(encoding="utf-8")

    assert result.train_id == "HSLM-A1"
    assert result.velocity_kmh == pytest.approx(330.0)
    assert result.include_prestress is True
    assert result.graph_node_id == 100016
    assert result.loaded_node_count == result.function_count
    assert result.loaded_node_count == 155
    assert result.bridge_length_m == pytest.approx(163.4)
    assert result.duration_s == pytest.approx(8.142545455)
    assert "0, 1, 1, NO, YES, 9.806" in text
    assert "G2_REPORT, D" in text
    assert "*LOADTOMASS" in text
    assert "G2_REPORT, 1" in text
    assert "*USE-STLD, G2_REPORT" in text
    assert "0, -106.75, 1, -106.75" in text
    assert "BXD 32.6 m dynamic countercheck: HSLM-A1 at 330 km/h" in text
    assert "*TFUNCTION" in text
    assert "FUNC=HSLM-A1_330kmh_n100016, 1, 3, 0, 1, 9.806" in text
    assert "*THLDCASE" in text
    assert "NAME=HSLM-A1_330" in text
    assert "1, 1, 1, 0, 8.142545455, 0.001" in text
    assert "1, 0.015" in text
    assert "*DYN-NLOAD" in text
    assert "100016, HSLM-A1_330, HSLM-A1_330kmh_n100016, Z, 0, -1" in text
    assert "*TH-GRAPH" in text
    assert "deck acc 32.6, HSLM-A1_330, 100016" in text
    assert "deck dz 32.6, HSLM-A1_330, 100016" in text
    assert text.index("*LOADTOMASS") < text.index("*TFUNCTION")
    assert text.index("*TFUNCTION") < text.index("*EIGEN-CTRL")


def test_bxd_dynamic_countercheck_can_exclude_prestress_tendons(tmp_path: Path) -> None:
    project_dir = _repo_root() / "examples" / "bxd"
    if (
        not (project_dir / "bridge.xlsx").exists()
        or not (project_dir / "dxf" / "tendon.dxf").exists()
    ):
        pytest.skip("BXD fixtures are not available")

    result = generate_bxd_32_6_dynamic_countercheck(
        project_dir,
        output_path=tmp_path / "model_dynamic_countercheck_32_6_A1_330_no_cable.mct",
        include_prestress=False,
    )
    text = result.mct_path.read_text(encoding="utf-8")

    assert result.include_prestress is False
    assert result.case_name == "HSLM-A1_330_NO_CABLE"
    assert "Prestress/tendon model: excluded" in text
    assert "*TDN-PROPERTY" not in text
    assert "*TDN-PROFILE" not in text
    assert "*TDN-PRESTRESS" not in text
    assert "Prestress, PS" not in text
    assert "G2_REPORT, 1" in text
    assert "NAME=HSLM-A1_330_NO_CABLE" in text
    assert "100016, HSLM-A1_330_NO_CABLE, HSLM-A1_330kmh_n100016, Z, 0, -1" in text
