from __future__ import annotations

from typing import Any, Dict, List


class FortnoxStubClient:
    """Stubbed Fortnox client for local/dev. Does not call external APIs."""

    def __init__(self, *_: Any, **__: Any) -> None:  # ignore credentials
        pass

    async def exchange_code(self, code: str) -> Dict[str, Any]:
        return {"access_token": f"stub-token-{code}", "scope": "invoices receipts bank", "expires_in": 3600}

    async def list_receipts(self, access_token: str) -> List[Dict[str, Any]]:
        # Minimal payload to emulate typical receipt objects
        return [
            {"id": "R1", "date": "2025-01-12", "total": 123.45, "currency": "SEK", "vendor": "Kaffe AB"},
        ]

    async def list_bank_transactions(self, access_token: str) -> List[Dict[str, Any]]:
        return [
            {"date": "2025-01-13", "amount": 123.45, "currency": "SEK", "description": "Card Kaffe AB", "counterparty": "Kaffe AB"},
        ]


def get_fortnox_client(stub: bool = True):
    if stub:
        return FortnoxStubClient()
    # A real client would be returned here when credentials/keys are configured
    return FortnoxStubClient()





