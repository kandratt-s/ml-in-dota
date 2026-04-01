from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: SecretStr

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD.get_secret_value()}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"


    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    BCRYPT_ROUNDS: int = 12  # выше = медленнее брутфорс, но дольше хэш
    # Максимум попыток входа до блокировки аккаунта
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    COOKIE_MAX_AGE: int = JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
    COOKIE_SECURE: bool = False

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    



    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()