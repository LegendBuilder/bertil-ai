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

# Drift & observability

- IaC: Terraform (S3 Object Lock, RDS, OpenSearch, Secrets)
- CI/CD: GitHub Actions (lint/test/build)
- Observability: OpenTelemetry → Grafana
- Incident & loggning: centraliserad, PII-allow-list


