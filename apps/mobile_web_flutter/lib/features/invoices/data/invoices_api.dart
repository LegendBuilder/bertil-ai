import 'dart:typed_data';
import 'package:dio/dio.dart';
import '../../../shared/services/network.dart';
import '../domain/customer.dart';
import '../domain/invoice.dart';

class InvoicesApi {
  final Dio _dio;

  InvoicesApi(this._dio);

  // Customer management
  Future<List<Customer>> getCustomers() async {
    final response = await _dio.get('/invoices/customers');
    final List<dynamic> data = response.data;
    return data.map((json) => Customer.fromJson(json)).toList();
  }

  Future<Customer> createCustomer(Customer customer) async {
    final response = await _dio.post(
      '/invoices/customers',
      data: customer.toJson(),
    );
    return Customer.fromJson(response.data);
  }

  Future<Customer> getCustomer(int customerId) async {
    final response = await _dio.get('/invoices/customers/$customerId');
    return Customer.fromJson(response.data);
  }

  // Invoice management
  Future<List<Invoice>> getInvoices({
    String? status,
    int? customerId,
  }) async {
    final queryParams = <String, dynamic>{};
    if (status != null) queryParams['status'] = status;
    if (customerId != null) queryParams['customer_id'] = customerId;

    final response = await _dio.get('/invoices/', queryParameters: queryParams);
    final List<dynamic> data = response.data;
    return data.map((json) => Invoice.fromJson(json)).toList();
  }

  Future<Invoice> createInvoice(InvoiceCreate invoiceData) async {
    final response = await _dio.post(
      '/invoices/',
      data: invoiceData.toJson(),
    );
    return Invoice.fromJson(response.data);
  }

  Future<Invoice> getInvoice(int invoiceId) async {
    final response = await _dio.get('/invoices/$invoiceId');
    return Invoice.fromJson(response.data);
  }

  Future<Invoice> updateInvoice(int invoiceId, InvoiceUpdate update) async {
    final response = await _dio.patch(
      '/invoices/$invoiceId',
      data: update.toJson(),
    );
    return Invoice.fromJson(response.data);
  }

  Future<Uint8List> downloadInvoicePdf(int invoiceId) async {
    final response = await _dio.get(
      '/invoices/$invoiceId/pdf',
      options: Options(responseType: ResponseType.bytes),
    );
    return Uint8List.fromList(response.data);
  }

  Future<void> sendInvoice(int invoiceId) async {
    await _dio.post('/invoices/$invoiceId/send');
  }

  Future<InvoiceStats> getInvoiceStats() async {
    final response = await _dio.get('/invoices/dashboard/stats');
    return InvoiceStats.fromJson(response.data);
  }
}

class InvoiceStats {
  final Outstanding outstanding;
  final Outstanding overdue;
  final double monthlyRevenue;

  InvoiceStats({
    required this.outstanding,
    required this.overdue,
    required this.monthlyRevenue,
  });

  factory InvoiceStats.fromJson(Map<String, dynamic> json) {
    return InvoiceStats(
      outstanding: Outstanding.fromJson(json['outstanding']),
      overdue: Outstanding.fromJson(json['overdue']),
      monthlyRevenue: (json['monthly_revenue'] as num).toDouble(),
    );
  }
}

class Outstanding {
  final int count;
  final double amount;

  Outstanding({required this.count, required this.amount});

  factory Outstanding.fromJson(Map<String, dynamic> json) {
    return Outstanding(
      count: json['count'],
      amount: (json['amount'] as num).toDouble(),
    );
  }
}