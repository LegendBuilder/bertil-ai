from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "sqlite+aiosqlite:///./bertil_local.db"
    cors_allow_origins: str = "*"
    otlp_endpoint: str | None = None

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()  # type: ignore[call-arg]


