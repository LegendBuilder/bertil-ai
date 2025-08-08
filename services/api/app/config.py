from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "sqlite+aiosqlite:///./bertil_local.db"
    cors_allow_origins: str = "*"
    otlp_endpoint: str | None = None
    jwt_secret: str = "dev-secret"
    jwt_issuer: str = "bertil-api"
    # OCR/AI provider configuration
    ocr_provider: str = "stub"  # options: stub | google_vision | aws_textract | tesseract
    google_credentials_json_path: str | None = None
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    tesseract_cmd: str | None = None

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()  # type: ignore[call-arg]


