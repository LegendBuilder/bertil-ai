# Arkitektur

Monorepo med Flutter-klient och FastAPI-backend. Infrastruktur via Terraform, lagring i SE/EU.

Komponenter

- Klient (Flutter Web/iOS/Android): Riverpod, go_router, Dio, Isar (offline/queue), camera/image_picker, pdfx, intl/freezed/json_serializable
- Backend (FastAPI): PostgreSQL + pgcrypto, OpenSearch, S3 (Object Lock), OCR (Vision/Textract + Tesseract fallback), AI/regler, OpenTelemetry

Append-only & spårbarhet

- `verifications` med `immutable_seq`
- `audit_log` med hashkedja och signatur

Observability

- OpenTelemetry (OTLP) → Grafana-stack


