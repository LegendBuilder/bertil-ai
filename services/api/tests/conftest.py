import os
import sys

import pytest
import asyncio

from sqlalchemy import text as _text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession

try:
    # Import db and main modules to swap engine/session during tests
    from services.api.app import db as _db_mod  # type: ignore
    from services.api.app import main as _main_mod  # type: ignore
except Exception:  # pragma: no cover - import guard for non-api test contexts
    _db_mod = None  # type: ignore
    _main_mod = None  # type: ignore



def _ensure_repo_root_on_path() -> None:
    """Prepend repo root to sys.path so `import services.*` works in tests.
    This avoids needing editable installs during CI/local runs.
    """
    current_dir = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


_ensure_repo_root_on_path()


@pytest.fixture(autouse=True)
def _isolate_db(tmp_path, monkeypatch):
    """Isolate DB per test by swapping engine/session to a fresh sqlite file.

    Also purges volatile tables to avoid cross-test leakage.
    """
    db_path = tmp_path / "test_api_run.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("APP_ENV", "ci")
    monkeypatch.setenv("OCR_PROVIDER", "stub")

    if _db_mod is None or _main_mod is None:
        yield
        return

    new_engine: AsyncEngine = create_async_engine(db_url, future=True, echo=False)
    new_session_local = async_sessionmaker(new_engine, expire_on_commit=False, class_=AsyncSession)

    # Swap engine and sessionmaker on both modules to guarantee isolation
    _db_mod.engine = new_engine
    _db_mod.SessionLocal = new_session_local
    _main_mod.engine = new_engine

    async def _ensure_and_purge() -> None:
        async with new_engine.begin() as conn:
            try:
                from services.api.app.db import Base  # import metadata for create_all
                await conn.run_sync(lambda c: Base.metadata.create_all(bind=c))
            except Exception:
                pass
            for tbl in ("entries", "verifications", "compliance_flags", "audit_log", "period_locks", "bank_transactions"):
                try:
                    await conn.execute(_text(f"DELETE FROM {tbl}"))
                except Exception:
                    pass
        # Defensive: also purge default dev DB if it exists to avoid cross-test leakage
        try:
            default_engine = create_async_engine("sqlite+aiosqlite:///./bertil_local.db", future=True, echo=False)
            async with default_engine.begin() as dconn:
                for tbl in ("entries", "verifications", "compliance_flags", "audit_log", "period_locks", "bank_transactions"):
                    try:
                        await dconn.execute(_text(f"DELETE FROM {tbl}"))
                    except Exception:
                        pass
            await default_engine.dispose()
        except Exception:
            pass

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(_ensure_and_purge())

    try:
        yield
    finally:
        loop.run_until_complete(new_engine.dispose())
