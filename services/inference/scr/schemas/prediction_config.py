from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PredictionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: Literal["boosting", "logreg"] = Field(default="boosting")
    time: Literal[1, 5, 10, 15, 20] = Field(default=10)
    interval: Literal[1, 3, 5] = Field(default=1)
    full_map: bool = Field(default=True)
