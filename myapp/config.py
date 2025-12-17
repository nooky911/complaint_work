from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 540

    FILE_STORAGE_PATH: str = "/app/storage"

    model_config = SettingsConfigDict(env_file=".env")

    def get_db_url(self, use_async: bool = True):
        driver = "asyncpg" if use_async else "psycopg2"
        return f"postgresql+{driver}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
