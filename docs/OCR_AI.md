## OCR & AI-pipelines

### Adaptrar

- Primär: Vision/Textract (EU), fallback: Tesseract
- Stöd: `stub | google_vision | aws_textract | tesseract` via `OCR_PROVIDER`

### Konfiguration (env)

- `OCR_PROVIDER=stub|google_vision|aws_textract|tesseract`
- Google: `GOOGLE_APPLICATION_CREDENTIALS` eller `google_credentials_json_path`
- AWS: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- Tesseract: `TESSERACT_CMD` om binären inte finns i PATH

### Endpoint

- `POST /documents/{id}/process-ocr` kör vald adapter, sparar OCR-text och fält i DB och skriver sidecar JSON.

### Fältextraktion

- Regex/heuristik (datum, belopp, motpart) med confidence, senare LLM-assist

### Kontomappning & momslogik

- BAS-mappning (lärd modell + regler), moms 25/12/6 + specialfall

### Explainability & avvikelser

- Kort orsak (“Valde 5811 …”), dubbletter, orimlig moms, fel datum

