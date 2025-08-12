## Driftsättning & Regionpolicy

- Regioner: primär `eu-north-1` (Stockholm), sekundär `eu-central-1` (Frankfurt). Endast SE/EU.
- Lagring: S3 Object Lock (COMPLIANCE) med retention ≥ 7 år, Legal Hold vid behov.
- Hemligheter: AWS Secrets Manager (JWT_SECRET m.fl.), annars ENV/`.secrets/` lokalt.

## Miljöer

- local: SQLite + lokal `.worm_store` + stub-OCR.
- staging: RDS Postgres, S3 med Object Lock, Textract/Vision i EU.
- prod: som staging men med minst 2 AZ, rotation av nycklar, branch-skydd hårt.

## Observability

- OTLP exporter (valfri) → Grafana Tempo/Loki/Prom.
- DLP/PII: inga personnummer i loggar (maskas i UI och centrala loggers har allow-list).

### KPIs
- `GET /metrics/kpi` – Automation attempts/success/rate per org och nivå, compliance pre/post blocks.
- `GET /metrics/flow` – P95 för foto→bokföring och senaste samples.
- `GET /metrics/alerts` – Samlar rate‑limit‑block, OCR‑kövarningar m.m.

## Policy (auth & CORS)

- `local/test/ci`: stub‑auth tillåten; CORS kan vara `*`.
- `staging/prod`: Bearer‑JWT krävs för alla skyddade endpoints; CORS måste vara låst till kända origin.

## Runbooks (kort)

- BankID‑störning: tillåt manuell demo‑login, fallback till stub endast i `local/test`.
- LLM‑fel/hög latens: slå av enhanced via feature flag; fallback till legacy `/ai/auto-post` fortsätter.
- S3 Object Lock delete‑fel: kontrollera retention/Legal Hold; följ WORM‑procedur.

## WORM smoke-test

- Endpoint: `POST /storage/worm/smoke-test` (prod/staging)
  - Skriver testobjekt under prefix `worm_test/` med COMPLIANCE retention (1 dag)
  - Försöker radera direkt och förväntar `AccessDenied` (delete denied)
  - Använd endast i kontrollerade miljöer

# Drift & observability

- IaC: Terraform (S3 Object Lock + KMS, RDS Multi‑AZ, OpenSearch, WAF/ALB, Secrets)
- CI/CD: GitHub Actions (lint/test/build)
- Observability: OpenTelemetry → Grafana
- Incident & loggning: centraliserad, PII-allow-list


