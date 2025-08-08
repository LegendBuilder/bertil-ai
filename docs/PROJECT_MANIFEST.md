Title: Bygg “Sveriges bästa digitala revisor” — Flutter + FastAPI/NestJS, BankID, OCR, SIE (SE-compliant, UX-first)
Roll & Mål

Du är senior full-stackarkitekt och byggrobot i ett greenfield-projekt. Leverera produktionsredo kod för:

    Klient: Flutter (iOS/Android/Web)

    Backend: FastAPI (Python 3.11) eller NestJS (Node 18+)

    Mål: snabbaste möjliga “Foto → Bokfört” under 20 sek för första kvittot, med svenska lagkrav (Bokföringslagen, Skatteverket/BFN, Bolagsverket, SIE).

Absoluta principer (allt UI & kod följer detta)

    UX-först, zero-jargong: Inget “debet/kredit/konto” i nybörjarläge. Tre tydliga val + “Vet inte”.

    “Foto → Klart” < 20 sek (första kvitto). Onboarding < 3 min (BankID → bolagsdata → första foto).

    Trygghetsmätare överst: “Skatteverks-klart ✅ | ⚠️ 2 saker kvar | ❌ blockerat”.

    Proaktiv agent: föreslår moms, periodisering, preliminärskatte-justering.

    Explainable AI: varje autoverifikation visar “Varför valde vi detta?”.

    Append-only & spårbarhet: inga “edit in place”; rättning = reverserande verifikation.

    Sekretess: maska personnummer; logga aldrig PII; DLP för personnummer/orgnr.

Juridiska måste-krav → Systemkrav (implementera)

    Löpande bokföring + verifikation per affärshändelse med: id, datum, belopp, motpart, moms, dokumentlänk.

    Arkivering 7 år, WORM (Object Lock), ordnat skick. Tillåten utlandslagring med åtkomst/anmälan.

    Digitalisering av papper (1 juli 2024): papperskvitto kan kasseras om oföränderlig digital kopia finns.

    E-inlämning årsredovisning (Bolagsverket/XBRL).

    SIE-export (svensk de-facto standard).

    BankID för auth/signering (via officiell broker, t.ex. Signicat).

Tekniska derivat:

    Append-only verifikationslogg med spårbar rättning.

    WORM-lagring/retention ≥ 7 år (S3 Object Lock + ev. legal hold).

    OCR→verifikationsgenerator som alltid fyller lagkravsfält.

    Exporter: SIE (1–4 + 5), PDF verifikationslistor, XBRL/ivis för Bolagsverket, underlag för e-inlämning.

    Regionkontroll: SE/EU. Utland → anmälningsflöde.

Arkitektur (målsystem)

Klient (Flutter Web + iOS + Android)

    State: Riverpod

    Navigation: go_router

    HTTP: Dio

    Offline/queue: Isar

    Media: camera, image_picker, file_picker

    PDF render: pdfx

    Analytics: firebase_analytics (eller PostHog)

    Intl/freezed/json_serializable

Backend (API & AI)

    API: FastAPI (Python) eller NestJS (Node)

    DB: PostgreSQL + pgcrypto

    Search: OpenSearch/Elasticsearch (avtal/underlag)

    OCR: Google Vision / AWS Textract, fallback Tesseract

    AI-pipelines: fältextraktion, BAS-kontomappning, momslogik, avvikelsedetektor

    Rules/Compliance: Python (Pydantic + rules) eller Nest service

    Storage: S3-kompatibel med Object Lock (WORM), retention ≥ 7 år

    Auth/Sign: BankID via broker (ex. Signicat)

    Exporter: SIE, XBRL/ivis, PDF verifikationslistor

    Observability: OpenTelemetry + Grafana

Säkerhet

    OIDC + mTLS mellan tjänster

    KMS-kryptering at rest, TLS 1.2+ in transit

    DLP för personnummer/orgnr

    Åtkomstloggning (append-only revisionslogg)

Datamodell (kärna – skapa migrations)

    users(id, personnummer_hash, bankid_subject, name, email, mfa, …)

    organizations(id, orgnr, name, address, bas_chart_version, …)

    fiscal_years(id, org_id, start_date, end_date, k2_k3)

    documents(id, org_id, fiscal_year_id, type[receipt|invoice|contract|other], storage_uri, hash_sha256, ocr_text, status, created_at)

    extracted_fields(document_id, key, value, confidence)

    verifications(id, org_id, fiscal_year_id, immutable_seq, date, total_amount, currency, vat_amount, counterparty, document_link, created_at)

    entries(id, verification_id, account, debit, credit, object/dimension)

    compliance_flags(entity_type, entity_id, rule_code, severity, message, resolved_by)

    audit_log(id, actor, action, target, before_hash, after_hash, timestamp, signature)

