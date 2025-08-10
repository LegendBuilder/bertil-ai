from __future__ import annotations

from services.api.app.vat_mapping import summarize_codes


def test_summarize_codes_oss_rc():
    rows = [("SE25", 100.0), ("SE12", 50.0), ("SE06", 25.0), ("RC25", 80.0), ("EU-RC-SERV", 120.0), ("OSS-LOW", 60.0)]
    totals = summarize_codes(rows)
    assert totals["base25"] == 100.0
    assert totals["base12"] == 50.0
    assert totals["base6"] == 25.0
    assert totals["rc_base"] == 200.0
    assert totals["oss_sales"] == 60.0


def test_summarize_codes_edge_se12_caps_and_oss_rates():
    rows = [
        ("SE12", 1000.0),  # food services
        ("SE12", 50.49),   # small receipt
        ("SE25", 200.0),
        ("OSS-HIGH", 300.0),
        ("OSS-LOW", 120.0),
    ]
    totals = summarize_codes(rows)
    assert totals["base12"] == 1050.49
    assert totals["base25"] == 200.0
    # We only track combined OSS sales amount in summarize_codes
    assert totals["oss_sales"] == 420.0





