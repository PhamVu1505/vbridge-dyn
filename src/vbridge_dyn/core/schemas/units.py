"""Hệ đơn vị nội bộ SI; exporter (Midas/RM) đổi sang đơn vị target."""

from typing import Literal

from pydantic import BaseModel


class UnitSystem(BaseModel):
    """Nội bộ luôn dùng SI. Exporter chịu trách nhiệm convert.

    Midas Civil MCT thường dùng (kN, m, ton, s) hoặc (kN, m, kJ, C).
    RM Bridge thường dùng (kN, m, ton, s).
    """

    length: Literal["m"] = "m"
    force: Literal["N"] = "N"
    mass: Literal["kg"] = "kg"
    time: Literal["s"] = "s"