Immutability: immutable_seq + hashkedja i audit_log. Rättning = ny verifikation som reverserar/ersätter, aldrig “edit in place”.
End-to-end-flöden (implementera exakt)

A) Foto → Verifikation (auto)

    Fota kvitto i Flutter (camera).

    Client-side: skapa hash + EXIF + tid → /ingest (Dio).

    OCR → AI-parser → datum, belopp, moms, motpart.

    Rules-motor sätter BAS-konto + momskod; skapar verifikation (append-only).

    Compliance-check: verifikationsnummer, period, momslogik, dubbletter.

    Svar till klient: “Bokfört ✅” + uppdatera Trygghetsmätare.

B) Arkivering

    Dokument + JSON-metadata → S3 med Object-Lock, retention 7 år.

    Lagringspolicy: SE/EU, anmälan vid utland.

C) Årsbokslut/Årsredovisning

    Trial balance → Resultat+Balans (K2/K3).

    Skapa XBRL för Bolagsverket, BankID e-sign, sänd in.

D) Exporter

    SIE (1–4 + 5), PDF verifikationslista.

Flutter: projektupplägg & paket

/lib
  /app
    app.dart
    router.dart
    theme.dart
  /features
    /auth
      data/...      // BankID status polling
      ui/login_page.dart
      provider/auth_providers.dart
    /ingest
      ui/capture_page.dart   // camera + cropping + glare warning
      ui/upload_queue.dart
      data/ingest_api.dart
      domain/document.dart
      provider/ingest_providers.dart
    /ledger
      ui/dashboard_page.dart // Trygghetsmätare + progress
      ui/verification_view.dart
      data/ledger_api.dart
      domain/verification.dart
    /reports
      ui/vat_report.dart
      ui/year_end.dart
    /settings
      ui/profile.dart
  /shared
    widgets/..., utils/..., services/network.dart
  /l10n
/test

Paket: flutter_riverpod, go_router, dio, isar, camera, image_picker, file_picker, pdfx, intl, freezed, json_serializable.
Stateprinciper: Allt IO via Repository + FutureProvider/StateNotifier. Optimistic UI + offline queue (Isar).
UI & Informationsarkitektur

Navigation

    Mobil bottom-nav: Hem · Fota · Dokument · Rapporter · Konto

    Web sidomeny: Hem / Fota / Dokument / Rapporter / Konto

Hem (daglig kärna)

    Trygghetsmätare (✅/⚠️/⛔) + “Allt redo…”/“Saknar 2 kvitton…”

    Nästa åtgärd (en primärknapp)

    Smart tidslinje (Inkomster/Kostnader/Moms)

    Proaktiv agent (“Justera preliminärskatt?”)

Fota

    Kamera öppnas direkt, auto-crop, blänk-varning, batchläge.

    Efter foto: Uploading → Läser → Bokför ✅ (3–5 s progressbar).

Dokument

    Flikar: Nya · Väntar info · Klara · Alla

    Kortlista: thumbnail, datum, belopp, statuschip.

    Detaljvy: vänster bild/PDF med OCR-zoning overlay; höger fält (Datum/Belopp/Motpart/Moms/Kategori med 3 förslag + “Vet inte”).

    Förklaringsruta: “Valde 5811 (representation) p.g.a. ‘Lunch’ + 12% moms + belopp < 300 kr.”

Rapporter

    Momsstatus (“Denna period: 12 450 kr att betala”), Förhandsgranska/Skicka in.

    Resultat/Balans (kort + trendlinjer).

    Årsavslut: checklista (verifikationer klara, periodisering klar, e-sign klar).

    Export: SIE / PDF / XBRL (“Ladda ner bokföringsfil”).

Microcopy (svensk, varm + rak)

    Efter första kvittot: “Klart! Vi har bokfört detta och sparar originalet digitalt i 7 år.”

    Trygghetsmätare grön: “Allt redo för Skatteverket ✅”

    Nudge: “2 transaktioner saknar kvitto. Fota nu så håller vi dig 100% grön.”

    Oskärpa: “Det blev lite suddigt. Testa igen nära kvittot – vi fixar resten.”

