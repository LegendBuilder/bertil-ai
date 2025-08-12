# API-kontrakt (översikt)

> Säkerhet: I `staging/prod` kräver alla skyddade endpoints headern `Authorization: Bearer <jwt>`. `local/test/ci` tillåter stub‑user.

## Auth (BankID)

- POST /auth/bankid/init → { orderRef, autoStartToken }
- GET /auth/bankid/status?orderRef= → { status: pending|complete, user: {...} }

## Ingest

- POST /documents (multipart: file + JSON meta) → { documentId }
- GET /documents/{id} → { meta, ocr, extracted_fields, compliance }

## Accounting

- POST /verifications
- GET /verifications?year=…
- GET /trial-balance?year=…

## AI Enhanced (NEW - 99% Automation)

### Invisible Bookkeeper Agent
- **POST /ai/enhanced/auto-post** → 99% automated verification creation
  ```json
  Request: { "file_path": "/path/to/receipt.jpg", "org_id": 1 }
  Response: { 
    "status": "auto_approved",
    "verification_id": 12345,
    "confidence": 0.94,
    "explanation": "Kaffe AB → 5811 (Representation). Compliance: 95/100"
  }
  ```

### Compliance Guardian Agent  
- **POST /ai/enhanced/pre-check** → Prevent compliance issues before creation
  ```json
  Request: { "total_amount": 1500, "counterparty": "Taxi AB", "org_id": 1 }
  Response: {
    "can_proceed": true,
    "risk_level": "low", 
    "compliance_score": 92,
    "warnings": []
  }
  ```

- **GET /ai/enhanced/compliance-health** → Daily compliance monitoring
  ```json
  Response: {
    "compliance_rate": "94.2%",
    "health_status": "GOOD",
    "critical_issues": 0,
    "next_vat_deadline": "2025-02-12 (15 days)"
  }
  ```

### Proactive Tax Optimizer
- **POST /ai/enhanced/optimize-tax/{verification_id}** → Swedish tax optimization
  ```json
  Response: {
    "total_tax_savings": 928.50,
    "optimizations": [
      {
        "type": "representation",
        "savings": 516.50,
        "reason": "Move to 5811 (Representation) - 50% deductible rule"
      }
    ]
  }
  ```

- **GET /ai/enhanced/tax-report** → Monthly tax optimization report
  ```json
  Response: {
    "total_potential_savings": 15420.75,
    "optimizations_available": 24,
    "optimization_rate": "67.3%"
  }
  ```

### Contextual Business Intelligence
- **GET /ai/enhanced/insights** → Perfect-timing business insights
  ```json
  Response: {
    "insights": [
      {
        "title": "Betydande kostnadökning",
        "message": "Kostnader ökat 23.5% (15750 SEK) vs förra månaden",
        "impact": 15750.0,
        "timing": "immediate",
        "action_required": true
      }
    ],
    "count": 5
  }
  ```

### System Status
- **GET /ai/enhanced/status** → All AI agent status check
  ```json
  Response: {
    "status": "active",
    "features": ["invisible_bookkeeper", "tax_optimizer", "compliance_guardian", "business_intelligence"],
    "automation_level": "99%"
  }
  ```

## Compliance

- GET /compliance/summary?year=… → { score, flags }

## Exports

- GET /exports/sie?year=… → .se
- GET /reports/vat?period=… → PDF/JSON
- POST /bolagsverket/submit → { receipt, status }


