from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InferenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
