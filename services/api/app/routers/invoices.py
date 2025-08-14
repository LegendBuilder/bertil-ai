"""Invoice management API endpoints."""

from __future__ import annotations

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, relationship

from ..db import get_session
from ..security import require_user, require_org
from ..models import Customer, Invoice, InvoiceLineItem, InvoiceSequence, Organization
from ..invoice_vat import (
    calculate_invoice_totals, 
    generate_invoice_number, 
    validate_swedish_invoice_data,
    DEFAULT_VAT_CODE,
    SWEDISH_VAT_RATES
)


router = APIRouter(prefix="/invoices", tags=["invoices"])


# Pydantic schemas
class CustomerCreate(BaseModel):
    name: str = Field(..., max_length=200)
    orgnr: Optional[str] = Field(None, max_length=20)
    vat_number: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=300)
    postal_code: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    country: str = Field("SE", max_length=2)
    payment_terms: int = Field(30, ge=1, le=365)


class CustomerResponse(CustomerCreate):
    id: int
    org_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceLineItemCreate(BaseModel):
    description: str = Field(..., max_length=500)
    quantity: float = Field(1.0, gt=0)
    unit_price: float = Field(..., gt=0)
    vat_code: str = Field(DEFAULT_VAT_CODE, max_length=20)
    
    @validator('vat_code')
    def validate_vat_code(cls, v):
        if v.upper() not in SWEDISH_VAT_RATES:
            raise ValueError(f"Invalid VAT code. Must be one of: {list(SWEDISH_VAT_RATES.keys())}")
        return v.upper()


class InvoiceLineItemResponse(BaseModel):
    id: int
    description: str
    quantity: float
    unit_price: float
    vat_rate: float
    vat_code: str
    line_total: float
    line_vat: float

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    customer_id: int
    invoice_date: Optional[date] = None
    currency: str = Field("SEK", max_length=3)
    notes: Optional[str] = None
    line_items: List[InvoiceLineItemCreate] = Field(..., min_items=1)
    
    @validator('invoice_date', pre=True, always=True)
    def set_invoice_date(cls, v):
        return v or date.today()


class InvoiceResponse(BaseModel):
    id: int
    org_id: int
    customer_id: int
    invoice_number: str
    invoice_date: date
    due_date: date
    currency: str
    subtotal: float
    vat_amount: float
    total_amount: float
    status: str
    notes: Optional[str]
    pdf_uri: Optional[str]
    sent_at: Optional[datetime]
    paid_at: Optional[datetime]
    created_at: datetime
    line_items: List[InvoiceLineItemResponse]
    customer: CustomerResponse

    class Config:
        from_attributes = True


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None


# API Endpoints

