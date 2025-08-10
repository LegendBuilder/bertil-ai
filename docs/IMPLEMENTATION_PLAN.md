# Implementation Plan (AI-first, Compliance-safe)

This plan delivers an accountant-grade experience with open‑source OCR, deterministic extraction, compliance rules, and a tiny LLM fallback only for low‑confidence edge cases. Originals are stored under WORM (S3 Object Lock).

## Phase 0 — Foundations
- Env & secrets
  - [x] Wire config readers (.env autoload)
  - [ ] Add `.env.example` committed (template provided in README; repo ignore previously blocked root file)
  - [x] Document Ops procedures (API README)
- Database
  - [x] Alembic scaffolding + initial migration from current SQLAlchemy models
  - [x] Target: Postgres (Supabase dev), SQLite for tests
  - [x] Indices on: `documents.hash_sha256`, `verifications.immutable_seq`, FKs
- CI
  - [x] GitHub Actions: tests for Python + Flutter analyze/tests
  - [x] Lint (ruff) + coverage gates
  - [ ] Branch protection

## Phase 1 — Capture & Storage
- S3 Object Lock ingest (production path)
  - [x] S3 path + optional retention (stubbed, env-driven)
  - [x] Private storage friendly: Supabase signed URLs + server proxy/thumbnail
- Thumbnails
  - [x] Server‑side thumbnail generation (Pillow) + `/documents/{id}/thumbnail`
  - [x] Cache headers/ETag + 304 handling; lifecycle policy docs

## Phase 2 — OCR Service (open‑source)
- Tesseract worker
  - [x] Tesseract adapter (swe+eng) with preprocessing (grayscale/autocontrast/denoise/sharpen)
  - [x] Worker + queue (Redis) baseline; autoscaling rules, p95 targets pending
- Queue & autoscaling
  - [x] Dev queue + worker + metric `/metrics/ocr`
- API integration
  - [x] FastAPI endpoint processes OCR; OTEL span added
  - [ ] Metrics: queue depth/failures (OCR)

## Phase 3 — Extraction & Mapping
- Deterministic extractor
  - [x] Regex/heuristics for date/total/vendor
- Vendor/category mapping
  - [x] pgvector table & seed endpoint; embedding lookup on autopost
  - [~] Replace stub embeddings with MiniLM; persist vectors via pgvector (provider toggle implemented; install to enable)
- Explainability
  - [x] Explainability sidecar; UI reason strings

## Phase 4 — Compliance & Ledger
- Rules R‑001/011/021/031/051
  - [x] Compute + persist; unit tests added
- CTAs
  - [x] Home chips wired with optimistic actions
- Corrections
  - [x] Endpoints implemented + UI

## Phase 5 — Exports & Reports
- SIE 1–4 + 5 completion; verification PDF list
  - [x] SIE export; Verifications PDF; VAT report JSON/PDF; momsdeklarationsrutor i UI; UI‑knappar

## Phase 6 — UX polish (continuous)
- Coachmarks (first‑run), skeletons, grid thumbs, optimistic nav (done/ongoing)
- [x] A11y sweep; skeletons. Bank‑UI: Semantics på transaktioner och förslag, fokusordning. Kortkommando‑översikt (`?`) i Bank/Rapporter/Dokument/Inbox.
  - Inbox: berikade förklaringar per uppgiftstyp, Semantics på list‑rader och bulk‑knappar, Tab/Shift+Tab fokusordning, synliga fokusramar.
  - Dashboard: CTA “Granska (N)” när uppgifter väntar; kortkommando `G` till Inbox.

## Phase 7 — Observability & Safety
- OTEL traces/metrics/logs (Grafana/Loki/Tempo or local)
  - [~] Traces: OCR span; request-id middleware planned
  - [ ] DLP allow-list logger; alarms

## Phase 8 — Security & Auth
- BankID broker (Signicat): init/status/callback behind feature flag
  - [x] BankID stub; JWT issuance
  - [ ] Broker integration; mTLS/TLS; pgcrypto tokenization (users: personnummer via pgcrypto, tokenization)

## Phase 9 — LLM Fallback (optional, low‑confidence only)
- Micro‑client (Claude/GPT) with strict JSON schema
  - [ ] Deferred behind feature flag

## Phase 10 — E2E & Performance
- Golden dataset of Swedish receipts (field‑level F1 targets)
  - [ ] Dataset + benchmarks; load tests

---

## Task Breakdown (track as checklist)

