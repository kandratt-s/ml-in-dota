from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AUTH_BASE_URL: str = "http://localhost:8001/api/v1"
    REQUEST_TIMEOUT_SECONDS: float = 10.0

    MAP_PATH: str = "assets/600px-Gamemap_7.40_minimap_dota2_gameasset.png"

    XMIN: int = -9400
    XMAX: int = 8000
    YMIN: int = -8500
    YMAX: int = 8500
    CELLS: int = 32

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()