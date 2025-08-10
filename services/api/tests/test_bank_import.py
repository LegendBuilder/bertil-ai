from __future__ import annotations

from io import BytesIO
from services.api.app.main import app
from fastapi.testclient import TestClient


def test_bank_import_and_list():
    client = TestClient(app)
    csv_data = (
        "date,amount,currency,description,counterparty\n"
        "2025-01-15,1234.56,SEK,Card purchase Kaffe AB,Kaffe AB\n"
        "2025-01-16,-1234.56,SEK,Refund Kaffe AB,Kaffe AB\n"
    ).encode("utf-8")
    files = {"file": ("bank.csv", BytesIO(csv_data), "text/csv")}
    r = client.post("/bank/import", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 2
    lst = client.get("/bank/transactions", params={"unmatched": 1})
    assert lst.status_code == 200
    assert len(lst.json()["items"]) >= 2
    tx_id = lst.json()["items"][0]["id"]
    sug = client.get(f"/bank/transactions/{tx_id}/suggest")
    assert sug.status_code == 200
    # Accept the first suggestion if any
    items = sug.json().get("items", [])
    if items:
        acc = client.post(f"/bank/transactions/{tx_id}/accept", json={"verification_id": items[0]["verification_id"]})
        assert acc.status_code == 200


def test_bank_filters_and_bulk_accept():
    client = TestClient(app)
    # List unmatched with query filter
    lst = client.get("/bank/transactions", params={"unmatched": 1, "q": "Kaffe"})
    assert lst.status_code == 200
    items = lst.json()["items"]
    # Bulk accept no-ops with empty should 400
    r = client.post("/bank/transactions/bulk-accept", json={"items": []})
    assert r.status_code == 400
    if items:
        tx_id = items[0]["id"]
        # Get suggestion and bulk accept single
        sug = client.get(f"/bank/transactions/{tx_id}/suggest")
        if sug.json().get("items"):
            ver_id = sug.json()["items"][0]["verification_id"]
            r2 = client.post("/bank/transactions/bulk-accept", json={"items": [{"tx_id": tx_id, "verification_id": ver_id}]})
            assert r2.status_code == 200
            assert r2.json()["updated"] >= 1


def test_camt053_import():
    client = TestClient(app)
    camt = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<BkToCstmrStmt xmlns=\"urn:iso:std:iso:20022:tech:xsd:camt.053.001.04\">\n"
        "  <Stmt>\n"
        "    <Ntry>\n"
        "      <Amt Ccy=\"SEK\">100.00</Amt>\n"
        "      <CdtDbtInd>CRDT</CdtDbtInd>\n"
        "      <ValDt><Dt>2025-01-20</Dt></ValDt>\n"
        "      <NtryDtls><TxDtls><RmtInf><Ustrd>Invoice 123</Ustrd></RmtInf></TxDtls></NtryDtls>\n"
        "    </Ntry>\n"
        "  </Stmt>\n"
        "</BkToCstmrStmt>\n"
    ).encode("utf-8")
    files = {"file": ("statement.camt.xml", camt, "application/xml")}
    r = client.post("/bank/import", files=files)
    assert r.status_code == 200
    lst = client.get("/bank/transactions")
    assert lst.status_code == 200
    items = lst.json()["items"]
    assert any(abs(it["amount"]) == 100.0 for it in items)