Edge/Empty/Error

    Tom Hem: “Låt oss fota ditt första kvitto. Det tar 20 sek.” [Öppna kameran]

    Ingen moms: “Noll att redovisa – skönt! Vi meddelar om något ändras.”

    BankID avbrutet: “Ingen fara. Vill du försöka igen?” [Starta BankID]

    Server nere: “Det är på oss. Vi återställer nu. Dina kvitton är säkra.”

Tillgänglighet & Hastighet

    WCAG 2.1 AA, fokusindikatorer, labels.

    Kamera→Bokfört < 20s i 4G, lazy-load, 60 fps scroll.

    Stora touchytor, svep för Godkänn/Parkera.

Personalisering & Sticky

    Minne: favoritställen (Café X → representation), resmönster (flyg → 5800-serie).

    Auto-fyll motpart via OCR + IBAN/orgnr.

    “Är det här samma som förra månaden?” (ett-trycks).

    Insamling: kvitto-mejl, Drive/Dropbox, bank-synk.

    Belöningar: “Du ligger före 92%…”, “+18% snabbare än i juni”.

    Notiser (värdedrivna, max 1/dag).

Smarta rekommendationer:

    “Du har rätt att dra av X kr i moms denna månad – vill du att vi fixar det?”

    “Vill du sänka skatten med 8% genom att justera pensionsavsättningen?”
 och den ska vara lika detaljerad som 

Backend: API-kontrakt (skapa routes + DTOs + clients)

Auth (BankID-flöde)

    POST /auth/bankid/init → { orderRef, autoStartToken }

    GET /auth/bankid/status?orderRef= → { status: pending|complete, user: {...} }

Ingest

    POST /documents (multipart: file + JSON meta) → { documentId }

    GET /documents/{id} → { meta, ocr, extracted_fields, compliance }

Accounting

    POST /verifications (undantagsvis; oftast auto)

    GET /verifications?year=…

    GET /trial-balance?year=…

Compliance

    GET /compliance/summary?year=… → { score: 0..100, flags: [...] }

Exports

    GET /exports/sie?year=… → .se file

    GET /reports/vat?period=… → PDF/JSON

    POST /bolagsverket/submit → { receipt, status }

AI-pipelines (konkret, implementera adaptergränssnitt)

    OCR: Vision/Textract → text + bounding boxes (+ fallback Tesseract).

    Dokumentklassning: kvitto/faktura/avtal/övrigt (LightGBM eller liten transformer).

    Fältextraktion: LLM-assisterad parser + regex/heuristik (datum, belopp, moms, VAT-rate, orgnr/IBAN, leverantör).

    Kontomappning (BAS): lärd modell + regel-fallback (MCC/leverantör → 4010/4020/5611 etc).

    Momslogik: sverige 25/12/6 + specialfall (representation, drivmedel).

    Avvikelsemotor: dubbletter, OCR-fel, orimlig moms, datum utanför period, saknad motpart.

    Explainability: returnera kort orsak (“Valde 5811 …”).

Compliance-regler (kodifiera + tests)

    R-001 Verifikationsinnehåll: id, datum, belopp, motpart, moms, dokumentlänk. Blockerande.

    R-011 Löpande bokföring tidsgräns: kontant händelse senast nästa arbetsdag. Varning.

    R-021 Arkivering 7 år (WORM): Blockerande.

    R-031 Digitalisering OK: info/”grönt ljus” om checksumma + WORM.

    R-051 SIE-export tillgänglig: Info.

Säkerhet & integritet (enforcers)

    OIDC + mTLS (service-to-service).

    KMS för nycklar, pgcrypto för fält (personnummer hash/tokenisering).

    DLP: maska personnummer i UI; blockera loggar av PII; centrala loggers med allow-list.

    Audit: append-only journaling; signera hashkedja.

DevOps

    Monorepo: apps/mobile_web_flutter, services/api, services/ocr, services/ai, infra/

    IaC: Terraform (S3+Object Lock, RDS, OpenSearch, EKS/GKE)

    CI/CD: GitHub Actions → test → build → deploy (staging/prod)

    Migrations: Alembic (Py) / Prisma (Node)

    Secrets: Vault / AWS Secrets Manager

    Observability: OpenTelemetry → Grafana/Tempo/Loki

Test & kvalitetsmål

    Flutter: widget + golden tests (kamera, dashboard, verification).

    E2E: Patrol/Flutter integration + Mock Server.

    OCR/AI-benchmark: 1000+ svenska kvitton; precision belopp ±0,01; datum; moms; kontomappning ≥ 95% top-1.

    Compliance-suite: regler körs mot kända felcase.

    A/B-mål: “Foto→Klar < 20s”, “First-week retention ≥ 80%”.

