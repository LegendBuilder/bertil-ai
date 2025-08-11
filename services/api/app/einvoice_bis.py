from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET


def generate_bis(invoice: dict) -> str:
    """Generate a minimal Peppol BIS Billing 3 style XML (not certified) for offline use.
    Expects invoice={ 'id', 'issue_date', 'supplier':{'name'}, 'customer':{'name'}, 'lines':[{'id','name','qty','price'}] }.
    """
    root = Element("Invoice")
    SubElement(root, "ID").text = str(invoice.get("id") or "INV-1")
    SubElement(root, "IssueDate").text = str(invoice.get("issue_date") or "2025-01-15")
    acct = SubElement(root, "AccountingSupplierParty")
    SubElement(acct, "Name").text = (invoice.get("supplier", {}) or {}).get("name", "Supplier")
    cust = SubElement(root, "AccountingCustomerParty")
    SubElement(cust, "Name").text = (invoice.get("customer", {}) or {}).get("name", "Customer")
    lines = invoice.get("lines") or []
    for ln in lines:
        il = SubElement(root, "InvoiceLine")
        SubElement(il, "ID").text = str(ln.get("id") or "1")
        SubElement(il, "Name").text = str(ln.get("name") or "Item")
        SubElement(il, "InvoicedQuantity").text = str(ln.get("qty") or 1)
        SubElement(il, "PriceAmount").text = f"{float(ln.get('price') or 0.0):.2f}"
    return tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def parse_bis(xml: str) -> dict:
    """Parse the minimal Invoice XML created above into a dict (offline preview only)."""
    tree = ET.fromstring(xml)
    out = {
        "id": (tree.findtext("ID") or "").strip(),
        "issue_date": (tree.findtext("IssueDate") or "").strip(),
        "supplier": {"name": (tree.findtext("AccountingSupplierParty/Name") or "").strip()},
        "customer": {"name": (tree.findtext("AccountingCustomerParty/Name") or "").strip()},
        "lines": [],
    }
    for il in tree.findall("InvoiceLine"):
        out["lines"].append({
            "id": (il.findtext("ID") or "").strip(),
            "name": (il.findtext("Name") or "").strip(),
            "qty": float((il.findtext("InvoicedQuantity") or "0").replace(",", ".") or 0),
            "price": float((il.findtext("PriceAmount") or "0").replace(",", ".") or 0),
        })
    return out










