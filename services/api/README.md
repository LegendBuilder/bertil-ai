# Bertil API – Dev Guide

## Quickstart

1) Create `.env` in repo root:

```
CORS_ALLOW_ORIGINS=*
JWT_SECRET=change-me
OCR_PROVIDER=stub
# LLM / OpenRouter
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
LLM_TEMPERATURE=0.1
LLM_MODEL=meta-llama/llama-3.1-70b-instruct:free
# Optional: enable fallback only when ready
LLM_FALLBACK_ENABLED=false
# Supabase (private bucket)
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_BUCKET=originals
SUPABASE_STORAGE_PUBLIC=false
# Database (Supabase)
DATABASE_URL=postgresql+psycopg://postgres:<password>@db.<proj>.supabase.co:5432/postgres
```

2) Install and run:

```
pip install -r services/api/requirements.txt
python -m uvicorn services.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

## Migrations

```
alembic -c services/api/alembic.ini upgrade head
```

## Tests

```
pytest -q
```

## Optional OCR Queue

Enable Redis-backed OCR queue by setting `OCR_QUEUE_URL=redis://localhost:6379/0` and running the worker:

```
python -m services.api.app.ocr_worker
```

API will enqueue on `/documents/{id}/process-ocr` and poll for up to ~5s.

## Vendor Embeddings (pgvector)

Enable the `vector` extension in Postgres (migration attempts automatically). Seed a small dictionary:

```
curl -X POST http://127.0.0.1:8000/admin/seed/vendors
```

Auto-post will consult the dictionary before rule-based mapping.