Roadmap (90 dagar)

    v0.1 (v1-4): BankID login, kamera-uppladdning, OCR MVP, auto-verifikation, dashboard (trygghet).

    v0.2 (v5-8): Momsregler, SIE-export, WORM-arkiv, avvikelsemotor, offline-queue.

    v0.3 (v9-12): K2/K3-paket, Bolagsverket e-inlämning (staging), A/B retention-test.

Mätpunkter (analytics)

Events: auth_login_success, capture_photo_started/completed(ms), ocr_extraction_success, auto_posting_success, doc_confirmed, doc_parked, compliance_score_changed, export_sie_clicked, year_end_signed
North-stars: TTFV < 60s, Foto→Bokfört median < 20s, 7-dagars retention ≥ 80%, gröna konton 30d ≥ 75%, AI-autopost precision ≥ 95%.
Coding standards

    Dart null-safety, very_good_analysis lints.

    95% testtäckning på rules/exporters.

    Rättningar = motbokningar (inga edits).

    Maska PII i UI, logga ej PII.

    Feature flags för AI-modellval.

Acceptance tests (ska passera innan DoD)

    “Foto→Klar” demo med svenskt kvitto (12% moms).

    Dubblettdetektor (samma hash) → flagga.

    WORM-policy test: write once, delete denied.

    SIE-export importeras i referenssystem utan fel.

Out of scope (kan stubbas)

    Lönehantering, avancerad lagerredovisning.

OUTPUT-PROTOKOLL (superviktigt för Cursor)

    Arbeta i tydliga pass.
    Pass 1: Plan + beslutsfrågor → vänta på “Fortsätt”.
    Pass 2: Scaffolda repo + CI + infra stubbar. [KLAR]
    Pass 3: Backend API (auth/ingest/ledger/compliance/exports) + migrations + tests. [PÅGÅR – MVP klart: auth/ingest/verifications/compliance/exports, auditkedja, trial balance, SIE MVP, tester gröna]
    Pass 4: Flutter app (struktur, navigation, skärmar, providers) + golden tests. [NÄST]
    Pass 5: OCR/AI-adaptrar + fallback + explainability.
    Pass 6: SIE/XBRL-exporter + e-sign stubbar.
    Pass 7: Observability, DLP, security hardening.
    Pass 8: E2E-tests, A/B toggles, polish.

    Filskrivning: För varje fil, skriv:

