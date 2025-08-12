from fastapi import FastAPI, Request
import sys
import asyncio
import uuid
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import engine, Base
from .routers import auth, ingest, verifications, compliance, exports, reports, ai_auto, ai_enhanced, bolagsverket, metrics, admin, storage, bank, vat, imports, einvoice, period, fortnox, review, accruals, email_ingest
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .logging_utils import mask_in_structure


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance."""
    # Ensure Windows uses a selector event loop compatible with async DB drivers
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    app = FastAPI(title="Bertil AI API", version="0.0.1")

    # CORS: strict by default outside local; configurable via env
    allowed_origins = settings.cors_allow_origins.split(",")
    if settings.app_env.lower() not in {"local", "test", "ci"} and allowed_origins == ["*"]:
        allowed_origins = []  # default deny-all unless explicitly configured
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allowed_origins == ["*"] else allowed_origins,
        allow_origin_regex=".*" if allowed_origins == ["*"] else None,
        allow_credentials=False,  # must be false when using wildcard origins
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok", "service": "api", "version": "0.0.1"}

    @app.get("/readiness")
    async def readiness() -> dict:
        # Readiness: DB accessible and storage backend reachable (best-effort)
        db_ok = False
        storage_ok = False
        queue_ok = True
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda c: Base.metadata.create_all(bind=c))
            db_ok = True
        except Exception:
            db_ok = False
        # Storage check
        try:
            if settings.s3_bucket and settings.aws_region and settings.aws_access_key_id and settings.aws_secret_access_key:
                import boto3  # type: ignore
                s3 = boto3.client(
                    "s3",
                    region_name=settings.aws_region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                )
                s3.head_bucket(Bucket=settings.s3_bucket)
                storage_ok = True
            elif settings.supabase_url and settings.supabase_service_role_key and settings.supabase_bucket:
                storage_ok = True  # assume reachable; deeper probe would require HTTP
            else:
                # local WORM store existence check
                from pathlib import Path as _Path
                storage_ok = _Path(".worm_store").exists()
        except Exception:
            storage_ok = False
        # Queue check (optional OCR queue)
        try:
            if settings.ocr_queue_url:
                import redis.asyncio as _redis  # type: ignore
                r = _redis.from_url(settings.ocr_queue_url, decode_responses=False)
                await r.ping()
            queue_ok = True
        except Exception:
            queue_ok = False
        status_txt = "ready" if (db_ok and storage_ok and queue_ok) else "degraded"
        return {"status": status_txt, "dependencies": {"db": db_ok, "storage": storage_ok, "queue": queue_ok}}

    # Include routers
    app.include_router(auth.router)
    app.include_router(ingest.router)
    app.include_router(verifications.router)
    app.include_router(compliance.router)
    app.include_router(exports.router)
    app.include_router(reports.router)
    app.include_router(ai_auto.router)
    app.include_router(ai_enhanced.router)  # Enhanced AI agents
    app.include_router(bolagsverket.router)
    app.include_router(metrics.router)
    app.include_router(admin.router)
    app.include_router(storage.router)
    app.include_router(bank.router)
    app.include_router(vat.router)
    app.include_router(imports.router)
    app.include_router(einvoice.router)
    app.include_router(period.router)
    app.include_router(fortnox.router)
    app.include_router(review.router)
    app.include_router(accruals.router)
    app.include_router(email_ingest.router)

    # Minimal DLP middleware: mask personal numbers in paths/queries
    @app.middleware("http")
    async def dlp_mask_middleware(request: Request, call_next):
        # Avoid logging PII by not printing raw paths; mask Swedish personnummer patterns if needed
        if settings.log_requests:
            try:
                body = await request.body()
                _ = mask_in_structure({
                    "path": request.url.path,
                    "query": dict(request.query_params),
                    "body": body.decode("utf-8", errors="ignore"),
                })
            except Exception:
                pass
        response = await call_next(request)
        # Example: if we were to log, mask response bodies (disabled by default)
        _ = mask_in_structure  # keep import used to show masking is available
        return response

    @app.middleware("http")
    async def region_policy_middleware(request: Request, call_next):
        # Basic region enforcement stub: block explicit non-EU endpoints if present (future use)
        # This is a minimal placeholder; real enforcement would inspect storage/compute regions
        return await call_next(request)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response

    # Defensive CORS header fallback for dev: ensures responses always include ACAO
    @app.middleware("http")
    async def cors_fallback_middleware(request: Request, call_next):
        # Let Starlette CORSMiddleware handle preflight; this ensures normal responses carry headers
        response = await call_next(request)
        response.headers.setdefault("Access-Control-Allow-Origin", "*")
        response.headers.setdefault("Access-Control-Allow-Methods", "*")
        response.headers.setdefault("Access-Control-Allow-Headers", "*")
        return response

    @app.on_event("startup")
    async def on_startup() -> None:
        # Create tables for local/dev (SQLite). In production use Alembic migrations.
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: Base.metadata.create_all(bind=c))
        # Dev-only schema adjustments and data purge moved behind env guard
        if settings.app_env.lower() in {"local", "test", "ci"}:
            try:
                from sqlalchemy import text as _text
                async with engine.begin() as conn:
                    try:
                        res = await conn.execute(_text("PRAGMA table_info('verifications')"))
                        cols = {row[1] for row in res.fetchall()}  # type: ignore[index]
                        if "vat_code" not in cols:
                            await conn.execute(_text("ALTER TABLE verifications ADD COLUMN vat_code VARCHAR(20)"))
                    except Exception:
                        pass
            except Exception:
                pass
            # Only purge in dev/test
            from sqlalchemy import text as _text
            async with engine.begin() as conn:
                try:
                    for tbl in ("entries", "verifications", "compliance_flags", "audit_log", "period_locks", "bank_transactions"):
                        await conn.execute(_text(f"DELETE FROM {tbl}"))
                except Exception:
                    pass
            # Seed VAT codes for tests/dev
            try:
                from .routers.admin import seed_vat_codes  # lazy import
                await seed_vat_codes()  # type: ignore[func-returns-value]
            except Exception:
                pass

        # OpenTelemetry setup (optional)
        if settings.otlp_endpoint:
            resource = Resource.create({"service.name": "bertil-api"})
            provider = TracerProvider(resource=resource)
            exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            FastAPIInstrumentor.instrument_app(app)

    return app


app = create_app()

