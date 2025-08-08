# Kravspecifikation (normaliserad)

Syfte: Snabbaste "Foto → Bokfört" (< 20s), nybörjarvänlig UX, svensk regelefterlevnad (Bokföringslagen, BFN/Skatteverket, Bolagsverket, SIE), arkivering i 7 år (WORM).

Kärnflöden

- A) Foto → Verifikation (auto): kamera, hash/EXIF, OCR, fältextraktion, regler/AI, verifikation, compliance, svar "Bokfört".
- B) Arkivering: Underlag + metadata till S3 Object Lock (WORM), retention ≥ 7 år.
- C) Årsbokslut/årsredovisning: Trial balance → R/B (K2/K3), XBRL, BankID e-sign, e-inlämning.
- D) Exporter: SIE (1–4 + 5), PDF verifikationslista, XBRL.

Datamodell (kärna)

- users, organizations, fiscal_years, documents, extracted_fields, verifications, entries, compliance_flags, audit_log (append-only, hashkedja)

Säkerhet & integritet

- OIDC, mTLS, TLS 1.2+, KMS-at-rest, pgcrypto, DLP (maskning), access-logging (append-only)

Acceptanskriterier (urval)

- Foto→Klar demo (svenskt kvitto 12% moms)
- Dubblettdetektor (hash)
- WORM-policy test (delete denied)
- SIE-export importerbar i referenssystem