=== path/to/file.ext ===
```lang
<innehåll>

Ange **en fil per sektion**. Inga förkortningar, inga “…” – skriv fullständig kod.

3) **Idempotens:** Vid ändringar, använd **“PATCH:”** block som visar unified diff mot filen eller skriv om hela filen under samma header.

4) **Miljö & hemligheter:** Alla nycklar via `ENV`. Inga riktiga hemligheter i repo. Lägg exempel i `.env.example`.

5) **Kvalitetsgrindar:** Kör linters/tests i CI. Blockera merge om tester/coverage misslyckas.

6) **Språk & lokalisering:** Svenska som primär copy i UI (intl), men kod/kommentarer på engelska.

---

# GENOMFÖRANDE (börja nu)

## Pass 1 – Plan & val (kräv bekräftelse)
- Fråga om backend-val (**FastAPI default** om inget sägs) och val av OCR-leverantör (Vision/Textract, med Tesseract fallback).
- Redovisa **full arbetsplan** med milstolpar och risker (juridik/BankID/WORM).
- Lista **domänmoduler** och tillhörande **testsviter**.
- Bekräfta **regionpolicy (SE/EU)** och **lagringskrav** (Object Lock ≥ 7 år).
- Presentera “**Definition of Done**” per pass (inkl. tester/coverage).

**Stoppa här och vänta på “Fortsätt”.**

## Pass 2 – Repo & CI/IaC skeleton
- Monorepo layout, GitHub Actions (lint/test/build), Terraform stubbar (S3 Object Lock, RDS, OpenSearch, Secrets).
- Codeowners + branch protection guidelines.

## Pass 3 – Backend (API, DB, Compliance)
- Välj FastAPI (om ej överstyrt). Strukturera `services/api` med routers: **auth, ingest, verifications, compliance, exports**.
- **BankID**: init/status endpoints med broker-abstraktion och stubbar för Signicat sandbox.
- **PostgreSQL** schema/migrations enligt **datamodellen**. `pgcrypto`/tokenisering för personnummer.
- **Append-only** verifikationsservice med **hashkedja** (SHA-256), audit-signering.
- **Compliance-motor** (R-001, R-011, R-021, R-031, R-051) + unit-/property-tests.
- **SIE exporter** (+ tests): stöder 1–4 och 5 (verifikationer).
- **XBRL/ivis**: datastrukturer + serialisering stubbar, e-inlämning adapter-interface.
- **OpenTelemetry** instrumentering.

## Pass 4 – Flutter app
- Skapa struktur enligt katalogträdet. **go_router**, **Riverpod**, **Dio**, **Isar** offline-queue.
- **Skärmar:** Login (BankID-polling), Camera/Capture (overlay + glare warning + batch), UploadQueue, Dashboard (Trygghetsmätare), DocumentList, VerificationView, VAT Report, Settings/Profile.
- **Trygghetsmätare** komponent (LinearProgressIndicator + chip + animations).
- **OCR-overlay** i dokumentdetalj (visa bounding boxes).
- **Microcopy** enligt bibliotek ovan. **WCAG AA**.

## Pass 5 – OCR/AI
- Adapterinterface + implementeringar: Vision/Textract + Tesseract fallback.
- LLM-assisterad fältextraktion med regex/heuristik; confidence score; **autogodkänn > 90%** (A/B-styrt).
- Avvikelsemotor + explainability.

## Pass 6 – Exporter & Årsavslut
- Full **SIE-export** (CLI + API), **PDF verifikationslista**.
- **K2/K3** rapportpaket (trial balance → R/B).
- E-sign (BankID) stubbar och workflow.

## Pass 7 – Security/Privacy Hardening
- OIDC + mTLS konfiguration, **TLS** enforce, **KMS** integration.
- DLP filter i loggers, PII-maskning, access-logging (append-only).

## Pass 8 – E2E & A/B
- Patrol/Flutter integration + Mock Server.
- A/B toggles: autogodkänn-tröskel, ikonval vs text.
- Mät **Foto→Bokfört** tid, retention, precision.

---

# UI-DETALJER (måste med i implementeringen)
- **Hem**: Trygghetsmätare (badge + färg), “Nästa åtgärd”, tidslinje-kort (Inkomster/Kostnader/Moms), agentkort.
- **Fota**: ett-trycks-foto, batchläge (long-press), auto-klassning (kvitto/faktura/avtal); snabbknappar “Privat köp”, “Utlägg”, “Osäker – parkera”.
- **Felhantering**: blänk/sudd → overlay-guide (3 s); osäker OCR → flagga “Väntar AI-granskning (du behöver inte göra något)”.
- **Dokument-list**: smarta listor, massåtgärder (Godkänn/Parkera/Privat).
- **Detalj**: tre kategoriförslag + “Vet inte”; förklaring **varför** konto/moms valdes (highlighta zoner).
- **Rapporter**: Momsstatus med Call-to-action, Årsavslut checklista, Export (SIE/PDF/XBRL) med enkelt språk.
- **Notiser**: daglig max 1 (framsteg), periodskifte, händelsebaserade (mejl-inkorg hittade kvitton). Enkelt att tona ned.

---

# KVALITET & DO-NOTS
- **Inga externa länkar i kod** (källor hålls i README för devs).
- **Logga aldrig PII**; centraliserade loggers med allow-list.
- **Inga “edit in place” av verifikationer**; använd reverserande poster.
- **Regionkontroll** (SE/EU) för all lagring.
- **Feature flags** för AI-modellval och autogodkänntröskel.
- **Coverage gates** i CI (rules/exporters ≥ 95%).

---

# README (auto-generera utdrag)
- Juridik i dev-termer: digitalisering (1 juli 2024), verifikationsfält, 7 års arkivering, e-inlämning, SIE interoperabilitet.
- Snabbstart: env-variabler, lokala körkommandon, test, seed.
- Säkerhet & DLP, WORM-konfig (Object Lock).

---

# STARTA NU – Första svaret ska innehålla:
1) **Konkret plan** (Pass 1–8) med tidsestimat per pass.  
2) **Valfrågor**: FastAPI vs NestJS (standard: FastAPI), OCR-leverantör, Analytics (Firebase eller PostHog).  
3) **Definition of Done** per pass.  
4) **Risker & mitigering** (BankID, WORM, SIE, XBRL, latency 4G).  

> När jag svarar “Fortsätt”, följ Output-protokollet och börja med **Pass 2** (rep