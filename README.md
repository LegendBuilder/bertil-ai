[![CI](https://github.com/LegendBuilder/bertil-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/LegendBuilder/bertil-ai/actions/workflows/ci.yml)

Sveriges bästa digitala revisor – Monorepo

Översikt

Detta monorepo innehåller klient (Flutter) och backend (FastAPI) med **avancerade AI-agenter** samt infrastruktur/IaC och dokumentation. Målet är **99% automatiserad bokföring** från foto till verifikation under 20 sekunder, med svenska regelkrav (Bokföringslagen, BFN/Skatteverket, Bolagsverket, SIE).

## 🚀 AI-Agenter (Ny funktionalitet)

**Bertil-AI är utrustad med fyra kraftfulla AI-agenter som levererar "Tesla-upplevelse" för bokföring.**

Aktivering (dev):

```
cp .env.example .env
# Fyll i OPENROUTER_API_KEY och sätt LLM_PROVIDER=openrouter
pip install -r services/api/requirements.txt
python -m uvicorn services.api.app.main:app --reload
```

### 1. **Invisible Bookkeeper Agent** (99% automatisering)
- ✅ Avancerad OCR med konfidensvalidering
- ✅ Svensk moms-detektion (SE25/SE12/SE06/RC25) från kvittotext  
- ✅ Automatisk företagskategori-igenkänning
- ✅ Intelligent återgång till manuell granskning vid låg säkerhet
- **Endpoint**: `POST /ai/enhanced/auto-post`

### 2. **Proactive Tax Optimizer** (Svenska skatteregler)
- ✅ Representation-optimering (50%-regeln)
- ✅ Resekostnads-optimering (6% moms för transport)
- ✅ FoU-kostnads-detektion (förhöjda avdrag)
- ✅ Årsskifte-strategier och kontoklass-optimering
- **Endpoints**: `POST /ai/enhanced/optimize-tax/{id}`, `GET /ai/enhanced/tax-report`

### 3. **Compliance Guardian** (Förebygg problem)
- ✅ Pre-verifikation compliance-kontroll (blockerar felaktig data)
- ✅ Svenska regleringsdeadlines-övervakning
- ✅ Kontanttransaktions-gränser (penningtvätt-prevention)
- ✅ Mönsteranalys (upptäcker misstänkta transaktioner)
- **Endpoints**: `POST /ai/enhanced/pre-check`, `GET /ai/enhanced/compliance-health`

### 4. **Contextual Business Intelligence** (Perfekt timing)
- ✅ Kostnadstrendanalys med påverkanskalkyl
- ✅ Kassaflödesprediktioner och varningar
- ✅ Skattemöjlighets-identifiering
- ✅ Leverantörs-koncentrations-riskanalys
- **Endpoint**: `GET /ai/enhanced/insights`

Struktur

- apps/mobile_web_flutter – Flutter-klient (iOS/Android/Web)
- services/api – FastAPI-baserad backend med **AI-agenter**
  - **services/api/app/agents/** – Fyra AI-agenter för automatisering
    - `invisible_bookkeeper.py` – 99% automatisk bokföring
    - `tax_optimizer.py` – Proaktiv skatteoptimering
    - `compliance_guardian.py` – Förebyggande compliance
    - `business_intelligence.py` – Kontextuell affärsintelligens
  - **services/api/app/routers/ai_enhanced.py** – Förbättrade AI-endpoints
- services/ocr – OCR-adaptrar (Tesseract, Google Vision, AWS Textract)
- services/ai – AI/regelmotor (ersatt av agents)
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

Status (Pass 3 - AI-Enhanced)

## ⚠️ VIKTIGT: Nuvarande Status - 60% Produktionsklar

### Implementerat (Grund finns)
- ✅ **AI-Agent arkitektur**: Fyra agenter med svensk affärslogik 
- ✅ **API-endpoints**: Alla `/ai/enhanced/*` endpoints fungerar
- ✅ **Grundläggande regelmotor**: Svenska moms- och skatteregler (förenklat)
- ✅ **Säker integration**: Wrapper-pattern, fallback till existerande system

### Kritiska Delar Som Saknas
- ❌ **LLM-integration**: Ingen OpenAI/Anthropic API kopplad (kräver API-nycklar)
- ❌ **Skatteverket-träning**: Behöver scrapa och träna på faktisk dokumentation
- ❌ **Cachning**: Ingen Redis-cache (dyra API-anrop)
- ❌ **Övervakning**: Ingen Prometheus/Grafana uppsatt
- ❌ **Inlärning**: Kan inte lära från användarkorrigeringar

### Väg till 99% Automatisering
**Se [PRODUCTION_READINESS.md](./PRODUCTION_READINESS.md) för fullständig plan**

- **Vecka 1-2**: Koppla LLM + Svenska kunskapsbas → 85% redo
- **Vecka 3-4**: Produktionshärdning + testning → 95% redo
- **Månad 2**: Lärande från verklig användning → 99% uppnåeligt

### Kostnadsuppskattning för Produktion
- **Utveckling**: 2 utvecklare × 4 veckor
- **LLM API**: $500 test-krediter, sedan $20-30K/månad vid 18K användare
- **Svensk skatteexpert**: 1 vecka konsultation för validering
- **Infrastruktur**: Redis, monitoring, load balancing

### Backend (Förbättrat)
- Auth (stub), Ingest (WORM), Verifikationer (append-only + ombokning/korrigering)
- **Nya AI-endpoints**: `/ai/enhanced/*` för avancerad automatisering
- Compliance-regler (R-001/011/021/031/DUP/VAT/PERIOD) + **förebyggande kontroll**
- **Skatteoptimerings-motor** med svenska affärsregler
- **Affärsintelligens-motor** för kostnadstrender och kassaflöde
- SIE/PDF-exporter, DLP-maskning util, E2E-prestandatest

### Flutter (Oförändrat)
- BankID-stubflöde, Kamera/Upload (auto-crop, blänkvarning, batch)
- Dokumentlista/detalj (OCR-overlay, explainability, öppna verifikation)
- Dashboard (Trygghetsmätare + flaggor), Verifikationsvy (entries, audit-hash, åtgärder)
- Rapporter (SIE/PDF-knappar)

### Konkurrensfördelar
- **vs Fortnox (349-500 SEK)**: Lägre pris (299 SEK) + zero user effort
- **vs Visma/Bokio**: 99% automatisering (de har ~60-80%) + proaktiv optimering
- **Målgrupp**: 18K användare, ROI 200-500% för småföretag


