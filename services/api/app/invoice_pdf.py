"""Swedish invoice PDF generation using ReportLab."""

from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class InvoicePDFGenerator:
    """Generate Swedish compliant invoice PDFs."""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
    
    def generate_invoice_pdf(
        self,
        invoice_data: Dict,
        company_data: Dict,
        customer_data: Dict,
        line_items: List[Dict]
    ) -> bytes:
        """
        Generate Swedish invoice PDF.
        
        Args:
            invoice_data: Invoice details (number, date, totals, etc.)
            company_data: Seller company information  
            customer_data: Customer information
            line_items: List of invoice line items
            
        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Build PDF content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles for Bertil AI Swedish invoices
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=20,
            textColor=colors.HexColor('#1f4788'),
            fontName='Helvetica-Bold'
        )
        
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        brand_style = ParagraphStyle(
            'BrandStyle',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#1f4788'),
            fontName='Helvetica-Bold'
        )
        
        # Bertil AI branded header
        header_table_data = [
            [Paragraph("Bertil AI", brand_style), Paragraph("FAKTURA", title_style)]
        ]
        
        header_table = Table(
            header_table_data,
            colWidths=[90*mm, 90*mm]
        )
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 5*mm))
        
        # Subtitle with tagline
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Fullservice AI-bokföring och skattoptimering", subtitle_style))
        story.append(Spacer(1, 10*mm))
        
        # Company and customer information side by side
        company_customer_data = [
            [self._format_company_info(company_data), self._format_customer_info(customer_data)]
        ]
        
        company_customer_table = Table(
            company_customer_data,
            colWidths=[90*mm, 90*mm]
        )
        company_customer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(company_customer_table)
        story.append(Spacer(1, 15*mm))
        
        # Invoice details
        invoice_details_data = [
            ['Fakturanummer:', invoice_data['invoice_number']],
            ['Fakturadatum:', invoice_data['invoice_date'].strftime('%Y-%m-%d')],
            ['Förfallodatum:', invoice_data['due_date'].strftime('%Y-%m-%d')],
            ['Betalningsvillkor:', f"{customer_data.get('payment_terms', 30)} dagar"],
            ['Valuta:', invoice_data.get('currency', 'SEK')]
        ]
        
        invoice_details_table = Table(
            invoice_details_data,
            colWidths=[40*mm, 50*mm]
        )
        invoice_details_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        
        story.append(invoice_details_table)
        story.append(Spacer(1, 10*mm))
        
        # Line items table
        story.append(self._create_line_items_table(line_items))
        story.append(Spacer(1, 10*mm))
        
        # Totals table
        story.append(self._create_totals_table(invoice_data))
        story.append(Spacer(1, 15*mm))
        
        # VAT breakdown (Swedish requirement)
        vat_table = self._create_vat_breakdown_table(invoice_data)
        if vat_table:  # Only add if table has content
            story.append(vat_table)
            story.append(Spacer(1, 10*mm))
        
        # Footer with payment information
        if invoice_data.get('notes'):
            story.append(Paragraph(f"<b>Meddelande:</b> {invoice_data['notes']}", styles['Normal']))
            story.append(Spacer(1, 5*mm))
        
        # Enhanced payment information with Bertil AI branding
        payment_info = """
        <b>Betalningsinformation:</b><br/>
        Vänligen ange fakturanummer vid betalning.<br/>
        Vid försenad betalning debiteras dröjsmålsränta enligt räntelagen.<br/><br/>
        <b>Swish:</b> Bertil AI (om tillgängligt)<br/>
        <b>Bankgiro:</b> Kontakta oss för kontouppgifter
        """
        story.append(Paragraph(payment_info, styles['Normal']))
        story.append(Spacer(1, 10*mm))
        
        # Bertil AI footer
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=1  # Center alignment
        )
        
        footer_text = """
        <b>Bertil AI</b> - Sveriges första AI-baserade bokföringstjänst<br/>
        Automatisk bokföring • Skatteoptimering • Compliance • 99% automation<br/>
        www.bertil.ai • Genererad automatiskt med AI
        """
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _format_company_info(self, company_data: Dict) -> str:
        """Format company information for invoice header."""
        lines = [
            f"<b>{company_data['name']}</b>",
            company_data.get('address', ''),
        ]
        
        if company_data.get('postal_code') and company_data.get('city'):
            lines.append(f"{company_data['postal_code']} {company_data['city']}")
        
        if company_data.get('orgnr'):
            lines.append(f"Org.nr: {company_data['orgnr']}")
        
        if company_data.get('vat_number'):
            lines.append(f"Momsreg.nr: {company_data['vat_number']}")
        
        return '<br/>'.join(line for line in lines if line)
    
    def _format_customer_info(self, customer_data: Dict) -> str:
        """Format customer information for invoice."""
        lines = [
            f"<b>Till:</b>",
            f"<b>{customer_data['name']}</b>",
            customer_data.get('address', ''),
        ]
        
        if customer_data.get('postal_code') and customer_data.get('city'):
            lines.append(f"{customer_data['postal_code']} {customer_data['city']}")
        
        if customer_data.get('orgnr'):
            lines.append(f"Org.nr: {customer_data['orgnr']}")
        
        if customer_data.get('vat_number'):
            lines.append(f"Momsreg.nr: {customer_data['vat_number']}")
        
        return '<br/>'.join(line for line in lines if line)
    
    def _create_line_items_table(self, line_items: List[Dict]) -> Table:
        """Create the line items table."""
        # Table headers
        headers = ['Beskrivning', 'Antal', 'Pris', 'Moms%', 'Summa']
        
        # Table data
        data = [headers]
        
        for item in line_items:
            data.append([
                item['description'],
                f"{item['quantity']:.2f}",
                f"{item['unit_price']:.2f} SEK",
                f"{item['vat_rate']:.0f}%",
                f"{item['line_total']:.2f} SEK"
            ])
        
        table = Table(
            data,
            colWidths=[80*mm, 20*mm, 30*mm, 20*mm, 30*mm]
        )
        
        table.setStyle(TableStyle([
            # Header style with Bertil AI colors
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            
            # Content style
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Right align numbers
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Left align description
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Alternating row colors with subtle Bertil AI accent
            *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')) 
              for i in range(2, len(data), 2)]
        ]))
        
        return table
    
    def _create_totals_table(self, invoice_data: Dict) -> Table:
        """Create the invoice totals table."""
        data = [
            ['Summa exkl. moms:', f"{invoice_data['subtotal']:.2f} SEK"],
            ['Moms:', f"{invoice_data['vat_amount']:.2f} SEK"],
            ['<b>Total att betala:</b>', f"<b>{invoice_data['total_amount']:.2f} SEK</b>"]
        ]
        
        table = Table(
            data,
            colWidths=[40*mm, 30*mm],
            hAlign='RIGHT'
        )
        
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 2), (-1, 2), 2, colors.HexColor('#1f4788')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#e8f0fe')),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#1f4788')),
        ]))
        
        return table
    
    def _create_vat_breakdown_table(self, invoice_data: Dict) -> Table:
        """Create VAT breakdown table (Swedish requirement)."""
        # Extract VAT breakdown from invoice data
        vat_breakdown = invoice_data.get('vat_breakdown', {})
        
        if not vat_breakdown:
            return None  # Return None if no breakdown
        
        headers = ['Momssats', 'Underlag', 'Momsbelopp']
        data = [headers]
        
        for vat_code, (base_amount, vat_amount) in vat_breakdown.items():
            vat_rate = vat_code.replace('SE', '') + '%'
            data.append([
                vat_rate,
                f"{base_amount:.2f} SEK",
                f"{vat_amount:.2f} SEK"
            ])
        
        table = Table(
            data,
            colWidths=[30*mm, 30*mm, 30*mm],
            hAlign='LEFT'
        )
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ]))
        
        return table


def generate_invoice_pdf(
    invoice_data: Dict,
    company_data: Dict,
    customer_data: Dict,
    line_items: List[Dict]
) -> bytes:
    """
    Convenience function to generate invoice PDF.
    
    Args:
        invoice_data: Invoice details
        company_data: Company information
        customer_data: Customer information  
        line_items: Invoice line items
        
    Returns:
        PDF bytes
    """
    generator = InvoicePDFGenerator()
    return generator.generate_invoice_pdf(
        invoice_data, company_data, customer_data, line_items
    )