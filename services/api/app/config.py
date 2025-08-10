from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Auto-load from .env in repo root; case-insensitive keys
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    app_env: str = "local"
    database_url: str = "sqlite+aiosqlite:///./bertil_local.db"
    cors_allow_origins: str = "*"
    otlp_endpoint: str | None = None
    jwt_secret: str = "dev-secret"
    jwt_issuer: str = "bertil-api"
    # OCR/AI provider configuration
    ocr_provider: str = "stub"  # options: stub | google_vision | aws_textract | tesseract
    ocr_queue_url: str | None = None  # e.g., redis://localhost:6379/0 to enable async OCR
    ocr_queue_warn_threshold: int = 50
    google_credentials_json_path: str | None = None
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    s3_bucket: str | None = None
    s3_object_lock_retention_days: int | None = None
    tesseract_cmd: str | None = None
    allowed_regions: str = "SE,EU"
    # Supabase (optional)
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_bucket: str | None = "originals"
    supabase_storage_public: bool = True

    # LLM fallback (optional)
    llm_fallback_enabled: bool = False
    llm_provider: str | None = None  # e.g., openai/anthropic
    llm_api_key: str | None = None
    llm_extraction_threshold: float = 0.6

    # Logging
    log_requests: bool = False

    # Embeddings
    embeddings_provider: str = "stub"  # options: stub | minilm

    # Banking & VAT
    default_settlement_account: str = "1930"  # default bank account used for settlements
    skv_file_export_enabled: bool = False  # disabled by default; enable after validation

    # Fortnox Integration
    fortnox_enabled: bool = False
    fortnox_stub: bool = True  # use stubbed client for tests/dev without external keys
    fortnox_client_id: str | None = None
    fortnox_client_secret: str | None = None
    fortnox_redirect_uri: str | None = None

    # Email ingest (IMAP)
    email_ingest_enabled: bool = False
    email_ingest_stub: bool = True  # read from local folder .email_ingest_inbox
    email_imap_host: str | None = None
    email_imap_port: int = 993
    email_imap_user: str | None = None
    email_imap_password: str | None = None
    email_sender_rules_json: str | None = None  # JSON mapping sender->meta (e.g., {"invoices@x.com": {"type":"invoice"}})


settings = Settings()  # type: ignore[call-arg]


