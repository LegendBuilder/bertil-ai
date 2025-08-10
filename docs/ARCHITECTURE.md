# Arkitektur

Monorepo med Flutter-klient och FastAPI-backend. Infrastruktur via Terraform.

Komponenter

- Klient (Flutter Web/iOS/Android): Riverpod, go_router, Dio, Isar (offline/queue), camera/image_picker, pdfx, intl/freezed/json_serializable
  - A11y: Semantics på bilder/miniaturer, FocusTraversalGroup i nav, skeletoner vid laddning
- Backend (FastAPI): PostgreSQL + pgcrypto, S3 (Object Lock) för original, OCR (Tesseract, PaddleOCR fallback; Vision/Textract valfritt), AI/regler, OpenTelemetry

Append-only & spårbarhet

- `verifications` med `immutable_seq`
- `audit_log` med hashkedja och signatur

Observability

- OpenTelemetry (OTLP) → Grafana-stack

Supabase (valfritt)

- Kan användas för DB/Auth/Storage i dev/staging och för tumnaglar. Produktions-original lagras i S3 med WORM. BankID fortsatt via broker/ backend.


Nuvarande status (MVP)

- API
  - Ingest: `POST /documents`, `GET /documents`, `GET /documents/{id}`, `GET /documents/{id}/image|thumbnail` (med ETag/Cache-Control och 304-stöd), `POST /documents/{id}/process-ocr`
  - AI/Autopost: `POST /ai/auto-post` (vendor→BAS, momsberäkning, explainability sidecar)
  - Verifikationer: `POST /verifications`, `GET /verifications`, `GET /verifications/{id}`, `GET /verifications/by-document/{docId}`, `POST /verifications/{id}/reverse|correct-date|correct-document`
  - Compliance: `GET /compliance/summary`, `GET /compliance/verification/{id}`, `POST /compliance/verification/{id}/resolve` (inkl. R‑RC, förstärkt R‑011)
  - Rapporter/Export: `GET /trial-balance`, `GET /exports/sie`, `GET /exports/verifications.pdf`, `GET /reports/vat?period=YYYY-MM&format=json|pdf`, `GET /reports/vat/declaration`
  - Moms/VAT: `GET /vat/codes` (seed via `/admin/seed/vat`), `vat_code` på verifikationer; deklarationsrutor (05–07, 30–32, 48–49) inkl. RC via 2615/2645
  - Bank: `POST /bank/import` (CSV), `GET /bank/transactions` (filters: unmatched|matched, q, date_from|date_to, amount_min|max), `GET /bank/transactions/{id}/suggest`, `POST /bank/transactions/{id}/accept`, `POST /bank/transactions/bulk-accept`, `POST /bank/transactions/{id}/settle`
  - Importer: `POST /imports/sie` (MVP parser för #VER/#TRANS)
  - E‑faktura (offline): `POST /einvoice/generate`, `POST /einvoice/parse`
  - Auth: `POST /auth/bankid/init`, `GET /auth/bankid/status` (stub), JWT-utfärdare
  - Bolagsverket: `POST /bolagsverket/submit` (stub)
  - Hälsa/metrics: `GET /healthz`, `GET /readiness`, `GET /metrics/health`
- Lagring
  - Dev: Supabase Storage (privat bucket) med server-side proxy och thumbnails. URL:er kan vara signed/public beroende på konfig.
  - Prod: S3 WORM (Object Lock) planerad; stubbar för PUT/get finns, retention via env.
- OCR
  - Adapter: stub + Tesseract (swe+eng) med förbehandling (Otsu-binarisering, deskew, skärpning); valbar Redis-kö (`OCR_QUEUE_URL`) och arbetare (`app/ocr_worker.py`). Inline-läge om kö ej satt. P95 mäts i worker-span.
- Regler/ledger
  - Append-only verifikationer, hashkedja i `audit_log`. Regler R‑001/011/021/031/051 + R‑DUP + R‑VAT + R‑PERIOD. Flaggor persisteras och kan markeras som lösta.
- Klient (Flutter)
  - Login (BankID-stub + demo), Capture/Upload + offlinekö (Isar), Dokumentlista/detalj med OCR-overlay och "Varför" + VAT‑kodval, Dashboard med Trygghetsmätare och CTA:er, Verifikationer, Rapporter (SIE/PDF/Moms inkl. kod‑chips), Bank "Stäm av konto" (förslag + acceptera), Settings.
- CI & tests
  - GitHub Actions: API tester (pytest + coverage), Flutter `analyze`/`test`. E2E-API-test: upload→OCR→autopost→compliance→SIE/PDF/Moms.
- Observability & säkerhet
  - OTEL-span för OCR, request-id middleware, DLP-maskeringshjälpmedel. OCR-ködjup via `/metrics/ocr`.
  - Flödesmetrik: `/metrics/flow` visar photo→posted tider (p95, samples)

Kända TODOs (hög nivå)

- BankID broker-integration (Signicat) när access finns.
- S3 WORM i produktion (retentionvalidering, lifecycle, region-enforcement).
- Fristående OCR-worker/auto-skalning och mer robust pre-processing.
- Embeddings/pgvector för leverantörsmappning; a11y-svep; full OTEL till Grafana; säkerhetshärdning; LLM-fallback bakom feature flag.