@router.get("/customers", response_model=List[CustomerResponse])
async def list_customers(
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """List all customers for the organization."""
    require_org(user, org_id)
    result = await db.execute(
        select(Customer).where(Customer.org_id == org_id).order_by(Customer.name)
    )
    customers = result.scalars().all()
    return customers


@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """Create a new customer."""
    require_org(user, org_id)
    customer = Customer(
        org_id=org_id,
        **customer_data.dict()
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """Get customer by ID."""
    require_org(user, org_id)
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.org_id == org_id
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """Create a new invoice."""
    require_org(user, org_id)
    
    # Verify customer exists and belongs to org
    customer_result = await db.execute(
        select(Customer).where(
            Customer.id == invoice_data.customer_id,
            Customer.org_id == org_id
        )
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get or create invoice sequence
    seq_result = await db.execute(
        select(InvoiceSequence).where(InvoiceSequence.org_id == org_id)
    )
    sequence = seq_result.scalar_one_or_none()
    if not sequence:
        sequence = InvoiceSequence(org_id=org_id, current_number=0)
        db.add(sequence)
        await db.flush()
    
    # Generate invoice number
    invoice_number = generate_invoice_number(org_id, sequence.current_number)
    
    # Calculate totals
    line_items_data = [item.dict() for item in invoice_data.line_items]
    totals = calculate_invoice_totals(line_items_data)
    
    # Calculate due date
    due_date = invoice_data.invoice_date + timedelta(days=customer.payment_terms)
    
    # Create invoice
    invoice = Invoice(
        org_id=org_id,
        customer_id=invoice_data.customer_id,
        invoice_number=invoice_number,
        invoice_date=invoice_data.invoice_date,
        due_date=due_date,
        currency=invoice_data.currency,
        subtotal=float(totals["subtotal"]),
        vat_amount=float(totals["vat_amount"]),
        total_amount=float(totals["total_amount"]),
        notes=invoice_data.notes,
        status="draft"
    )
    db.add(invoice)
    await db.flush()
    
    # Create line items
    for item_data in invoice_data.line_items:
        from ..invoice_vat import get_vat_rate
        vat_rate = get_vat_rate(item_data.vat_code)
        line_total = Decimal(str(item_data.unit_price)) * Decimal(str(item_data.quantity))
        line_vat = line_total * vat_rate / Decimal("100")
        
        line_item = InvoiceLineItem(
            invoice_id=invoice.id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            vat_rate=float(vat_rate),
            vat_code=item_data.vat_code,
            line_total=float(line_total),
            line_vat=float(line_vat)
        )
        db.add(line_item)
    
    # Update invoice sequence
    await db.execute(
        update(InvoiceSequence)
        .where(InvoiceSequence.org_id == org_id)
        .values(
            current_number=sequence.current_number + 1,
            updated_at=datetime.utcnow()
        )
    )
    
    await db.commit()
    
    # Return invoice with relationships
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.customer)
        )
        .where(Invoice.id == invoice.id)
    )
    created_invoice = result.scalar_one()
    return created_invoice


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session),
    status: Optional[str] = None,
    customer_id: Optional[int] = None
):
    """List invoices with optional filtering."""
    require_org(user, org_id)
    query = select(Invoice).options(
        selectinload(Invoice.line_items),
        selectinload(Invoice.customer)
    ).where(Invoice.org_id == org_id)
    
    if status:
        query = query.where(Invoice.status == status)
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
    
    query = query.order_by(Invoice.created_at.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """Get invoice by ID with line items."""
    require_org(user, org_id)
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.customer)
        )
        .where(
            Invoice.id == invoice_id,
            Invoice.org_id == org_id
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    updates: InvoiceUpdate,
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """Update invoice status and other fields."""
    require_org(user, org_id)
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.org_id == org_id
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    await db.commit()
    await db.refresh(invoice)
    
    # Return updated invoice with relationships
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.customer)
        )
        .where(Invoice.id == invoice_id)
    )
    updated_invoice = result.scalar_one()
    return updated_invoice


