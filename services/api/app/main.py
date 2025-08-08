from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import engine, Base
from .routers import auth, ingest, verifications, compliance, exports, reports, ai_auto
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance."""
    app = FastAPI(title="Bertil AI API", version="0.0.1")

    allowed_origins = settings.cors_allow_origins.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
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

    # Minimal DLP middleware: mask personal numbers in paths/queries
    @app.middleware("http")
    async def dlp_mask_middleware(request: Request, call_next):
        # Avoid logging PII by not printing raw paths; mask Swedish personnummer patterns if needed
        # We do not log here; this is a placeholder for central logger allow-list
        response = await call_next(request)
        return response

    @app.middleware("http")
    async def region_policy_middleware(request: Request, call_next):
        # Basic region enforcement stub: block explicit non-EU endpoints if present (future use)
        # This is a minimal placeholder; real enforcement would inspect storage/compute regions
        return await call_next(request)

    @app.on_event("startup")
    async def on_startup() -> None:
        # Create tables for local/dev (SQLite). In production use Alembic migrations.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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

