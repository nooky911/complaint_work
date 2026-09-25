from pydantic import model_validator
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

    FILE_STORAGE_PATH: str = "./storage"

    CORS_ORIGINS: str = "http://localhost:5173,http://91.184.246.250:3333"

    # Подключение к Oracle Omega
    ORACLE_HOST: str | None = None
    ORACLE_PORT: int | None = None
    ORACLE_SERVICE: str | None = None
    ORACLE_USER: str | None = None
    ORACLE_PASSWORD: str | None = None
    OMEGA_SYNC_ENABLED: bool = False
    OMEGA_SYNC_HOUR: int = 2
    OMEGA_SYNC_MINUTE: int = 0
    OMEGA_SYNC_REQUEST_DELAY_SECONDS: float = 0.25

    @model_validator(mode="after")
    def validate_omega_settings(self) -> "Settings":
        """Требует параметры Oracle только при включённой синхронизации"""
        if self.OMEGA_SYNC_ENABLED:
            required = (
                "ORACLE_HOST",
                "ORACLE_PORT",
                "ORACLE_SERVICE",
                "ORACLE_USER",
                "ORACLE_PASSWORD",
            )
            missing = [name for name in required if not getattr(self, name)]
            if missing:
                raise ValueError(
                    "Для синхронизации Omega не заданы параметры: "
                    + ", ".join(missing)
                )
        return self

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

    @property
    def oracle_dsn(self) -> str:
        """Собирает Oracle Easy Connect DSN для подключения к Omega"""
        if not self.ORACLE_HOST or not self.ORACLE_PORT or not self.ORACLE_SERVICE:
            raise ValueError("Не заданы параметры подключения к Oracle Omega")
        return f"{self.ORACLE_HOST}:{self.ORACLE_PORT}/{self.ORACLE_SERVICE}"


settings = Settings()