@router.get("/dashboard/stats")
async def get_invoice_stats(
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """Get invoice dashboard statistics."""
    require_org(user, org_id)
    # Outstanding invoices
    outstanding_result = await db.execute(
        select(func.count(Invoice.id), func.sum(Invoice.total_amount))
        .where(
            Invoice.org_id == org_id,
            Invoice.status.in_(["sent", "overdue"])
        )
    )
    outstanding_count, outstanding_amount = outstanding_result.one()
    
    # Overdue invoices
    overdue_result = await db.execute(
        select(func.count(Invoice.id), func.sum(Invoice.total_amount))
        .where(
            Invoice.org_id == org_id,
            Invoice.status == "overdue",
            Invoice.due_date < date.today()
        )
    )
    overdue_count, overdue_amount = overdue_result.one()
    
    # Revenue this month
    today = date.today()
    month_start = date(today.year, today.month, 1)
    revenue_result = await db.execute(
        select(func.sum(Invoice.total_amount))
        .where(
            Invoice.org_id == org_id,
            Invoice.status == "paid",
            Invoice.paid_at >= month_start
        )
    )
    monthly_revenue = revenue_result.scalar() or 0
    
    return {
        "outstanding": {
            "count": outstanding_count or 0,
            "amount": float(outstanding_amount or 0)
        },
        "overdue": {
            "count": overdue_count or 0,
            "amount": float(overdue_amount or 0)
        },
        "monthly_revenue": float(monthly_revenue)
    }


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: int,
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """Download invoice as PDF."""
    require_org(user, org_id)
    # Get invoice with relationships
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.customer)
        )
        .where(
            Invoice.id == invoice_id,
            Invoice.org_id == org_id
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get organization details
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        from ..invoice_pdf import generate_invoice_pdf
        
        # Prepare data for PDF generation
        invoice_data = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'due_date': invoice.due_date,
            'currency': invoice.currency,
            'subtotal': invoice.subtotal,
            'vat_amount': invoice.vat_amount,
            'total_amount': invoice.total_amount,
            'notes': invoice.notes,
            'vat_breakdown': {}  # TODO: Calculate from line items
        }
        
        company_data = {
            'name': organization.name,
            'address': organization.address,
            'orgnr': organization.orgnr,
            # TODO: Add VAT number and other company details
        }
        
        customer_data = {
            'name': invoice.customer.name,
            'address': invoice.customer.address,
            'postal_code': invoice.customer.postal_code,
            'city': invoice.customer.city,
            'orgnr': invoice.customer.orgnr,
            'vat_number': invoice.customer.vat_number,
            'payment_terms': invoice.customer.payment_terms
        }
        
        line_items = [
            {
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'vat_rate': item.vat_rate,
                'line_total': item.line_total
            }
            for item in invoice.line_items
        ]
        
        # Generate PDF
        pdf_bytes = generate_invoice_pdf(
            invoice_data, company_data, customer_data, line_items
        )
        
        # Return PDF response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=faktura_{invoice.invoice_number}.pdf"
            }
        )
        
    except ImportError:
        raise HTTPException(
            status_code=500, 
            detail="PDF generation not available. ReportLab library required."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: int,
    org_id: int,
    user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_session)
):
    """Send invoice via email."""
    require_org(user, org_id)
    # Get invoice with relationships
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.customer)
        )
        .where(
            Invoice.id == invoice_id,
            Invoice.org_id == org_id
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.customer.email:
        raise HTTPException(status_code=400, detail="Customer has no email address")
    
    # Get organization details
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = org_result.scalar_one_or_none()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        # Generate PDF
        from ..invoice_pdf import generate_invoice_pdf
        
        # Prepare data for PDF generation
        invoice_data = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'due_date': invoice.due_date,
            'currency': invoice.currency,
            'subtotal': invoice.subtotal,
            'vat_amount': invoice.vat_amount,
            'total_amount': invoice.total_amount,
            'notes': invoice.notes,
            'vat_breakdown': {}  # TODO: Calculate from line items
        }
        
        company_data = {
            'name': organization.name,
            'address': organization.address,
            'orgnr': organization.orgnr,
        }
        
        customer_data = {
            'name': invoice.customer.name,
            'address': invoice.customer.address,
            'postal_code': invoice.customer.postal_code,
            'city': invoice.customer.city,
            'orgnr': invoice.customer.orgnr,
            'vat_number': invoice.customer.vat_number,
            'payment_terms': invoice.customer.payment_terms
        }
        
        line_items = [
            {
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'vat_rate': item.vat_rate,
                'line_total': item.line_total
            }
            for item in invoice.line_items
        ]
        
        # Generate PDF
        pdf_bytes = generate_invoice_pdf(
            invoice_data, company_data, customer_data, line_items
        )
        
        # Send email
        from ..invoice_email import send_invoice_email
        
        email_sent = send_invoice_email(
            to_email=invoice.customer.email,
            customer_name=invoice.customer.name,
            invoice_number=invoice.invoice_number,
            total_amount=invoice.total_amount,
            due_date=invoice.due_date.strftime('%Y-%m-%d'),
            pdf_content=pdf_bytes,
            company_name=organization.name
        )
        
        if email_sent:
            # Update status to sent
            invoice.status = "sent"
            invoice.sent_at = datetime.utcnow()
            await db.commit()
            
            return {"message": "Invoice sent successfully", "invoice_id": invoice_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
    
    except ImportError:
        # Fallback: just mark as sent without email
        invoice.status = "sent"
        invoice.sent_at = datetime.utcnow()
        await db.commit()
        
        return {
            "message": "Invoice marked as sent (email not configured)", 
            "invoice_id": invoice_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send invoice: {str(e)}")


@router.get("/email/status")
async def get_email_status(
    user: dict = Depends(require_user)
):
    """Get email configuration status."""
    from ..invoice_email import InvoiceEmailSender
    
    sender = InvoiceEmailSender()
    is_configured = sender._is_configured()
    
    status = {
        "configured": is_configured,
        "smtp_server": sender.smtp_server is not None,
        "smtp_username": sender.smtp_username is not None,
        "smtp_password": sender.smtp_password is not None,
        "from_email": sender.from_email is not None,
        "smtp_port": sender.smtp_port,
        "smtp_use_tls": sender.smtp_use_tls
    }
    
    return status


@router.post("/email/test")
async def send_test_email(
    test_email: str,
    user: dict = Depends(require_user)
):
    """Send a test email to verify configuration."""
    from ..invoice_email import InvoiceEmailSender
    
    sender = InvoiceEmailSender()
    
    if not sender._is_configured():
        raise HTTPException(
            status_code=400, 
            detail="Email not configured. Check SMTP settings."
        )
    
    try:
        success = sender.send_test_email(test_email)
        if success:
            return {"message": f"Test email sent successfully to {test_email}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")