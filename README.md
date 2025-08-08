[![CI](https://github.com/LegendBuilder/bertil-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/LegendBuilder/bertil-ai/actions/workflows/ci.yml)

Sveriges bästa digitala revisor – Monorepo

Översikt

Detta monorepo innehåller klient (Flutter) och backend (FastAPI) samt infrastruktur/IaC och dokumentation. Målet är snabbaste vägen från foto till bokförd verifikation under 20 sekunder, med svenska regelkrav (Bokföringslagen, BFN/Skatteverket, Bolagsverket, SIE).

Struktur

- apps/mobile_web_flutter – Flutter-klient (iOS/Android/Web)
- services/api – FastAPI-baserad backend
- services/ocr – OCR-adaptrar (stub i Pass 2)
- services/ai – AI/regelmotor (stub i Pass 2)
- infra/terraform – Terraform-stubbar (S3 Object Lock, RDS, OpenSearch, Secrets)
- docs – Dokumentation (krav, arkitektur, säkerhet, tester, roadmap)

Snabbstart (lokalt, Windows PowerShell)

Backend (Python/FastAPI)

1. Skapa och aktivera virtuell miljö (Python 3.11):
   - py -3.11 -m venv .venv
   - .\.venv\Scripts\Activate.ps1
2. Installera beroenden:
   - pip install -r services\api\requirements.txt -r services\api\requirements-dev.txt
3. Kör tester:
   - pytest -q
4. Starta API (utveckling):
   - uvicorn services.api.app.main:app --reload

Flutter-klient

1. (Första gången) Säkerställ att Flutter finns i PATH och kör:
   - cd apps\mobile_web_flutter
   - flutter create .   (genererar android/ios mappar)
   - flutter pub get
   - flutter test
2. Kör appen (t.ex. web):
   - flutter run -d chrome
3. Kör i Android emulator (exempel):
   - uvicorn services.api.app.main:app --reload
   - cd apps\mobile_web_flutter
   - flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000

Miljövariabler

- API
  - `DATABASE_URL` (lokalt default SQLite)
  - `CORS_ALLOW_ORIGINS` (default `*`)
  - `JWT_SECRET`, `JWT_ISSUER`
  - `OCR_PROVIDER` = `stub|google_vision|aws_textract|tesseract`
  - `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (Textract)
  - `GOOGLE_APPLICATION_CREDENTIALS` (Vision)
  - `OTLP_ENDPOINT` (valfri)
Se `.env.example` för exempelvärden. Använd separata `.env` per tjänst/miljö.

CI/CD

GitHub Actions kör lint och tester för backend och Flutter samt formatteringskontroll för Terraform. Branch-skydd och CODEOWNERS ingår. Backend-coverage gate: ≥ 80%.
- WORM-smoketest säkerställer lokalt arkiv-layout för `/documents/{id}`.

Jurisdiktion & lagring

- SE/EU-regioner, S3 Object Lock (WORM) ≥ 7 år.
- Append-only verifikationer och revisionskedja.

Status (Pass 2)

- Monorepo scaffoldat, CI-workflows skapade, Terraform-stubbar tillagda.
- Backend: Auth (stub), Ingest (WORM), Verifikationer (append-only + ombokning/korrigering), Compliance-regler (R-001/011/021/031/DUP/VAT/PERIOD), SIE/PDF-exporter, DLP-maskning util, E2E-prestandatest.
- Flutter: BankID-stubflöde, Kamera/Upload (auto-crop, blänkvarning, batch), Dokumentlista/detalj (OCR-overlay, explainability, öppna verifikation), Dashboard (Trygghetsmätare + flaggor), Verifikationsvy (entries, audit-hash, åtgärder), Rapporter (SIE/PDF-knappar).


