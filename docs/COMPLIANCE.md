# Compliance-regler

Kodifierade regler (Pass 3+):

- R-001 Verifikationsinnehåll – blockerande
- R-011 Löpande bokföring tidsgräns – varning
- R-021 Arkivering 7 år (WORM) – blockerande
- R-031 Digitalisering OK – info
- R-051 SIE-export tillgänglig – info

Tester: unit + property + kända felcase; coverage ≥ 95% för rules.

## KPI-koppling
- Pre‑check block loggas i `compliance_blocked_total{phase="pre"}`
- Post‑check block (vid skapande) loggas i `compliance_blocked_total{phase="post"}`

