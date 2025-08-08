# OCR & AI-pipelines

Adaptrar

- Primär: Vision/Textract (EU), fallback: Tesseract

Fältextraktion

- LLM-assist + regex/heuristik (datum, belopp, moms, orgnr/IBAN, motpart) med confidence

Kontomappning & momslogik

- BAS-mappning (lärd modell + regler), moms 25/12/6 + specialfall

Explainability & avvikelser

- Kort orsak (“Valde 5811 …”), dubbletter, orimlig moms, fel datum


