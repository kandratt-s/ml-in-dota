from pydantic import BaseModel, Field
from datetime import datetime


class HeatmapResponse(BaseModel):
    version: int
    grid_size: int
    heat: list[list[float]]
    max_value: float
    updated_at: datetime
    session_active: bool