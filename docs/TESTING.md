# Testning & kvalitetsmål

- Backend: pytest + coverage, property-tests för regler/exporter
- Flutter: widget + golden, integration (mock server), Patrol E2E (Pass 8)
- Coverage gates i CI; exporter/rules ≥ 95% från Pass 3+

## KPI & Metrics test
- Validera att `/metrics/kpi` uppdateras när autopost körs (legacy/enhanced)
- Säkerställ att `compliance_blocked_total` ökar vid pre/post‑blockeringar
- Mät `flow_photo_to_post_seconds` i dev och att `/metrics/flow` visar p95 inom målgräns