- [x] Phase 0: Env/Secrets, Alembic migrations, CI workflows (base)
- [x] Phase 1: S3/Supabase upload, signed URLs/proxy, thumbnails endpoint
- [x] Phase 2: Tesseract adapter + OCR integration (worker pending)
- [x] Phase 3: Extractor + explainability (embeddings pending)
- [x] Phase 4: Rules + CTAs + corrections end‑to‑end
- [x] Phase 5: SIE/PDF + VAT report; reports UI
- [~] Phase 6: UX polish & A11y sweep
- [~] Phase 7: OTEL/Logs/Alerts (traces partial)
- [ ] Phase 8: BankID broker flow; security hardening
- [ ] Phase 9: LLM fallback micro‑client (feature‑flagged)
- [ ] Phase 10: E2E tests, performance budget verification


---

## Increment: Bank rec improvements + VAT declaration (this change)

- Backend (FastAPI)
  - Added filters, bulk accept and settlement flows in `services/api/app/routers/bank.py`:
    - `GET /bank/transactions` now supports `unmatched|matched`, `q`, `date_from|date_to`, `amount_min|max`.
    - `POST /bank/transactions/bulk-accept` to accept multiple matches.
    - `POST /bank/transactions/{id}/settle` to create AR/AP settlement verification (uses `settings.default_settlement_account`).
  - Added open items endpoint in `services/api/app/routers/verifications.py`:
    - `GET /verifications/open-items?type=ar|ap&counterparty=…` aggregates 1510/2440 balances.
  - Extended VAT declaration mapping in `services/api/app/routers/reports.py`:
    - RC/EU-RC codes excluded from base 05–07; rely on 2615/2645 impact.
    - `GET /reports/vat/declaration/file` behind `settings.skv_file_export_enabled` returns CSV for pilot.
  - Exposed config in `services/api/app/config.py`: `default_settlement_account`, `skv_file_export_enabled`.
  - `services/api/app/routers/verifications.py`: `VerificationIn` accepts `vat_code` and persists to `verifications.vat_code`.
  - Tests:
    - `services/api/tests/test_bank_import.py`: filters + bulk accept.
    - `services/api/tests/test_bank_settlement.py`: AR settlement flow.
    - `services/api/tests/test_reports_sie_compliance.py`: asserts VAT boxes present.

- Flutter (Web/Mobile)
  - `apps/mobile_web_flutter/lib/features/bank/data/bank_api.dart`: added `bulkAccept` and `settle` methods.
  - `apps/mobile_web_flutter/lib/features/bank/ui/reconcile_page.dart`: added A11y labels, “Avräkna” button for settlement, refresh action.
  - `apps/mobile_web_flutter/lib/features/reports/ui/reports_page.dart`: polished Semantics labels for VAT boxes.

- Docs
  - `docs/ARCHITECTURE.md`: updated Bank/VAT endpoints and metrics.
  - `docs/IMPLEMENTATION_PLAN.md`: ticked Phase 11/12 items and clarified remaining work.


## Phase 11 — Bank ingestion & reconciliation (local‑first)
- Data model & endpoints
  - [x] Table `bank_transactions(id, date, amount, currency, description, counterparty_ref, import_batch_id, matched_verification_id)`
  - [x] POST `/bank/import` (CSV/CAMT.053); GET `/bank/transactions` with filters (unmatched|matched, q, date_from|date_to, amount_min|max)
  - [x] GET `/bank/transactions/{id}/suggest`; POST `/bank/transactions/{id}/accept`; POST `/bank/transactions/bulk-accept`
  - [x] POST `/bank/transactions/{id}/settle` to create AR/AP settlement (1930 vs 1510/2440) and mark matched
- Matching engine MVP
  - [x] Rules: amount/date tolerance + text similarity (token overlap); limit by date window
  - [ ] Embeddings (pgvector) for description/vendor boost (behind provider flag)
- UI
  - [x] `Stäm av konto` screen: show unmatched lines, suggestions, accept + settle actions; A11y labels
  - [x] Bulk select/accept toolbar and search filter
- Tests/DoD
  - [x] CSV fixtures and endpoint tests for import/list/suggest/accept/bulk-accept
  - [x] Settlement happy-path test (AR)
  - [ ] Settlement happy-path test (AP)

## Phase 12 — VAT engine (codes & reverse charge)
- Model & logic
  - [x] Table `vat_codes`; `vat_code` on verifications; RC codes seeded (RC25, EU-RC-SERV)
  - [x] Reverse charge postings supported in autopost via `build_entries_with_code`
- Reports & compliance
  - [x] VAT return endpoint; momsdeklaration `/reports/vat/declaration` with boxes 05–07, 30–32, 48–49; RC via 2615/2645 impact
  - [x] Compliance rules: `R-RC` and `R-VATCODE` implemented
- UI
  - [x] VAT code selector in `DocumentDetail`; declaration boxes shown in Reports
- Tests/DoD
- [x] Basic tests for codes listing and declaration boxes present
- [x] Snapshot/value tests for declaration mapping inkl. representation/drivmedel och RC/EU; OSS low/high summeras; måltäcke ≥ 80% på VAT‑moduler

