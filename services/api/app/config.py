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
    openrouter_api_key: str | None = None  # allow OPENROUTER_API_KEY in .env without validation error
    llm_extraction_threshold: float = 0.6
    llm_cache_url: str | None = None  # e.g., redis://localhost:6379/1
    llm_cache_ttl_hours: int = 24
    llm_budget_daily_usd: float = 1.0
    llm_budget_enforce: bool = False
    llm_cost_per_request_estimate_usd: float = 0.002
    # A/B routing
    llm_ab_test_enabled: bool = False
    llm_ab_primary_model: str | None = None
    llm_ab_secondary_model: str | None = None
    llm_ab_split_percent: int = 0  # 0..100
    
    # OpenRouter specific models
    llm_model: str | None = None
    llm_temperature: float = 0.1
    
    # Knowledge base
    kb_http_fetch_enabled: bool = False

    # Logging
    log_requests: bool = False

    # Embeddings
    embeddings_provider: str = "stub"  # options: stub | minilm

    # Banking & VAT
    default_settlement_account: str = "1930"  # default bank account used for settlements
    skv_file_export_enabled: bool = False  # disabled by default; enable after validation

    # Upload hardening
    upload_max_bytes: int = 15_000_000  # 15 MB default
    upload_allowed_mime: str = "image/jpeg,image/png"
    upload_allow_pdf: bool = False
    pdf_sanitize_enabled: bool = False

    # Rate limiting (naive, in-process)
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 120
    rate_limit_redis_url: str | None = None  # optional Redis for distributed limiting

    # Virus scan
    virus_scan_enabled: bool = False
    virus_scan_engine: str = "clamav"  # future use

    # WORM smoke test
    storage_smoketest_enabled: bool = False
    worm_test_object_prefix: str = "worm_test/"

    # Fortnox Integration
    fortnox_enabled: bool = False
    fortnox_stub: bool = True  # use stubbed client for tests/dev without external keys
    fortnox_client_id: str | None = None
    fortnox_client_secret: str | None = None
    fortnox_redirect_uri: str | None = None
    
    # BankID / broker placeholders (keys will be set via env/secrets in non-local)
    bankid_broker: str | None = None
    bankid_client_id: str | None = None
    bankid_client_secret: str | None = None
    bankid_redirect_uri: str | None = None
    bankid_environment: str = "test"

    # Email ingest (IMAP)
    email_ingest_enabled: bool = False
    email_ingest_stub: bool = True  # read from local folder .email_ingest_inbox
    email_imap_host: str | None = None
    email_imap_port: int = 993
    email_imap_user: str | None = None
    email_imap_password: str | None = None
    email_sender_rules_json: str | None = None  # JSON mapping sender->meta (e.g., {"invoices@x.com": {"type":"invoice"}})

    # Knowledge base (RAG) HTTP fetch toggle
    kb_http_fetch_enabled: bool = False


settings = Settings()  # type: ignore[call-arg]


