"""Email sending functionality for invoices."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Optional

from .config import settings


class InvoiceEmailSender:
    """Send invoice emails with attachments."""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'smtp_server', None)
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_username = getattr(settings, 'smtp_username', None)
        self.smtp_password = getattr(settings, 'smtp_password', None)
        self.from_email = getattr(settings, 'from_email', None)
        self.smtp_use_tls = getattr(settings, 'smtp_use_tls', True)
        
    def send_invoice_email(
        self,
        to_email: str,
        customer_name: str,
        invoice_number: str,
        total_amount: float,
        due_date: str,
        pdf_content: bytes,
        company_name: str = "Bertil AI"
    ) -> bool:
        """
        Send invoice via email with PDF attachment.
        
        Args:
            to_email: Customer email address
            customer_name: Customer name
            invoice_number: Invoice number
            total_amount: Total amount
            due_date: Due date string
            pdf_content: PDF file content as bytes
            company_name: Sender company name
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._is_configured():
            raise ValueError("Email sending not configured. Check SMTP settings.")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f"Faktura {invoice_number} från {company_name}"
            
            # Email body in Swedish
            body = self._create_email_body(
                customer_name, invoice_number, total_amount, due_date, company_name
            )
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Attach PDF
            pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition', 
                'attachment', 
                filename=f'faktura_{invoice_number}.pdf'
            )
            msg.attach(pdf_attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                text = msg.as_string()
                server.sendmail(self.from_email, to_email, text)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _create_email_body(
        self, 
        customer_name: str, 
        invoice_number: str, 
        total_amount: float, 
        due_date: str,
        company_name: str
    ) -> str:
        """Create Swedish invoice email body."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1f4788;">Faktura från {company_name}</h2>
                
                <p>Hej {customer_name},</p>
                
                <p>Bifogat finner du faktura <strong>{invoice_number}</strong> på totalt <strong>{total_amount:,.2f} SEK</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1f4788;">Fakturauppgifter</h3>
                    <p><strong>Fakturanummer:</strong> {invoice_number}</p>
                    <p><strong>Belopp:</strong> {total_amount:,.2f} SEK</p>
                    <p><strong>Förfallodatum:</strong> {due_date}</p>
                </div>
                
                <p>Vänligen betala senast <strong>{due_date}</strong>. Ange fakturanummer som referens vid betalning.</p>
                
                <p>Vid frågor om denna faktura, kontakta oss på denna e-postadress.</p>
                
                <p>Tack för ditt förtroende!</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <div style="font-size: 12px; color: #666;">
                    <p><strong>{company_name}</strong></p>
                    <p>Detta meddelande skickades automatiskt av Bertil AI.</p>
                    <p>Vid försenad betalning debiteras dröjsmålsränta enligt räntelagen.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _is_configured(self) -> bool:
        """Check if SMTP settings are configured."""
        return all([
            self.smtp_server,
            self.smtp_username,
            self.smtp_password,
            self.from_email
        ])
    
    def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify configuration."""
        if not self._is_configured():
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "Test från Bertil AI"
            
            body = """
            <html>
            <body>
                <h2>Test-meddelande</h2>
                <p>Detta är ett test-meddelande från Bertil AI för att verifiera e-postkonfigurationen.</p>
                <p>Om du får detta meddelande fungerar e-postutskicket korrekt.</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                text = msg.as_string()
                server.sendmail(self.from_email, to_email, text)
            
            return True
            
        except Exception as e:
            print(f"Failed to send test email: {e}")
            return False


# Convenience function
def send_invoice_email(
    to_email: str,
    customer_name: str,
    invoice_number: str,
    total_amount: float,
    due_date: str,
    pdf_content: bytes,
    company_name: str = "Bertil AI"
) -> bool:
    """Send invoice email - convenience function."""
    sender = InvoiceEmailSender()
    return sender.send_invoice_email(
        to_email, customer_name, invoice_number, 
        total_amount, due_date, pdf_content, company_name
    )