## Phase 13 — SIE import & period close
- Import
  - [ ] `POST /imports/sie` → parse 1–4+5 → persist; idempotent
- Closing
  - [x] `POST /period/close` (lock period); `GET /period/status`
  - [x] Enforcement in `create_verification` (403 when locked)
  - [ ] Accrual templates & guided checklist
- UI
  - [ ] Reports: “Import SIE”; Closing checklist with statuses
- Tests/DoD
  - [ ] Fixtures; E2E import creates expected balances; period lock prevents new postings

## Phase 14 — E‑invoice (Peppol BIS offline)
- Backend
  - [ ] Generate BIS Billing 3 XML from AP/AR objects; parse inbound BIS to AP invoice draft
- UI
  - [ ] Upload BIS → preview → create AP invoice + suggested postings; export BIS from invoice
- Tests/DoD
  - [ ] XML fixtures; round‑trip generate/parse parity tests

## Phase 15 — Ingestion channels & UX/A11y polish
- Ingestion
  - [~] Email IMAP connector stub → `documents` with SHA‑256 de‑dup; sender rules (flag `EMAIL_INGEST_ENABLED=false`)
  - [x] Web drop‑zone under flag (web-only; ENABLE_DROPZONE)
- A11y/UX
  - [~] Sweep semantics & focus order across all pages; keyboard shortcuts on web; glare overlay on camera (delvis implementerat: Semantics, FocusTraversalGroup, skeletoner)
- Tests/DoD
  - [x] Widget test for dropzone placeholder; Patrol E2E pending

## Phase 16 — Observability & Acceptance SLOs
- Metrics & alarms
  - [x] `/metrics/flow` med photo→posted tider (p95, samples)
  - [x] Alarm stubs: /metrics/alerts (OCR queue depth, failure counters)
- CI gates
  - [x] Acceptance smoke med budget (load_test --budget), coverage‑trösklar höjda till 75%

---

---

## Definition of Done (for new phases)
- Bank rec: import → suggest → one‑click clear; tests pass; demo sample bank lines cleared
- VAT engine: code assigned in UI; reverse‑charge postings emitted; return JSON matches expectations
- SIE import/close: import fixture; lock period; exports still pass; tests green
- E‑invoice: BIS XML generate/parse parity; AP invoice draft created from BIS; unit tests green
- Ingestion/a11y: email ingest creates documents; drop‑zone works; a11y checks across pages
- Observability: SLO metrics exposed; CI acceptance step runs and enforces minimal budget


## Phase 17 — Fortnox Ingest (bridge for adoption)
- Backend
  - [ ] Real Fortnox client (OAuth code→token; retries/backoff; pagination; ETags)
  - [ ] Endpoints: Account Charts, Accounts, Customers
  - [ ] Files: Archive and File Attachments (list/retrieve)
  - [ ] Idempotent sync job per tenant; SHA‑256 de‑dup to `documents`; source back‑links
  - [ ] Config flags: `fortnox_enabled`, `fortnox_client_id/secret/redirect_uri`
- Tests/DoD
  - [ ] Fixtures/mocks for endpoints; pagination/backoff tested; mapping snapshot tests

## Phase 18 — Autopilot Agents (graph + guardrails)
- Orchestrator
  - [ ] Graph (Ingest→Classify→Extract→Post→Reconcile→VAT) with confidence thresholds
  - [x] Review Inbox backend (queue/list/complete)
  - [ ] Per-node OTEL spans and counters; audit logs
- Tests/DoD
  - [ ] Graph tool unit tests; end‑to‑end run queues low‑confidence tasks, posts high‑confidence

## Phase 19 — ML Uplift (safe, explainable)
- Vendor mapping: MiniLM embeddings + classifier (fallback to RapidFuzz); pgvector storage
- Bank matcher: feature model (date/amount/text)
- VAT code classifier: SE25/12/06 + EU/RC with calibrated probabilities
- Tests/DoD: offline eval; drift checks; explanation snapshots

## Phase 20 — VAT SKV File
- Builder for SKV file, boxes 05–07, 30–32, 48, 49; RC via 2615/2645
- Snapshot tests; gated behind `skv_file_export_enabled`

## Phase 21 — Bank Feeds (flagged)
- PSD2 aggregator integration behind `bank_feeds_enabled`; idempotent import; alarms

## Phase 22 — Peppol BIS (offline → cert)
- Strict schema validation; inbound→AP draft; outbound from AR; fixtures and parity tests

## Phase 23 — Autopilot Inbox UI (dead‑simple)
- Flutter `InboxPage`: list tasks, bulk Approve/Undo, explainability, keyboarding
- Bank: saved filters (date/amount) + "Accept/Settle all safe"; Documents: "Post all safe"


