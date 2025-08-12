# Roadmap

## v0.1 (MVP, nu → 2 veckor)
- Auth: JWT‑guards live; BankID broker (stub → Signicat sandbox)
- Foto → Bokfört: OCR (Tesseract) + enhanced autopost med fallback
- Rapporter: SIE (MVP), Trial balance, Momsrapport JSON/PDF
- WORM (dev): lokal WORM‑sim + S3 layout; delete‑deny test
- Observability: grunddashboard (OCR p95, automation rate)

## v0.2 (2 → 6 veckor)
- BankID: riktig init/status + JWT issuance
- WORM (prod): S3 Object Lock + retention ≥ 7 år, Legal Hold
- Fortnox: OAuth + tokenpersistens + batchsync + retry/backoff
- VAT: EU/RC‑edgefall, representation 50% (split), drivmedel, OSS
- LLM: OpenRouter/OpenAI + Redis‑cache + cost guards

## v0.3 (6 → 12 veckor)
- Bolagsverket e‑inlämning (staging), XBRL serializer
- Org/RBAC: org‑scoping + roller; admin‑actions audit
- BI: kassaflöde, trendlarm, optimeringsrapport
- E2E & Load: 1k req/h; fuzz uploader; SAST/DAST + SBOM



