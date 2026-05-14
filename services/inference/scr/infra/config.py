from pathlib import Path
import os
import socket

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # Queue names for input/output
    INFERENCE_INPUT_QUEUE: str = "inference:input"
    INFERENCE_OUTPUT_QUEUE: str = "inference:output"
    HEATMAP_RESULT_KEY: str = "heat_map"

    # Heatmap size
    CELLS: int = 32

    # Local data configuration
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    LOCAL_DATA: Path = BASE_DIR / "local_data"
    ITEMS_JSON: Path = LOCAL_DATA / "items.json"
    HERO_STATS_JSON: Path = LOCAL_DATA / "heroes.json"
    ABILITIES_JSON: Path = LOCAL_DATA / "abilities.json"

    # Model configuration
    MODEL_PATH: Path | None = Field(
        default=Path(__file__).resolve().parents[2] / "scr" / "infra" / "model.cbm",
        description="Path to the trained CatBoost model file",
    )

    # Worker settings
    BATCH_SIZE: int = 16
    POLL_INTERVAL_SECONDS: float = 1.0

    # Consumer group and worker identity
    CONSUMER_NAME: str = Field(
        default_factory=lambda: os.getenv("CONSUMER_NAME") or f"inference-worker-{socket.gethostname()}",
        description="Unique consumer name for Redis Streams consumer group",
    )

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @field_validator("MODEL_PATH", mode="before")
    @classmethod
    def normalize_model_path(cls, value: object) -> Path | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized or normalized in {".", "./"}:
                return None
            return Path(normalized)
        if isinstance(value, Path):
            if str(value).strip() in {"", ".", "./"}:
                return None
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()