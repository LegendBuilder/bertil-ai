[![CI](https://github.com/LegendBuilder/bertil-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/LegendBuilder/bertil-ai/actions/workflows/ci.yml)

Sveriges bästa digitala revisor – Monorepo

Översikt

Detta monorepo innehåller klient (Flutter) och backend (FastAPI) med **avancerade AI-agenter** samt infrastruktur/IaC och dokumentation. Målet är **99% automatiserad bokföring** från foto till verifikation under 20 sekunder, med svenska regelkrav (Bokföringslagen, BFN/Skatteverket, Bolagsverket, SIE).

## 🚀 AI-Agenter & Personal Skatteavdrag (Ny funktionalitet)

### 🇸🇪 Personal Tax Optimization - NYHET!

**Bertil AI hjälper nu privatpersoner med skatteavdrag - första plattformen som kombinerar företags- och privatekonomisk optimering!**

- ✅ **Smart kvittoscanning**: AI upptäcker automatiskt ROT/RUT, sjukkostnader, arbetsutrustning
- ✅ **Svenska skatteregler**: ROT (30%), RUT (50%), medicinska kostnader (över 5K), arbetskostnader  
- ✅ **Familjeoptimering**: Sammanräkningar, barnbidrag, optimal fördelning mellan partners
- ✅ **IPS & pensionsoptimering**: Maximera skatteavdrag för pensionssparande
- ✅ **Skatteåterbäringsberäkning**: Estimera återbäring baserat på upptäckta avdrag
- **Endpoints**: `/personal-tax/*` - analyze-receipt, optimize-family-taxes, pension-optimization

### Offline‑kö (web + mobil)

- När nätverket är nere köas POST/PUT/PATCH i en lokal outbox och spelas upp automatiskt när anslutning återkommer.
- Web: IndexedDB (via idb_shim). Mobil: Isar.
- UI: en liten badge visar antal köade objekt och en knapp "Försök igen" triggar replay.
- Outbox‑hantering: öppna `/#/settings/outbox` för att se, försöka igen eller radera poster.

**Bertil-AI är utrustad med kraftfulla AI-agenter som levererar "Tesla-upplevelse" för både företag och privatpersoner.**

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
  - KPI: `compliance_blocked_total{org_id,phase}` (pre/post)

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
  - **Metrics/KPI**
    - `GET /metrics/kpi` – attempts/success/rate per org och nivå
    - `GET /metrics/flow` – p95 och sampletider för foto→bokföring
    - `GET /metrics/alerts` – rate‑limit‑block, OCR‑kövarningar m.m.
    - A/B: LLM‑modellsplit via env; Grafana dashboards inkluderar automation rate/latency per model
- services/ocr – OCR-adaptrar (Tesseract, Google Vision, AWS Textract)
- services/ai – AI/regelmotor (ersatt av agents)
- infra/terraform – Terraform (S3 Object Lock + KMS, RDS Multi‑AZ, OpenSearch, WAF/ALB, Secrets)
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
   - Starta API lokalt: `uvicorn services.api.app.main:app --reload`
   - cd apps\mobile_web_flutter
   - flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000

Docker (API + worker + Postgres + Redis)

1. Skapa `.env` i repo-roten (valfritt för OpenRouter/Redis cache):
   ```
   LLM_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-...
   LLM_MODEL=meta-llama/llama-3.1-70b-instruct:free
   LLM_TEMPERATURE=0.1
   LLM_CACHE_URL=redis://redis:6379/1
   LLM_CACHE_TTL_HOURS=24
   LLM_FALLBACK_ENABLED=true
   ```
2. Starta stacken:
   - `docker compose up -d --build`
3. Verifiera:
   - `curl http://localhost:8000/healthz`
   - `curl http://localhost:8000/admin/kb/status`

Flutter enhanced AI

- Klienten anropar `/ai/enhanced/auto-post` när förbättrad automation är aktiverad i appens inställningar; annars faller den tillbaka till `/ai/auto-post` automatiskt vid fel.

Miljövariabler

- API
  - `DATABASE_URL` (lokalt default SQLite)
  - `CORS_ALLOW_ORIGINS` (default `*`)
  - `JWT_SECRET`, `JWT_ISSUER`
  - `OCR_PROVIDER` = `stub|google_vision|aws_textract|tesseract`
  - `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (Textract)
  - `GOOGLE_APPLICATION_CREDENTIALS` (Vision)
  - `OTLP_ENDPOINT` (valfri)
  - Rate limiting: `RATE_LIMIT_REDIS_URL`, `RATE_LIMIT_PER_MINUTE` (fallback till in‑process)
  - Upload hardening: `UPLOAD_MAX_BYTES`, `UPLOAD_ALLOWED_MIME`, `UPLOAD_ALLOW_PDF`, `PDF_SANITIZE_ENABLED`, `VIRUS_SCAN_ENABLED`
  - LLM budget: `LLM_BUDGET_DAILY_USD`, `LLM_BUDGET_ENFORCE`, `LLM_COST_PER_REQUEST_ESTIMATE_USD`
  - LLM A/B: `LLM_AB_TEST_ENABLED`, `LLM_AB_PRIMARY_MODEL`, `LLM_AB_SECONDARY_MODEL`, `LLM_AB_SPLIT_PERCENT`
  - WORM/S3: `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`
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
- ⚠️ **Cachning**: Redis‑cache stöd finns men ej aktiverad i prod
- ⚠️ **Observability**: Prometheus endpoints klara; Grafana dashboards pending
- ✅ **Inlärning**: Feedback‑loop aktiv (vendor→konto/moms)

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

### Flutter (Förbättrat - Personal Skatteavdrag)
- **NY: Skatteavdrag-flik**: Personal tax dashboard med svenska skatteoptimering
- **Smart kvittoscanning**: Enhanced capture som analyserar både företag och privat
- **Skattenotifier**: Popup som föreslår Smart Capture för potentiella skatteavdrag
- BankID-stubflöde, Kamera/Upload (auto-crop, blänkvarning, batch)
- Dokumentlista/detalj (OCR-overlay, explainability, öppna verifikation)
- Dashboard (Trygghetsmätare + flaggor), Verifikationsvy (entries, audit-hash, åtgärder)
- Rapporter (SIE/PDF-knappar)

### Konkurrensfördelar
- **vs Fortnox (349-500 SEK)**: Lägre pris (299 SEK) + zero user effort + personal skatteavdrag
- **vs Visma/Bokio**: 99% automatisering (de har ~60-80%) + proaktiv optimering
- **UNIK**: Första plattformen som kombinerar företags- och privatekonomisk optimering
- **Personal Tax Market**: Ingen konkurrent erbjuder AI-driven ROT/RUT/sjukkostnads-optimering
- **Målgrupp**: 18K småföretag + privata användare, ROI 200-500% för företag, 1000-3000 kr/år skattebesparingar för privatpersoner


