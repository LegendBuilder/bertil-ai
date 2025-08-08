from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import engine, Base
from .routers import auth, ingest, verifications, compliance, exports, reports
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
    def readiness() -> dict:
        # In Pass 3 we'll check DB/storage integrations.
        return {"status": "ready", "dependencies": {"db": "stub", "storage": "stub"}}

    # Include routers
    app.include_router(auth.router)
    app.include_router(ingest.router)
    app.include_router(verifications.router)
    app.include_router(compliance.router)
    app.include_router(exports.router)
    app.include_router(reports.router)

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

