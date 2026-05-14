from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InferenceRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    record_id: str = Field(..., min_length=1, description="Unique record identifier")
    payload: dict[str, Any] = Field(default_factory=dict, description="Raw payload data")


class InferenceStreamMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    stream_id: str = Field(..., min_length=1, description="Redis stream entry id")
    record: InferenceRecord = Field(..., description="Validated inference record")


class InferenceBatchItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    record_id: str = Field(..., min_length=1, description="Unique record identifier")
    features: dict[str, Any] = Field(default_factory=dict, description="Flattened features for model input")
    raw_payload: dict[str, Any] = Field(default_factory=dict, description="Original payload before processing")


class InferenceResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    record_id: str = Field(..., min_length=1, description="Unique record identifier")
    death_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted death probability [0, 1]")
    model_backend: str = Field(..., min_length=1, description="Name of the model backend used")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the prediction")

    @field_validator("death_probability")
    @classmethod
    def validate_probability(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("death_probability must be between 0 and 1")
        return v