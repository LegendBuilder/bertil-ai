# API-kontrakt (översikt)

Auth (BankID)

- POST /auth/bankid/init → { orderRef, autoStartToken }
- GET /auth/bankid/status?orderRef= → { status: pending|complete, user: {...} }

Ingest

- POST /documents (multipart: file + JSON meta) → { documentId }
- GET /documents/{id} → { meta, ocr, extracted_fields, compliance }

Accounting

- POST /verifications
- GET /verifications?year=…
- GET /trial-balance?year=…

Compliance

- GET /compliance/summary?year=… → { score, flags }

Exports

- GET /exports/sie?year=… → .se
- GET /reports/vat?period=… → PDF/JSON
- POST /bolagsverket/submit → { receipt, status }


