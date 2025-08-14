# Production Readiness

## Current Status (overview)

- Backend
  - Auth: JWT Bearer via `require_user`. Local/test/ci allows stub user; staging/prod enforce token.
  - Endpoints: Most routes secured; `/healthz` open; metrics mostly protected except `/metrics/health`.
  - AI: Enhanced endpoints available; OpenRouter integration optional (keys required); robust payload handling; fallback path.
  - OCR: Tesseract (swe+eng) in images; optional cloud OCR. Basic pre-processing.
  - Compliance: Rules framework present (R‑001/011/021/031/051 + VAT/PERIOD/DUP). Pre‑check path wired for enhanced flow.
  - Exports: SIE (MVP), PDFs. VAT report/declaration generation present.
  - KPIs: Automation attempts/success/rate; compliance pre/post blocks; flow p95 histogram.
- Frontend (Flutter Web/Mobile)
  - One‑tap capture/upload → OCR → enhanced autopost (fallback) → “Bokfört ✅”.
  - Offline‑kö: Web (IndexedDB via idb_shim), Mobil (Isar). Replay med backoff, UI‑badge och `/settings/outbox` för hantering.
  - API base via `API_BASE_URL`.
- Infra/DevOps
  - Dockerfiles include Tesseract; non‑root user; qpdf/ClamAV for upload hardening.
  - Terraform: S3 Object Lock (COMPLIANCE) with KMS, RDS Multi‑AZ, WAF/ALB skeleton, OpenSearch, Secrets Manager.
  - CI: lint/tests, SBOM (pip‑audit/CycloneDX), SAST (CodeQL), DAST (ZAP), optional Trivy/Grype.
  - CD: blue/green workflow stub to flip ALB target group via Terraform.

## Gaps to close before production (prioritized)

1) Security & Access Control
- RBAC roles + organization scoping enforced at DB/query level
- Rate limiting + brute‑force protection; per‑IP/origin policy
- File upload hardening: MIME/size caps, magic-sniff, imagebomb protections, PDF sanitize (qpdf), virus/malware scan (ClamAV)
- Secret management: AWS Secrets Manager in all non‑local envs; key rotation

2) Identity & Auth
- BankID broker (Signicat or similar): init/callback + JWT issuance; recovery flows
- Admin authorization model (least privilege), audit of privileged actions

3) Data & Storage (WORM)
- S3 Object Lock (COMPLIANCE) with retention ≥ 7 år, legal hold path
- Lifecycle policies, region enforcement (SE/EU), cross‑region backup
- Document hashing/dedup at ingest; duplicate detection surfaced in UI

 4) AI & Automation Quality
 - LLM cache (Redis hooks) + budget guard; strict JSON schemas for extraction/tax/compliance/insights.
 - RAG KB loader supports local `kb/*.json`; weekly GH Action refresh (basic clean + diff). Acceptance tests in progress.
 - Learning loop: `AiFeedback` → `VendorEmbedding`; refresh scripts available.
 - A/B routing via env (model split). Grafana dashboard covers rate/latency/errors/cost per model.

 5) Observability & Operations
 - OTEL traces/metrics/logs to Grafana/Loki/Tempo; dashboards (`/metrics`, `/metrics/synthetic`) and SLOs.
 - KPI endpoints: `/metrics/kpi`, `/metrics/flow`, `/metrics/alerts`.
 - Dashboards: Flow p95, Automation KPIs, LLM A/B Results (includes success rate and cost), System Health.
 - Alerts: OCR queue depth, rate‑limit blocks; extensible.

6) Integrations
- Fortnox: OAuth, token persistence, sync jobs, retries & backoff
- Bolagsverket: XBRL + e‑inlämning path (staging → prod)
- Bankfeeds (Bankgirot/PSD2) roadmap

 7) Testing & Quality
 - E2E tests: upload→OCR→autopost→compliance→export.
 - Schema tests for LLM outputs.
 - Security testing (SAST/DAST), dependency scanning, SBOM in CI.

## Environment policy

- local: stub auth, SQLite/Dev S3, permissive CORS
- staging: JWT enforced, RDS Postgres, S3 Object Lock, SE/EU OCR providers, restricted CORS
- prod: like staging with multi‑AZ, backups, KMS, strict CORS, WAF/Rate limits

## Auth model

- Header: `Authorization: Bearer <jwt>`
- Local/test/ci: optional token returns stub identity
- Staging/prod: token required; admin endpoints require `role=admin`

## Readiness checklist

- [ ] JWT enforced in staging/prod for all protected routes
- [x] RBAC + org scoping on queries/services (documents/verifications/bank/review)
- [ ] CORS restricted to allowed origins
- [x] Upload hardening (MIME/magic, size caps, imagebomb, qpdf sanitize, ClamAV)
- [x] S3 Object Lock (COMPLIANCE) with KMS; bucket policy prevents deletes
- [x] Dashboards: OCR p95, automation rate, LLM A/B (success, latency, errors, cost)
- [x] LLM cache hooks + budget guard; strict schemas
- [ ] BankID e2e in staging (keys pending)
- [ ] Fortnox OAuth + sync job reliability
- [x] CI gates: tests + lint + SBOM + SAST/DAST
- [x] Offline queue (web IndexedDB / mobile Isar) with replay + UI badge and management screen

## Step‑by‑step rollout (4 weeks)

- Week 1: RBAC/org scoping, rate limiting, CORS tightening, malware scan; Redis cache; CI gates
- Week 2: BankID broker integration; Fortnox OAuth + token store; S3 Object Lock verification
- Week 3: RAG/KB (Skatteverket), LLM cache + cost guards, dashboards/alerts
- Week 4: E2E/perf/security tests; runbooks; prod cutover checklist

## Tokenless local dev

- No token required in `local/test/ci` to simplify development; staging/prod require Bearer tokens.
