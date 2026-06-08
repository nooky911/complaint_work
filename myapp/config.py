from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 600

    PARTNER_ACCESS_NAMES: str = ""

    FILE_STORAGE_PATH: str = "/app/storage"

    CORS_ORIGINS: str = "http://localhost:5173,http://10.131.251.65:3333"

    @property
    def partner_access_list(self) -> set[str]:
        """Достает строку разрешенных имен для совместного редактирования из .env"""
        if not self.PARTNER_ACCESS_NAMES:
            return set()
        return {name.strip() for name in self.PARTNER_ACCESS_NAMES.split(",")}

    @property
    def cors_origins_list(self) -> list[str]:
        """Превращает строку из .env в список"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def get_db_url(self, use_async: bool = True) -> str:
        driver = "asyncpg" if use_async else "psycopg2"
        return f"postgresql+{driver}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
