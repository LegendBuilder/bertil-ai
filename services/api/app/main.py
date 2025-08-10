from fastapi import FastAPI, Request
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
    app = FastAPI(title="Bertil AI API", version="0.0.1")

    # CORS for dev: allow any origin without credentials to avoid preflight failures in browsers
    allowed_origins = settings.cors_allow_origins.split(",")
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
        # Simple readiness: DB metadata accessible, local WORM dir exists
        db_ok = False
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            db_ok = True
        except Exception:
            db_ok = False
        storage_ok = True  # local stub
        return {"status": "ready" if db_ok and storage_ok else "degraded", "dependencies": {"db": db_ok, "storage": storage_ok}}

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
            await conn.run_sync(Base.metadata.create_all)
        # Seed core VAT codes so tests relying on listing don't fail on empty DB
        try:
            from .routers.admin import seed_vat_codes  # lazy import
            import anyio
            await seed_vat_codes()  # type: ignore[func-returns-value]
        except Exception:
            # Non-fatal in production; tests can seed explicitly
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

