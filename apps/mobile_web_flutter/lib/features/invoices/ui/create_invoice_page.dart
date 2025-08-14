import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../shared/widgets/app_bar_accent.dart';
import '../provider/invoices_providers.dart';
import '../domain/customer.dart';
import '../domain/invoice.dart';

class CreateInvoicePage extends ConsumerStatefulWidget {
  const CreateInvoicePage({super.key});

  @override
  ConsumerState<CreateInvoicePage> createState() => _CreateInvoicePageState();
}

class _CreateInvoicePageState extends ConsumerState<CreateInvoicePage> {
  final _formKey = GlobalKey<FormState>();
  final NumberFormat _currencyFormat = NumberFormat.currency(symbol: 'SEK ');
  bool _isLoading = false;

  // Form controllers
  final _notesController = TextEditingController();

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final draftState = ref.watch(draftInvoiceProvider);
    final customersAsync = ref.watch(customersProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Skapa faktura'),
        bottom: appBarAccent(context),
        actions: [
          TextButton(
            onPressed: draftState.isValid && !_isLoading ? _saveInvoice : null,
            child: _isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Spara'),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildCustomerSection(customersAsync),
                    const SizedBox(height: 24),
                    _buildInvoiceDetailsSection(draftState),
                    const SizedBox(height: 24),
                    _buildLineItemsSection(draftState),
                    const SizedBox(height: 24),
                    _buildNotesSection(),
                  ],
                ),
              ),
            ),
            _buildTotalsFooter(draftState),
          ],
        ),
      ),
    );
  }

  Widget _buildCustomerSection(AsyncValue<List<Customer>> customersAsync) {
    final draftState = ref.watch(draftInvoiceProvider);
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Kund',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                TextButton.icon(
                  onPressed: () => _showCreateCustomerDialog(),
                  icon: const Icon(Icons.add, size: 18),
                  label: const Text('Ny kund'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            customersAsync.when(
              data: (customers) {
                if (customers.isEmpty) {
                  return Column(
                    children: [
                      const Text('Inga kunder än. Skapa din första kund för att fortsätta.'),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: () => _showCreateCustomerDialog(),
                        icon: const Icon(Icons.add),
                        label: const Text('Skapa kund'),
                      ),
                    ],
                  );
                }
                
                return DropdownButtonFormField<Customer>(
                  value: draftState.selectedCustomer,
                  decoration: const InputDecoration(
                    labelText: 'Välj kund *',
                    border: OutlineInputBorder(),
                  ),
                  items: customers.map((customer) {
                    return DropdownMenuItem(
                      value: customer,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(customer.name),
                          if (customer.displayAddress.isNotEmpty)
                            Text(
                              customer.displayAddress,
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Colors.grey[600],
                              ),
                            ),
                        ],
                      ),
                    );
                  }).toList(),
                  onChanged: (customer) {
                    ref.read(draftInvoiceProvider.notifier).setCustomer(customer);
                  },
                  validator: (value) {
                    if (value == null) {
                      return 'Välj en kund';
                    }
                    return null;
                  },
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stack) => Text('Fel: $error'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInvoiceDetailsSection(DraftInvoiceState draftState) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Fakturadetaljer',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              decoration: const InputDecoration(
                labelText: 'Fakturadatum',
                border: OutlineInputBorder(),
                suffixIcon: Icon(Icons.calendar_today),
              ),
              readOnly: true,
              controller: TextEditingController(
                text: DateFormat('yyyy-MM-dd').format(draftState.invoiceDate),
              ),
              onTap: () async {
                final date = await showDatePicker(
                  context: context,
                  initialDate: draftState.invoiceDate,
                  firstDate: DateTime.now().subtract(const Duration(days: 365)),
                  lastDate: DateTime.now().add(const Duration(days: 365)),
                );
                if (date != null) {
                  ref.read(draftInvoiceProvider.notifier).setInvoiceDate(date);
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLineItemsSection(DraftInvoiceState draftState) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Rader',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                IconButton(
                  onPressed: () => _showAddLineItemDialog(),
                  icon: const Icon(Icons.add_circle),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (draftState.lineItems.isEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(32),
                child: Column(
                  children: [
                    Icon(
                      Icons.receipt_long,
                      size: 48,
                      color: Colors.grey[400],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Inga rader ännu',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Lägg till produkter eller tjänster',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.grey[500],
                      ),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: () => _showAddLineItemDialog(),
                      icon: const Icon(Icons.add),
                      label: const Text('Lägg till rad'),
                    ),
                  ],
                ),
              )
            else
              Column(
                children: draftState.lineItems.asMap().entries.map((entry) {
                  final index = entry.key;
                  final item = entry.value;
                  return _buildLineItemCard(item, index);
                }).toList(),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildLineItemCard(InvoiceLineItemCreate item, int index) {
    final lineTotal = item.unitPrice * item.quantity;
    
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.description,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${item.quantity} × ${_currencyFormat.format(item.unitPrice)} (${item.vatCode})',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
            Text(
              _currencyFormat.format(lineTotal),
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            IconButton(
              onPressed: () => _editLineItem(index, item),
              icon: const Icon(Icons.edit, size: 20),
            ),
            IconButton(
              onPressed: () => ref.read(draftInvoiceProvider.notifier).removeLineItem(index),
              icon: const Icon(Icons.delete, size: 20, color: Colors.red),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNotesSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Meddelande (valfritt)',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _notesController,
              decoration: const InputDecoration(
                hintText: 'Lägg till ett meddelande till kunden...',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
              onChanged: (value) {
                ref.read(draftInvoiceProvider.notifier).setNotes(
                  value.isEmpty ? null : value,
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTotalsFooter(DraftInvoiceState draftState) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Summa exkl. moms:'),
              Text(_currencyFormat.format(draftState.subtotal)),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Moms:'),
              Text(_currencyFormat.format(draftState.vatAmount)),
            ],
          ),
          const Divider(),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Total:',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                _currencyFormat.format(draftState.totalAmount),
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showCreateCustomerDialog() {
    // TODO: Implement customer creation dialog
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Kundhantering kommer snart!')),
    );
  }

  void _showAddLineItemDialog() {
    _showLineItemDialog(null, null);
  }

  void _editLineItem(int index, InvoiceLineItemCreate item) {
    _showLineItemDialog(index, item);
  }

  void _showLineItemDialog(int? editIndex, InvoiceLineItemCreate? existingItem) {
    final descriptionController = TextEditingController(text: existingItem?.description ?? '');
    final quantityController = TextEditingController(text: existingItem?.quantity.toString() ?? '1');
    final priceController = TextEditingController(text: existingItem?.unitPrice.toString() ?? '');
    String selectedVatCode = existingItem?.vatCode ?? 'SE25';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(editIndex == null ? 'Lägg till rad' : 'Redigera rad'),
        content: SizedBox(
          width: 400,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Beskrivning *',
                  border: OutlineInputBorder(),
                ),
                autofocus: true,
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: quantityController,
                      decoration: const InputDecoration(
                        labelText: 'Antal',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                      inputFormatters: [
                        FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,3}')),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    flex: 2,
                    child: TextFormField(
                      controller: priceController,
                      decoration: const InputDecoration(
                        labelText: 'Pris (SEK) *',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                      inputFormatters: [
                        FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedVatCode,
                decoration: const InputDecoration(
                  labelText: 'Momssats',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'SE25', child: Text('25% (Standard)')),
                  DropdownMenuItem(value: 'SE12', child: Text('12% (Reducerad)')),
                  DropdownMenuItem(value: 'SE06', child: Text('6% (Reducerad)')),
                  DropdownMenuItem(value: 'SE00', child: Text('0% (Momsfri)')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    selectedVatCode = value;
                  }
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Avbryt'),
          ),
          ElevatedButton(
            onPressed: () {
              if (descriptionController.text.isNotEmpty && 
                  priceController.text.isNotEmpty) {
                final item = InvoiceLineItemCreate(
                  description: descriptionController.text,
                  quantity: double.tryParse(quantityController.text) ?? 1.0,
                  unitPrice: double.tryParse(priceController.text) ?? 0.0,
                  vatCode: selectedVatCode,
                );

                if (editIndex == null) {
                  ref.read(draftInvoiceProvider.notifier).addLineItem(item);
                } else {
                  ref.read(draftInvoiceProvider.notifier).updateLineItem(editIndex, item);
                }

                Navigator.of(context).pop();
              }
            },
            child: Text(editIndex == null ? 'Lägg till' : 'Spara'),
          ),
        ],
      ),
    );
  }

  Future<void> _saveInvoice() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final draftState = ref.read(draftInvoiceProvider);
      final invoiceData = ref.read(draftInvoiceProvider.notifier).toInvoiceCreate();
      
      final actions = ref.read(invoiceActionsProvider);
      await actions.createInvoice(invoiceData);

      if (mounted) {
        ref.read(draftInvoiceProvider.notifier).clear();
        context.go('/invoices');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Faktura skapad!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fel vid skapande av faktura: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
}