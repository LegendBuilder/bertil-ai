"""Swedish VAT calculation logic for invoices."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple


# Swedish VAT rates and codes (2024)
SWEDISH_VAT_RATES = {
    "SE25": Decimal("25.00"),  # Standard rate - most goods and services
    "SE12": Decimal("12.00"),  # Reduced rate - food, transport, hotels
    "SE06": Decimal("6.00"),   # Reduced rate - books, newspapers, cultural events
    "SE00": Decimal("0.00"),   # Zero rate - exports, international transport
}

# Default VAT code for most services
DEFAULT_VAT_CODE = "SE25"


def get_vat_rate(vat_code: str) -> Decimal:
    """Get VAT rate for Swedish VAT code."""
    return SWEDISH_VAT_RATES.get(vat_code.upper(), SWEDISH_VAT_RATES[DEFAULT_VAT_CODE])


def calculate_line_vat(unit_price: Decimal, quantity: Decimal, vat_rate: Decimal) -> Tuple[Decimal, Decimal]:
    """
    Calculate VAT for a single invoice line item.
    
    Returns:
        (line_total_excl_vat, vat_amount)
    """
    line_total = unit_price * quantity
    vat_amount = line_total * vat_rate / Decimal("100")
    
    # Round to 2 decimal places (Swedish kronor)
    line_total = line_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vat_amount = vat_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    return line_total, vat_amount


def calculate_invoice_totals(line_items: List[Dict]) -> Dict[str, Decimal]:
    """
    Calculate invoice totals from line items.
    
    Args:
        line_items: List of dicts with keys: unit_price, quantity, vat_code
        
    Returns:
        Dict with subtotal, vat_amount, total_amount, vat_breakdown
    """
    subtotal = Decimal("0.00")
    total_vat = Decimal("0.00")
    vat_breakdown = {}  # {vat_code: (base_amount, vat_amount)}
    
    for item in line_items:
        unit_price = Decimal(str(item["unit_price"]))
        quantity = Decimal(str(item.get("quantity", 1)))
        vat_code = item.get("vat_code", DEFAULT_VAT_CODE).upper()
        vat_rate = get_vat_rate(vat_code)
        
        line_total, line_vat = calculate_line_vat(unit_price, quantity, vat_rate)
        
        subtotal += line_total
        total_vat += line_vat
        
        # Track VAT breakdown by code
        if vat_code in vat_breakdown:
            vat_breakdown[vat_code] = (
                vat_breakdown[vat_code][0] + line_total,
                vat_breakdown[vat_code][1] + line_vat
            )
        else:
            vat_breakdown[vat_code] = (line_total, line_vat)
    
    total_amount = subtotal + total_vat
    
    return {
        "subtotal": subtotal,
        "vat_amount": total_vat,
        "total_amount": total_amount,
        "vat_breakdown": vat_breakdown
    }


def generate_invoice_number(org_id: int, current_number: int, prefix: str = None) -> str:
    """
    Generate sequential Swedish invoice number.
    
    Format: YYYY-NNNN (e.g., 2024-0001)
    """
    if prefix is None:
        from datetime import datetime
        prefix = str(datetime.now().year)
    
    next_number = current_number + 1
    return f"{prefix}-{next_number:04d}"


def validate_swedish_invoice_data(invoice_data: Dict) -> List[str]:
    """
    Validate invoice data meets Swedish legal requirements.
    
    Returns list of validation errors.
    """
    errors = []
    
    # Required fields
    required_fields = [
        "customer_name", "customer_address", "invoice_date", 
        "line_items", "seller_vat_number"
    ]
    
    for field in required_fields:
        if not invoice_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Line items validation
    line_items = invoice_data.get("line_items", [])
    if not line_items:
        errors.append("Invoice must have at least one line item")
    
    for i, item in enumerate(line_items):
        if not item.get("description"):
            errors.append(f"Line item {i+1}: Missing description")
        if not item.get("unit_price") or float(item["unit_price"]) <= 0:
            errors.append(f"Line item {i+1}: Invalid unit price")
        
        # Validate VAT code
        vat_code = item.get("vat_code", DEFAULT_VAT_CODE).upper()
        if vat_code not in SWEDISH_VAT_RATES:
            errors.append(f"Line item {i+1}: Invalid VAT code '{vat_code}'")
    
    # VAT number format (basic validation)
    vat_number = invoice_data.get("seller_vat_number", "")
    if vat_number and not vat_number.startswith("SE"):
        errors.append("Swedish VAT number must start with 'SE'")
    
    return errors


def format_amount_sek(amount: Decimal) -> str:
    """Format amount as Swedish kronor string."""
    return f"{amount:,.2f} SEK".replace(",", " ")