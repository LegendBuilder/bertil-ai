from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List
import xml.etree.ElementTree as ET


def parse_camt053(xml_text: str) -> List[Dict[str, Any]]:
    """Parse a minimal subset of CAMT.053 (BkToCstmrStmt) into transaction dicts.

    Returns a list of {date, amount, currency, description, counterparty_ref}.
    Notes:
      - Supports common namespaces; ignores unknown fields.
      - Uses Ntry/ValDt/Dt for date, Ntry/Amt for amount/currency.
      - Description from Ntry/NtryDtls/TxDtls/RmtInf/Ustrd or Ntry/AddtlNtryInf.
      - Counterparty from Ntry/NtryDtls/TxDtls/RltdPties/Cdtr/Nm or Dbtr/Nm.
    """
    ns = {
        "doc": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02",
        "ns": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.04",
    }
    # Try to auto-detect which ns is present
    def find(path: str) -> list[ET.Element]:
        for prefix in ("ns", "doc"):
            elems = root.findall(path.replace("PREFIX", prefix), ns)
            if elems:
                return elems
        return []

    root = ET.fromstring(xml_text)
    out: List[Dict[str, Any]] = []
    stmts = find(".//PREFIX:Stmt") or [root]
    for stmt in stmts:
        entries = stmt.findall(".//{urn:iso:std:iso:20022:tech:xsd:camt.053.001.04}Ntry")
        if not entries:
            entries = stmt.findall(".//{urn:iso:std:iso:20022:tech:xsd:camt.053.001.02}Ntry")
        for ntry in entries:
            # Date
            d_el = (
                ntry.find(".//{*}ValDt/{*}Dt")
                or ntry.find(".//{*}BookgDt/{*}Dt")
                or ntry.find(".//{*}ValDt/{*}DtTm")
            )
            dt = datetime.fromisoformat(d_el.text[:10]).date() if d_el is not None and d_el.text else date.today()
            # Amount and currency
            amt_el = ntry.find(".//{*}Amt")
            amount = float((amt_el.text or "0").replace(",", ".")) if amt_el is not None else 0.0
            currency = (amt_el.attrib.get("Ccy") if amt_el is not None else "SEK") or "SEK"
            # Description
            desc = ""
            ustrd = ntry.find(".//{*}RmtInf/{*}Ustrd")
            addtl = ntry.find(".//{*}AddtlNtryInf")
            if ustrd is not None and (ustrd.text or "").strip():
                desc = (ustrd.text or "").strip()
            elif addtl is not None and (addtl.text or "").strip():
                desc = (addtl.text or "").strip()
            # Counterparty name (creditor or debtor)
            cp = None
            for path in (".//{*}RltdPties/{*}Cdtr/{*}Nm", ".//{*}RltdPties/{*}Dbtr/{*}Nm"):
                el = ntry.find(path)
                if el is not None and (el.text or "").strip():
                    cp = el.text.strip()
                    break
            out.append({
                "date": dt,
                "amount": amount,
                "currency": currency[:3],
                "description": desc[:500],
                "counterparty_ref": cp,
            })
    return out





