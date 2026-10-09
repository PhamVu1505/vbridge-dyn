"""Midas time-dependent material blocks."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from vbridge_dyn.core.schemas.bridge import Bridge
from vbridge_dyn.core.schemas.project import Project
from vbridge_dyn.core.schemas.properties import Material


@dataclass(frozen=True)
class _TdmLink:
    material_id: int
    tdm_name: str
    fck_kn_m2: float


def build_time_dependent_concrete_lines(
    project: Project,
    bridge: Bridge,
    material_ids: dict[str, int],
    warnings: list[str],
) -> list[str]:
    """Build CEB-FIP creep/shrinkage material links for concrete."""
    config = project.targets.midas_civil.time_dependent_concrete
    if not config.enabled:
        return []

    links: list[_TdmLink] = []
    include = set(config.include_materials)
    for material in bridge.materials:
        if material.kind != "CONC":
            continue
        if include and not {material.id, material.name, material.grade or ""} & include:
            continue
        strength = _tdm_strength(material, config.strengths)
        if strength is None:
            warnings.append(
                f"Material {material.id}: không suy ra được fck cho TDM; bỏ qua TDM-LINK."
            )
            continue
        links.append(
            _TdmLink(
                material_id=material_ids[material.id],
                tdm_name=_midas_name(material.id, limit=16),
                fck_kn_m2=strength,
            )
        )

    if not links:
        warnings.append("time_dependent_concrete.enabled=true nhưng không có vật liệu CONC hợp lệ.")
        return []

    lines = [
        "*TDM-TYPE    ; Time Dependent Material (creep & shrinkage)",
        "; NAME=NAME, CODE, STR, HU, MSIZE, CTYPE, AGE              ; CODE=CEB",
    ]
    for link in links:
        lines.append(
            f"   NAME={link.tdm_name}, {config.code}, {_num(link.fck_kn_m2)}, "
            f"{_num(config.relative_humidity_percent)}, {_num(config.notional_size)}, "
            f"{config.cement_type}, {_num(config.age_days)}, 0"
        )

    lines.extend(
        [
            "",
            "*TDM-ELAST    ; Time Dependent Material (Comp. Strength)",
            "; NAME=NAME, TYPE, CODE, STRENGTH, iCTYPE",
        ]
    )
    for link in links:
        lines.append(
            f"   NAME={link.tdm_name}, CODE, {config.elasticity_code}, {_num(link.fck_kn_m2)}, 2"
        )

    lines.extend(
        [
            "",
            "*TDM-LINK    ; Time Dependent Material Link",
            "; iMAT, TDM(creep/shrink), TDM(elast)",
        ]
    )
    for link in links:
        lines.append(f"   {link.material_id}, {link.tdm_name}, {link.tdm_name}")
    lines.append("")

    warnings.append(
        "Đã link time-dependent concrete cho "
        + ", ".join(f"{link.tdm_name}(mat {link.material_id})" for link in links)
        + "."
    )
    return lines


def _tdm_strength(material: Material, overrides: dict[str, float]) -> float | None:
    for key in (material.id, material.name, material.grade or ""):
        if key in overrides:
            return float(overrides[key])

    for text in (material.grade, material.id, material.name):
        if not text:
            continue
        match = re.search(r"C\s*(\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1)) * 1000.0
    return None


def _num(value: float) -> str:
    return f"{value:.10g}"


def _midas_name(value: str, *, limit: int) -> str:
    normalized = unicodedata.normalize("NFKD", value.replace(",", " ").strip())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = " ".join(ascii_text.split())
    if not cleaned:
        cleaned = "Unnamed"
    return cleaned[:limit]
