# Changelog

All notable changes to Bertil AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Professional Invoice Management System** - Complete invoicing solution with Swedish compliance
  - Full CRUD operations for customers and invoices
  - Automatic Swedish VAT categorization (SE25/SE12/SE06/RC25)
  - Sequential invoice numbering system according to Swedish requirements
  - Professional PDF generation with enhanced Bertil AI branding
  - SMTP email integration for automatic invoice sending
  - Customer management with organization number and VAT registration
  - Invoice status tracking (Draft → Sent → Paid)
  - Dashboard with outstanding, overdue, and monthly revenue statistics
  - Swedish-compliant invoice layout and formatting
  - Email configuration and testing endpoints
  - Integration with main Flutter navigation ("Fakturor" tab)

### Enhanced
- **API Security** - Updated all invoice endpoints to use consistent authentication patterns
- **PDF Templates** - Enhanced branding with Bertil AI colors and professional Swedish design
- **Email System** - Production-ready SMTP configuration with TLS support
- **Flutter UI** - Consistent Material 3 design integration with existing app patterns
- **Documentation** - Updated README with comprehensive invoice system documentation

### Technical
- Added complete invoice database models with Swedish compliance fields
- Implemented sequential invoice numbering with organization-specific sequences
- Created comprehensive test suite for invoice functionality
- Added environment configuration template (.env.example) with email settings
- Enhanced PDF generation with ReportLab integration and Swedish formatting
- Implemented proper error handling and validation for all invoice operations

## [Previous Releases]

Previous changelog entries would be documented here as features are released.