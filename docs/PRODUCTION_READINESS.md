# Production Readiness

## Current Status (overview)

- Backend
  - Auth: JWT Bearer via `require_user`. Local/test/ci allows stub user; staging/prod enforce token.
  - Endpoints: Most routes secured; `/healthz` open; metrics mostly protected except `/metrics/health`.
  - AI: Enhanced endpoints available; OpenRouter integration optional (keys required); robust payload handling; fallback path.
  - OCR: Tesseract (swe+eng) in images; optional cloud OCR. Basic pre-processing.
  - Compliance: Rules framework present (R‑001/011/021/031/051 + VAT/PERIOD/DUP). Pre‑check path wired for enhanced flow.
  - Exports: SIE (MVP), PDFs. VAT report/declaration generation present.
- Frontend (Flutter Web/Mobile)
  - One‑tap capture/upload → OCR → enhanced autopost (fallback) → “Bokfört ✅”.
  - Web uses queue stub; mobile uses Isar queue.
  - API base configured via `API_BASE_URL`.
- Infra/DevOps
  - Dockerfiles include Tesseract; non‑root user. Terraform stubs exist. CI basic.

## Gaps to close before production (prioritized)

1) Security & Access Control
- RBAC roles + organization scoping enforced at DB/query level
- Rate limiting + brute‑force protection; per‑IP/origin policy
- File upload hardening: MIME/size caps, imagebomb protections, virus/malware scan
- Secret management: AWS Secrets Manager in all non‑local envs; key rotation

2) Identity & Auth
- BankID broker (Signicat or similar): init/callback + JWT issuance; recovery flows
- Admin authorization model (least privilege), audit of privileged actions

3) Data & Storage (WORM)
- S3 Object Lock (COMPLIANCE) with retention ≥ 7 år, legal hold path
- Lifecycle policies, region enforcement (SE/EU), cross‑region backup
- Document hashing/dedup at ingest; duplicate detection surfaced in UI

4) AI & Automation Quality
- LLM provider(s) with cache (Redis) and cost guardrails
- Swedish KB/RAG for Skatteverket/BFN; evaluation corpus; acceptance thresholds
- Learning loop from user corrections; vendor embeddings with pgvector

5) Observability & Operations
- OTEL traces/metrics/logs to Grafana/Loki/Tempo; dashboards and SLOs
- Alerts for OCR/AI failures, queue depth, automation rate, compliance health
- Runbooks (incident, secret rotation, BankID outage, storage failures)

6) Integrations
- Fortnox: OAuth, token persistence, sync jobs, retries & backoff
- Bolagsverket: XBRL + e‑inlämning path (staging → prod)
- Bankfeeds (Bankgirot/PSD2) roadmap

7) Testing & Quality
- Integration/E2E tests: upload→OCR→autopost→compliance→export (golden outputs)
- Property tests for SIE/VAT; load tests to 1k req/h; fuzz uploads
- Security testing (SAST/DAST), dependency scanning, SBOM

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
- [ ] RBAC + org scoping on queries/services
- [ ] CORS restricted to allowed origins
- [ ] Malware scan on uploads; MIME/size enforcement
- [ ] S3 Object Lock retention tested; delete denied; legal hold path
- [ ] OTEL dashboards: OCR p95, automation rate, compliance score, error rate
- [ ] LLM cache + cost guard in place; fallback flag works
- [ ] BankID integration e2e in staging
- [ ] Fortnox OAuth + sync job reliability
- [ ] CI gates: tests + coverage + lint

## Step‑by‑step rollout (4 weeks)

- Week 1: RBAC/org scoping, rate limiting, CORS tightening, malware scan; Redis cache; CI gates
- Week 2: BankID broker integration; Fortnox OAuth + token store; S3 Object Lock verification
- Week 3: RAG/KB (Skatteverket), LLM cache + cost guards, dashboards/alerts
- Week 4: E2E/perf/security tests; runbooks; prod cutover checklist

## Tokenless local dev

- No token required in `local/test/ci` to simplify development; staging/prod require Bearer tokens.
