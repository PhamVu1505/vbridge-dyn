"""Vị trí xuất kết quả (map sang node / element / track station)."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ResultStation(BaseModel):
    """Một vị trí xuất kết quả.

    Map qua một trong 3 target:
    - 'node': dùng `node_id` trực tiếp
    - 'element': nội suy giữa 2 node của element theo `element_eta` ∈ [0, 1]
    - 'track': cho `track_id` + `track_x` (m từ đầu track)
    """

    id: str
    name: str = ""
    target: Literal["node", "element", "track"] = "track"

    node_id: int | None = Field(default=None, ge=1)
    element_id: int | None = Field(default=None, ge=1)
    element_eta: float | None = Field(default=None, ge=0.0, le=1.0)
    track_id: str | None = None
    track_x: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="after")
    def _check_target_consistency(self) -> "ResultStation":
        if self.target == "node" and self.node_id is None:
            msg = "ResultStation target='node' phải có node_id"
            raise ValueError(msg)
        if self.target == "element" and (self.element_id is None or self.element_eta is None):
            msg = "ResultStation target='element' phải có element_id và element_eta ∈ [0,1]"
            raise ValueError(msg)
        if self.target == "track" and (self.track_id is None or self.track_x is None):
            msg = "ResultStation target='track' phải có track_id và track_x ≥ 0"
            raise ValueError(msg)
        return self
