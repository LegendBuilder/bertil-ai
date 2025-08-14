import 'customer.dart';

class Invoice {
  final int? id;
  final int? orgId;
  final int customerId;
  final String invoiceNumber;
  final DateTime invoiceDate;
  final DateTime dueDate;
  final String currency;
  final double subtotal;
  final double vatAmount;
  final double totalAmount;
  final String status;
  final String? notes;
  final String? pdfUri;
  final DateTime? sentAt;
  final DateTime? paidAt;
  final DateTime? createdAt;
  final List<InvoiceLineItem> lineItems;
  final Customer? customer;

  Invoice({
    this.id,
    this.orgId,
    required this.customerId,
    required this.invoiceNumber,
    required this.invoiceDate,
    required this.dueDate,
    this.currency = 'SEK',
    required this.subtotal,
    required this.vatAmount,
    required this.totalAmount,
    this.status = 'draft',
    this.notes,
    this.pdfUri,
    this.sentAt,
    this.paidAt,
    this.createdAt,
    this.lineItems = const [],
    this.customer,
  });

  factory Invoice.fromJson(Map<String, dynamic> json) {
    return Invoice(
      id: json['id'],
      orgId: json['org_id'],
      customerId: json['customer_id'],
      invoiceNumber: json['invoice_number'],
      invoiceDate: DateTime.parse(json['invoice_date']),
      dueDate: DateTime.parse(json['due_date']),
      currency: json['currency'] ?? 'SEK',
      subtotal: (json['subtotal'] as num).toDouble(),
      vatAmount: (json['vat_amount'] as num).toDouble(),
      totalAmount: (json['total_amount'] as num).toDouble(),
      status: json['status'] ?? 'draft',
      notes: json['notes'],
      pdfUri: json['pdf_uri'],
      sentAt: json['sent_at'] != null ? DateTime.parse(json['sent_at']) : null,
      paidAt: json['paid_at'] != null ? DateTime.parse(json['paid_at']) : null,
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
      lineItems: json['line_items'] != null
          ? (json['line_items'] as List)
              .map((item) => InvoiceLineItem.fromJson(item))
              .toList()
          : [],
      customer: json['customer'] != null ? Customer.fromJson(json['customer']) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      if (orgId != null) 'org_id': orgId,
      'customer_id': customerId,
      'invoice_number': invoiceNumber,
      'invoice_date': invoiceDate.toIso8601String().split('T')[0],
      'due_date': dueDate.toIso8601String().split('T')[0],
      'currency': currency,
      'subtotal': subtotal,
      'vat_amount': vatAmount,
      'total_amount': totalAmount,
      'status': status,
      if (notes != null) 'notes': notes,
      if (pdfUri != null) 'pdf_uri': pdfUri,
      if (sentAt != null) 'sent_at': sentAt!.toIso8601String(),
      if (paidAt != null) 'paid_at': paidAt!.toIso8601String(),
      if (createdAt != null) 'created_at': createdAt!.toIso8601String(),
      'line_items': lineItems.map((item) => item.toJson()).toList(),
      if (customer != null) 'customer': customer!.toJson(),
    };
  }

  bool get isOverdue => status != 'paid' && DateTime.now().isAfter(dueDate);
  bool get isPaid => status == 'paid';
  bool get isDraft => status == 'draft';

  String get statusDisplayName {
    switch (status) {
      case 'draft': return 'Utkast';
      case 'sent': return 'Skickad';
      case 'paid': return 'Betald';
      case 'overdue': return 'Försenad';
      case 'cancelled': return 'Avbruten';
      default: return status;
    }
  }

  @override
  String toString() => 'Invoice(id: $id, number: $invoiceNumber, total: $totalAmount $currency)';
}

class InvoiceLineItem {
  final int? id;
  final String description;
  final double quantity;
  final double unitPrice;
  final double vatRate;
  final String? vatCode;
  final double lineTotal;
  final double lineVat;

  InvoiceLineItem({
    this.id,
    required this.description,
    this.quantity = 1.0,
    required this.unitPrice,
    required this.vatRate,
    this.vatCode,
    required this.lineTotal,
    required this.lineVat,
  });

  factory InvoiceLineItem.fromJson(Map<String, dynamic> json) {
    return InvoiceLineItem(
      id: json['id'],
      description: json['description'],
      quantity: (json['quantity'] as num).toDouble(),
      unitPrice: (json['unit_price'] as num).toDouble(),
      vatRate: (json['vat_rate'] as num).toDouble(),
      vatCode: json['vat_code'],
      lineTotal: (json['line_total'] as num).toDouble(),
      lineVat: (json['line_vat'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'description': description,
      'quantity': quantity,
      'unit_price': unitPrice,
      'vat_rate': vatRate,
      if (vatCode != null) 'vat_code': vatCode,
      'line_total': lineTotal,
      'line_vat': lineVat,
    };
  }
}

class InvoiceLineItemCreate {
  final String description;
  final double quantity;
  final double unitPrice;
  final String vatCode;

  InvoiceLineItemCreate({
    required this.description,
    this.quantity = 1.0,
    required this.unitPrice,
    this.vatCode = 'SE25',
  });

  Map<String, dynamic> toJson() {
    return {
      'description': description,
      'quantity': quantity,
      'unit_price': unitPrice,
      'vat_code': vatCode,
    };
  }
}

class InvoiceCreate {
  final int customerId;
  final DateTime? invoiceDate;
  final String currency;
  final String? notes;
  final List<InvoiceLineItemCreate> lineItems;

  InvoiceCreate({
    required this.customerId,
    this.invoiceDate,
    this.currency = 'SEK',
    this.notes,
    required this.lineItems,
  });

  Map<String, dynamic> toJson() {
    return {
      'customer_id': customerId,
      if (invoiceDate != null) 'invoice_date': invoiceDate!.toIso8601String().split('T')[0],
      'currency': currency,
      if (notes != null) 'notes': notes,
      'line_items': lineItems.map((item) => item.toJson()).toList(),
    };
  }
}

class InvoiceUpdate {
  final String? status;
  final String? notes;
  final DateTime? paidAt;

  InvoiceUpdate({
    this.status,
    this.notes,
    this.paidAt,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {};
    if (status != null) data['status'] = status;
    if (notes != null) data['notes'] = notes;
    if (paidAt != null) data['paid_at'] = paidAt!.toIso8601String();
    return data;
  }
}