import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/services/network.dart';
import '../data/invoices_api.dart';
import '../domain/customer.dart';
import '../domain/invoice.dart';

// API provider
final invoicesApiProvider = Provider<InvoicesApi>((ref) {
  final networkService = NetworkService();
  return InvoicesApi(networkService.client);
});

// Customer providers
final customersProvider = FutureProvider<List<Customer>>((ref) async {
  final api = ref.read(invoicesApiProvider);
  return await api.getCustomers();
});

final customerProvider = FutureProvider.family<Customer, int>((ref, customerId) async {
  final api = ref.read(invoicesApiProvider);
  return await api.getCustomer(customerId);
});

// Invoice providers
final invoicesProvider = FutureProvider.family<List<Invoice>, InvoiceFilter?>((ref, filter) async {
  final api = ref.read(invoicesApiProvider);
  return await api.getInvoices(
    status: filter?.status,
    customerId: filter?.customerId,
  );
});

final invoiceProvider = FutureProvider.family<Invoice, int>((ref, invoiceId) async {
  final api = ref.read(invoicesApiProvider);
  return await api.getInvoice(invoiceId);
});

final invoiceStatsProvider = FutureProvider<InvoiceStats>((ref) async {
  final api = ref.read(invoicesApiProvider);
  return await api.getInvoiceStats();
});

// Draft invoice provider (for creating new invoices)
final draftInvoiceProvider = StateNotifierProvider<DraftInvoiceNotifier, DraftInvoiceState>((ref) {
  return DraftInvoiceNotifier();
});

// State classes
class InvoiceFilter {
  final String? status;
  final int? customerId;

  InvoiceFilter({this.status, this.customerId});
}

class DraftInvoiceState {
  final Customer? selectedCustomer;
  final DateTime invoiceDate;
  final String currency;
  final String? notes;
  final List<InvoiceLineItemCreate> lineItems;
  final bool isValid;

  DraftInvoiceState({
    this.selectedCustomer,
    required this.invoiceDate,
    this.currency = 'SEK',
    this.notes,
    this.lineItems = const [],
    this.isValid = false,
  });

  DraftInvoiceState copyWith({
    Customer? selectedCustomer,
    DateTime? invoiceDate,
    String? currency,
    String? notes,
    List<InvoiceLineItemCreate>? lineItems,
    bool? isValid,
  }) {
    return DraftInvoiceState(
      selectedCustomer: selectedCustomer ?? this.selectedCustomer,
      invoiceDate: invoiceDate ?? this.invoiceDate,
      currency: currency ?? this.currency,
      notes: notes ?? this.notes,
      lineItems: lineItems ?? this.lineItems,
      isValid: isValid ?? this.isValid,
    );
  }

  double get subtotal {
    return lineItems.fold(0.0, (sum, item) => sum + (item.unitPrice * item.quantity));
  }

  double get vatAmount {
    return lineItems.fold(0.0, (sum, item) {
      final lineTotal = item.unitPrice * item.quantity;
      final vatRate = _getVatRate(item.vatCode);
      return sum + (lineTotal * vatRate / 100);
    });
  }

  double get totalAmount => subtotal + vatAmount;

  double _getVatRate(String vatCode) {
    switch (vatCode) {
      case 'SE25': return 25.0;
      case 'SE12': return 12.0;
      case 'SE06': return 6.0;
      case 'SE00': return 0.0;
      default: return 25.0;
    }
  }
}

class DraftInvoiceNotifier extends StateNotifier<DraftInvoiceState> {
  DraftInvoiceNotifier() : super(DraftInvoiceState(invoiceDate: DateTime.now()));

  void setCustomer(Customer? customer) {
    state = state.copyWith(selectedCustomer: customer);
    _validate();
  }

  void setInvoiceDate(DateTime date) {
    state = state.copyWith(invoiceDate: date);
    _validate();
  }

  void setNotes(String? notes) {
    state = state.copyWith(notes: notes);
  }

  void addLineItem(InvoiceLineItemCreate item) {
    final newItems = [...state.lineItems, item];
    state = state.copyWith(lineItems: newItems);
    _validate();
  }

  void updateLineItem(int index, InvoiceLineItemCreate item) {
    final newItems = [...state.lineItems];
    newItems[index] = item;
    state = state.copyWith(lineItems: newItems);
    _validate();
  }

  void removeLineItem(int index) {
    final newItems = [...state.lineItems];
    newItems.removeAt(index);
    state = state.copyWith(lineItems: newItems);
    _validate();
  }

  void clear() {
    state = DraftInvoiceState(invoiceDate: DateTime.now());
  }

  void _validate() {
    final isValid = state.selectedCustomer != null && 
                   state.lineItems.isNotEmpty &&
                   state.lineItems.every((item) => 
                     item.description.isNotEmpty && 
                     item.unitPrice > 0 && 
                     item.quantity > 0
                   );
    state = state.copyWith(isValid: isValid);
  }

  InvoiceCreate toInvoiceCreate() {
    if (!state.isValid) {
      throw StateError('Cannot create invoice from invalid state');
    }

    return InvoiceCreate(
      customerId: state.selectedCustomer!.id!,
      invoiceDate: state.invoiceDate,
      currency: state.currency,
      notes: state.notes,
      lineItems: state.lineItems,
    );
  }
}

// Quick actions provider for invoice operations
final invoiceActionsProvider = Provider<InvoiceActions>((ref) {
  final api = ref.read(invoicesApiProvider);
  return InvoiceActions(api, ref);
});

class InvoiceActions {
  final InvoicesApi _api;
  final Ref _ref;

  InvoiceActions(this._api, this._ref);

  Future<Customer> createCustomer(Customer customer) async {
    final result = await _api.createCustomer(customer);
    _ref.invalidate(customersProvider);
    return result;
  }

  Future<Invoice> createInvoice(InvoiceCreate invoiceData) async {
    final result = await _api.createInvoice(invoiceData);
    _ref.invalidate(invoicesProvider);
    _ref.invalidate(invoiceStatsProvider);
    return result;
  }

  Future<Invoice> updateInvoice(int invoiceId, InvoiceUpdate update) async {
    final result = await _api.updateInvoice(invoiceId, update);
    _ref.invalidate(invoicesProvider);
    _ref.invalidate(invoiceProvider(invoiceId));
    _ref.invalidate(invoiceStatsProvider);
    return result;
  }

  Future<void> sendInvoice(int invoiceId) async {
    await _api.sendInvoice(invoiceId);
    _ref.invalidate(invoicesProvider);
    _ref.invalidate(invoiceProvider(invoiceId));
    _ref.invalidate(invoiceStatsProvider);
  }

  Future<void> markAsPaid(int invoiceId) async {
    await _api.updateInvoice(
      invoiceId, 
      InvoiceUpdate(status: 'paid', paidAt: DateTime.now())
    );
    _ref.invalidate(invoicesProvider);
    _ref.invalidate(invoiceProvider(invoiceId));
    _ref.invalidate(invoiceStatsProvider);
  }
}