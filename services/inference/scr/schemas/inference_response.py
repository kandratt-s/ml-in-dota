from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status: 'ok' or 'degraded'")
    redis_ready: bool = Field(..., description="Whether Redis is reachable")
    model_ready: bool = Field(..., description="Whether model is loaded and ready")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional status details")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("ok", "degraded", "error"):
            raise ValueError("status must be 'ok', 'degraded', or 'error'")
        return v


class ProcessBatchResponse(BaseModel):
    processed_items: int = Field(..., ge=0, description="Number of items processed")
    enqueued_results: int = Field(..., ge=0, description="Number of results enqueued")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional processing details")


class InferenceResponse(BaseModel):
    predictions: list[float] = Field(..., description="List of predictions")