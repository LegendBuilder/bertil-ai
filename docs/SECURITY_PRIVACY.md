# Säkerhet & integritet

- OIDC + mTLS mellan tjänster
- TLS 1.2+, KMS-kryptering at-rest, pgcrypto för fält
- DLP: maskning av personnummer/orgnr, central logger allow-list, ingen PII i loggar
- Append-only access-logging

## DLP och PII

- Logga aldrig PII (personnummer, orgnr, IBAN). Maskning i UI (`******-1234`).
- Centraliserad logging med allow-list.
- Ingen OCR-text i råform i loggar; endast hash och fält med låg känslighet.

## WORM / Arkivering

- S3 Object Lock (COMPLIANCE), retention ≥ 7 år, legal hold vid behov.
- Versionering på, public access block på, SSE-S3.
- Lifecycle: avbryt multipart efter 7 dagar.

## Regionpolicy

- SE/EU-lagring. Utland kräver anmälan och kontraktsmässig grund.

## Hemligheter

- Secrets Manager för JWT-sekret, API-nycklar. Inga nycklar i repo.


