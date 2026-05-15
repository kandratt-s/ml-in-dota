from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: SecretStr
    TOKEN_SECRET: str
    DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: SecretStr

    INFERENCE_INPUT_QUEUE: str = "inference:input"

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD.get_secret_value()}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    XMIN: int
    XMAX: int
    YMIN: int
    YMAX: int
    CELLS: int

    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    LOCAL_DATA: Path = BASE_DIR / "local_data"
    ITEMS_JSON: Path = LOCAL_DATA / "items.json"
    HERO_STATS_JSON: Path = LOCAL_DATA / "heroes.json"
    ABILITIES_JSON: Path = LOCAL_DATA / "abilities.json"
    HERO_NAMES_JSON: Path = LOCAL_DATA / "heroNames.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()