from fastapi.testclient import TestClient
from services.api.app.main import app


def test_sie_and_pdf_exports() -> None:
    with TestClient(app) as client:
        # create sample verifications
        for i in range(2):
            payload = {
                "org_id": 1,
                "date": "2025-03-0{}".format(i + 1),
                "total_amount": 100.0 + i,
                "currency": "SEK",
                "vat_amount": 0.0,
                "counterparty": "Test AB",
                "document_link": ".worm_store/aa/bb/{}{}_doc.jpg".format("a" * 62, i),
                "entries": [
                    {"account": "1910", "debit": 100.0 + i, "credit": 0.0},
                    {"account": "4000", "debit": 0.0, "credit": 100.0 + i},
                ],
            }
            r = client.post("/verifications", json=payload)
            assert r.status_code == 200

        r_sie = client.get("/exports/sie", params={"year": 2025})
        assert r_sie.status_code == 200
        assert "#VER" in r_sie.text and "#TRANS" in r_sie.text

        r_pdf = client.get("/exports/verifications.pdf", params={"year": 2025})
        assert r_pdf.status_code == 200
        assert r_pdf.headers.get("content-type", "").startswith("application/pdf")


