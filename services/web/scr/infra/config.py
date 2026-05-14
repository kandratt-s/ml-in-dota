from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Redis configuration - uses Docker service names in container environment
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    # HTTP request configuration
    REQUEST_TIMEOUT_SECONDS: float = 10.0

    # Inference service configuration - uses Docker service name in container environment
    INFERENCE_SERVICE_URL: str | None = "http://inference:8000"

    # Map and grid configuration
    MAP_PATH: str = "assets/600px-Gamemap_7.40_minimap_dota2_gameasset.png"

    XMIN: int = -9400
    XMAX: int = 8000
    YMIN: int = -8500
    YMAX: int = 8500
    CELLS: int = 32

    # Streamlit configuration
    REFRESH_INTERVAL_SECONDS: float = 1.0
    MAX_REFRESH_RATE_SECONDS: float = 5.0

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()