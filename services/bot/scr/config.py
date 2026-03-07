from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: SecretStr
    TOKEN_SECRET: str = "ml-in-dota-default-secret"
    DATABASE_URL: str
    

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()