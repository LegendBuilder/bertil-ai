import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../shared/widgets/app_bar_accent.dart';
import '../provider/invoices_providers.dart';
import '../domain/invoice.dart';

class InvoiceDetailPage extends ConsumerWidget {
  final int invoiceId;

  const InvoiceDetailPage({
    super.key,
    required this.invoiceId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final invoiceAsync = ref.watch(invoiceProvider(invoiceId));
    final currencyFormat = NumberFormat.currency(symbol: 'SEK ');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Faktura'),
        bottom: appBarAccent(context),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) => _handleMenuAction(context, ref, value),
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'download_pdf',
                child: ListTile(
                  leading: Icon(Icons.download),
                  title: Text('Ladda ner PDF'),
                ),
              ),
              const PopupMenuItem(
                value: 'send',
                child: ListTile(
                  leading: Icon(Icons.send),
                  title: Text('Skicka'),
                ),
              ),
              const PopupMenuItem(
                value: 'mark_paid',
                child: ListTile(
                  leading: Icon(Icons.check_circle),
                  title: Text('Markera som betald'),
                ),
              ),
            ],
          ),
        ],
      ),
      body: invoiceAsync.when(
        data: (invoice) => _buildInvoiceDetail(context, ref, invoice, currencyFormat),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Fel vid laddning av faktura: $error'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.invalidate(invoiceProvider(invoiceId)),
                child: const Text('Försök igen'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInvoiceDetail(
    BuildContext context,
    WidgetRef ref,
    Invoice invoice,
    NumberFormat currencyFormat,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeaderCard(context, invoice, currencyFormat),
          const SizedBox(height: 16),
          _buildCustomerCard(context, invoice),
          const SizedBox(height: 16),
          _buildLineItemsCard(context, invoice, currencyFormat),
          const SizedBox(height: 16),
          _buildTotalsCard(context, invoice, currencyFormat),
          if (invoice.notes?.isNotEmpty == true) ...[
            const SizedBox(height: 16),
            _buildNotesCard(context, invoice),
          ],
          const SizedBox(height: 16),
          _buildActionButtons(context, ref, invoice),
        ],
      ),
    );
  }

  Widget _buildHeaderCard(BuildContext context, Invoice invoice, NumberFormat currencyFormat) {
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
                  invoice.invoiceNumber,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                _buildStatusChip(context, invoice),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Fakturadatum',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                      Text(
                        DateFormat('yyyy-MM-dd').format(invoice.invoiceDate),
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Förfallodatum',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                      Text(
                        DateFormat('yyyy-MM-dd').format(invoice.dueDate),
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: invoice.isOverdue ? Colors.red : null,
                          fontWeight: invoice.isOverdue ? FontWeight.bold : null,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Totalbelopp',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Text(
                  currencyFormat.format(invoice.totalAmount),
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: invoice.isPaid ? Colors.green : null,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCustomerCard(BuildContext context, Invoice invoice) {
    final customer = invoice.customer;
    if (customer == null) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Kund',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              customer.name,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            if (customer.displayAddress.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                customer.displayAddress,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
            if (customer.orgnr?.isNotEmpty == true) ...[
              const SizedBox(height: 4),
              Text(
                'Org.nr: ${customer.orgnr}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey[600],
                ),
              ),
            ],
            if (customer.email?.isNotEmpty == true) ...[
              const SizedBox(height: 4),
              Text(
                customer.email!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey[600],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildLineItemsCard(BuildContext context, Invoice invoice, NumberFormat currencyFormat) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Rader',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Table(
              columnWidths: const {
                0: FlexColumnWidth(3),
                1: FlexColumnWidth(1),
                2: FlexColumnWidth(1.5),
                3: FlexColumnWidth(1),
                4: FlexColumnWidth(1.5),
              },
              children: [
                TableRow(
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                  ),
                  children: [
                    _buildTableHeader('Beskrivning'),
                    _buildTableHeader('Antal'),
                    _buildTableHeader('Pris'),
                    _buildTableHeader('Moms'),
                    _buildTableHeader('Summa'),
                  ],
                ),
                ...invoice.lineItems.map((item) => TableRow(
                  children: [
                    _buildTableCell(item.description),
                    _buildTableCell(item.quantity.toString()),
                    _buildTableCell(currencyFormat.format(item.unitPrice)),
                    _buildTableCell('${item.vatRate.toInt()}%'),
                    _buildTableCell(currencyFormat.format(item.lineTotal)),
                  ],
                )),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTableHeader(String text) {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Text(
        text,
        style: const TextStyle(
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildTableCell(String text) {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Text(
        text,
        style: const TextStyle(fontSize: 12),
      ),
    );
  }

  Widget _buildTotalsCard(BuildContext context, Invoice invoice, NumberFormat currencyFormat) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Summa exkl. moms:'),
                Text(currencyFormat.format(invoice.subtotal)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Moms:'),
                Text(currencyFormat.format(invoice.vatAmount)),
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
                  currencyFormat.format(invoice.totalAmount),
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNotesCard(BuildContext context, Invoice invoice) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Meddelande',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              invoice.notes!,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusChip(BuildContext context, Invoice invoice) {
    Color backgroundColor;
    Color textColor = Colors.white;
    
    switch (invoice.status) {
      case 'draft':
        backgroundColor = Colors.grey;
        break;
      case 'sent':
        backgroundColor = Colors.blue;
        break;
      case 'paid':
        backgroundColor = Colors.green;
        break;
      case 'overdue':
        backgroundColor = Colors.red;
        break;
      case 'cancelled':
        backgroundColor = Colors.red[300]!;
        break;
      default:
        backgroundColor = Colors.grey;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        invoice.statusDisplayName,
        style: TextStyle(
          color: textColor,
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context, WidgetRef ref, Invoice invoice) {
    return Column(
      children: [
        if (invoice.isDraft) ...[
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => _sendInvoice(context, ref, invoice),
              icon: const Icon(Icons.send),
              label: const Text('Skicka faktura'),
            ),
          ),
          const SizedBox(height: 8),
        ],
        if (!invoice.isPaid) ...[
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: () => _markAsPaid(context, ref, invoice),
              icon: const Icon(Icons.check_circle),
              label: const Text('Markera som betald'),
            ),
          ),
          const SizedBox(height: 8),
        ],
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => _downloadPdf(context, ref, invoice),
            icon: const Icon(Icons.download),
            label: const Text('Ladda ner PDF'),
          ),
        ),
      ],
    );
  }

  void _handleMenuAction(BuildContext context, WidgetRef ref, String action) {
    final invoiceAsync = ref.read(invoiceProvider(invoiceId));
    invoiceAsync.whenData((invoice) {
      switch (action) {
        case 'download_pdf':
          _downloadPdf(context, ref, invoice);
          break;
        case 'send':
          _sendInvoice(context, ref, invoice);
          break;
        case 'mark_paid':
          _markAsPaid(context, ref, invoice);
          break;
      }
    });
  }

  Future<void> _downloadPdf(BuildContext context, WidgetRef ref, Invoice invoice) async {
    try {
      final actions = ref.read(invoiceActionsProvider);
      // TODO: Implement PDF download
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('PDF-nedladdning kommer snart!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Fel vid nedladdning: $e')),
      );
    }
  }

  Future<void> _sendInvoice(BuildContext context, WidgetRef ref, Invoice invoice) async {
    try {
      final actions = ref.read(invoiceActionsProvider);
      await actions.sendInvoice(invoice.id!);
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Faktura skickad!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Fel vid skickande: $e')),
      );
    }
  }

  Future<void> _markAsPaid(BuildContext context, WidgetRef ref, Invoice invoice) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Markera som betald'),
        content: Text('Är du säker på att faktura ${invoice.invoiceNumber} är betald?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Avbryt'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Ja, markera som betald'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        final actions = ref.read(invoiceActionsProvider);
        await actions.markAsPaid(invoice.id!);
        
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Faktura markerad som betald!')),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fel vid uppdatering: $e')),
        );
      }
    }
  }
}