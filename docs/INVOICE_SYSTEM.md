# Professional Invoice Management System

## Overview

Bertil AI now includes a complete professional invoice management system designed specifically for Swedish businesses. The system provides end-to-end functionality from customer management to PDF generation and email delivery, all while maintaining Swedish regulatory compliance.

## Features

### 🏢 Customer Management
- Complete customer database with Swedish business data
- Organization number (orgnr) and VAT number support
- Address management with postal codes and cities
- Payment terms configuration per customer
- Contact information including email for automatic invoice delivery

### 📄 Invoice Creation & Management
- Professional invoice creation with line items
- Automatic Swedish VAT categorization (SE25/SE12/SE06/RC25)
- Sequential invoice numbering per Swedish legal requirements
- Draft → Sent → Paid status workflow
- Due date calculation based on customer payment terms
- Notes and custom messaging support

### 💫 Enhanced PDF Generation
- Professional Swedish invoice layout
- Enhanced Bertil AI branding and color scheme
- Automatic VAT breakdown tables (Swedish requirement)
- Company and customer information formatting
- Swedish language throughout
- Professional footer with AI automation branding

### 📧 Email Integration
- SMTP configuration for automatic invoice sending
- Professional Swedish email templates
- PDF attachment functionality
- Email status monitoring and testing
- Production-ready configuration system

### 📊 Financial Dashboard
- Outstanding invoices tracking
- Overdue invoice monitoring
- Monthly revenue statistics
- Visual status indicators
- Quick action buttons for common tasks

### 🖥️ Flutter Integration
- "Fakturor" tab integrated into main navigation
- Consistent Material 3 design with existing app
- Mobile-responsive interface
- Real-time updates and notifications
- Seamless routing integration

## Technical Architecture

### Backend (FastAPI)
- **Database Models**: Complete invoice and customer models with Swedish compliance
- **API Endpoints**: RESTful interface with proper authentication
- **PDF Generation**: ReportLab integration with Swedish formatting
- **Email System**: SMTP integration with configurable settings
- **VAT Calculation**: Automatic Swedish VAT handling and validation
- **Security**: Consistent authentication patterns across all endpoints

### Frontend (Flutter)
- **State Management**: Riverpod providers for reactive state
- **Navigation**: go_router integration with deep linking
- **UI Components**: Consistent design system integration
- **API Client**: Dio-based HTTP client with error handling
- **Forms**: Comprehensive form validation and user experience

### Configuration
- **Environment Variables**: Complete SMTP configuration system
- **Documentation**: Comprehensive setup and usage documentation
- **Example Configuration**: Template files for easy deployment
- **Testing**: Built-in email testing and validation tools

## Swedish Compliance

### Legal Requirements
- ✅ Sequential invoice numbering
- ✅ VAT breakdown tables
- ✅ Company registration numbers
- ✅ Due date calculation
- ✅ Professional formatting standards
- ✅ Swedish language throughout

### VAT Handling
- ✅ SE25 (25% - Standard rate)
- ✅ SE12 (12% - Reduced rate)
- ✅ SE06 (6% - Reduced rate)
- ✅ RC25 (Reverse charge)
- ✅ Automatic VAT calculation and validation

## API Endpoints

### Customer Management
- `GET /invoices/customers` - List all customers
- `POST /invoices/customers` - Create new customer
- `GET /invoices/customers/{id}` - Get customer details

### Invoice Operations
- `GET /invoices/` - List invoices with filtering
- `POST /invoices/` - Create new invoice
- `GET /invoices/{id}` - Get invoice details
- `PATCH /invoices/{id}` - Update invoice status
- `GET /invoices/{id}/pdf` - Download invoice PDF
- `POST /invoices/{id}/send` - Send invoice via email

### Dashboard & Statistics
- `GET /invoices/dashboard/stats` - Get financial statistics

### Email System
- `GET /invoices/email/status` - Check email configuration
- `POST /invoices/email/test` - Send test email

## Configuration

### Required Environment Variables
```bash
# SMTP Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@company.com
SMTP_USE_TLS=true
```

### Optional Configuration
- Email templates customization
- PDF branding adjustments
- VAT rate modifications
- Currency settings

## Getting Started

1. **Backend Setup**:
   ```bash
   cd services/api
   pip install -r requirements.txt
   cp .env.example .env  # Configure email settings
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**:
   ```bash
   cd apps/mobile_web_flutter
   flutter pub get
   flutter run -d chrome
   ```

3. **Access the System**:
   - Navigate to the "Fakturor" tab in the main application
   - Create customers and invoices
   - Generate and send professional PDFs

## Testing

The system includes comprehensive testing capabilities:
- Unit tests for all business logic
- Integration tests for API endpoints
- PDF generation validation
- Email configuration testing
- End-to-end workflow testing

## Future Enhancements

- Integration with Swedish payment systems (Swish, Bankgiro)
- Automated payment tracking and reconciliation
- Advanced reporting and analytics
- Integration with external accounting systems
- Multi-language support for international customers

---

This invoice system represents a significant enhancement to Bertil AI's capabilities, providing Swedish businesses with a complete, compliant, and professional invoicing solution that maintains the platform's focus on automation and user experience excellence.