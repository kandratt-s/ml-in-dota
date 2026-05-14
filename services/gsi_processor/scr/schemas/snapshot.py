from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EnemyPositionSnapshot(BaseModel):
    """Enemy position and last-seen timing information."""
    model_config = ConfigDict(extra="forbid")

    enemy_last_seen_time: int = Field(default=0, ge=0)
    enemy_last_seen_x: int
    enemy_last_seen_y: int


class SnapshotState(BaseModel):
    """Stores only enemy position/timing data keyed by hero name."""
    model_config = ConfigDict(extra="forbid")

    enemies: dict[str, EnemyPositionSnapshot] = Field(default_factory=dict)
