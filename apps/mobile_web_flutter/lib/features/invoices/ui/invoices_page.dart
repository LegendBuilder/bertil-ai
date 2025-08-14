import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../shared/widgets/app_bar_accent.dart';
import '../../../shared/widgets/skeleton.dart';
import '../provider/invoices_providers.dart';
import '../domain/invoice.dart';
import 'create_invoice_page.dart';
import 'invoice_detail_page.dart';

class InvoicesPage extends ConsumerStatefulWidget {
  const InvoicesPage({super.key});

  @override
  ConsumerState<InvoicesPage> createState() => _InvoicesPageState();
}

class _InvoicesPageState extends ConsumerState<InvoicesPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final NumberFormat _currencyFormat = NumberFormat.currency(symbol: 'SEK ');

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fakturor'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(96),
          child: Column(
            children: [
              TabBar(
                controller: _tabController,
                tabs: const [
                  Tab(text: 'Alla'),
                  Tab(text: 'Utkast'),
                  Tab(text: 'Skickade'),
                  Tab(text: 'Betalda'),
                ],
              ),
              appBarAccent(context),
            ],
          ),
        ),
        actions: [
          IconButton(
            tooltip: 'Skapa faktura',
            icon: const Icon(Icons.add),
            onPressed: () => _createInvoice(context),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildStatsCard(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildInvoiceList(null),
                _buildInvoiceList('draft'),
                _buildInvoiceList('sent'),
                _buildInvoiceList('paid'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsCard() {
    final statsAsync = ref.watch(invoiceStatsProvider);
    
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: statsAsync.when(
          data: (stats) => Row(
            children: [
              Expanded(
                child: _buildStatItem(
                  'Utestående',
                  '${stats.outstanding.count}',
                  _currencyFormat.format(stats.outstanding.amount),
                  Colors.orange,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildStatItem(
                  'Försenade',
                  '${stats.overdue.count}',
                  _currencyFormat.format(stats.overdue.amount),
                  Colors.red,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildStatItem(
                  'Månadens omsättning',
                  '',
                  _currencyFormat.format(stats.monthlyRevenue),
                  Colors.green,
                ),
              ),
            ],
          ),
          loading: () => const SizedBox(
            height: 100,
            child: Padding(
              padding: EdgeInsets.all(16),
              child: SkeletonBox(width: double.infinity, height: 60),
            ),
          ),
          error: (error, stack) => Center(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text('Kunde inte ladda statistik: $error'),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatItem(String title, String count, String amount, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.bodySmall,
        ),
        if (count.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            count,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: color,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
        const SizedBox(height: 4),
        Text(
          amount,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            color: color,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildInvoiceList(String? status) {
    final invoicesAsync = ref.watch(invoicesProvider(
      status != null ? InvoiceFilter(status: status) : null
    ));

    return invoicesAsync.when(
      data: (invoices) {
        if (invoices.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.receipt_long,
                  size: 64,
                  color: Colors.grey[400],
                ),
                const SizedBox(height: 16),
                Text(
                  status == null 
                    ? 'Inga fakturor än'
                    : 'Inga ${_getStatusDisplayName(status)} fakturor',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.grey[600],
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Skapa din första faktura för att komma igång',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey[500],
                  ),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () => _createInvoice(context),
                  icon: const Icon(Icons.add),
                  label: const Text('Skapa faktura'),
                ),
              ],
            ),
          );
        }

        return RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(invoicesProvider);
            ref.invalidate(invoiceStatsProvider);
          },
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: invoices.length,
            separatorBuilder: (context, index) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final invoice = invoices[index];
              return _buildInvoiceCard(invoice);
            },
          ),
        );
      },
      loading: () => const Padding(
        padding: EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
            children: [
              SkeletonBox(width: double.infinity, height: 80),
              SizedBox(height: 8),
              SkeletonBox(width: double.infinity, height: 80),
              SizedBox(height: 8),
              SkeletonBox(width: double.infinity, height: 80),
              SizedBox(height: 8),
              SkeletonBox(width: double.infinity, height: 80),
            ],
          ),
        ),
      ),
      error: (error, stack) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Fel vid laddning av fakturor: $error'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.invalidate(invoicesProvider),
              child: const Text('Försök igen'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInvoiceCard(Invoice invoice) {
    return Card(
      child: InkWell(
        onTap: () => _viewInvoice(context, invoice.id!),
        borderRadius: BorderRadius.circular(16),
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
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  _buildStatusChip(invoice),
                ],
              ),
              const SizedBox(height: 8),
              if (invoice.customer != null)
                Text(
                  invoice.customer!.name,
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              const SizedBox(height: 4),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Förfaller: ${DateFormat('yyyy-MM-dd').format(invoice.dueDate)}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: invoice.isOverdue ? Colors.red : null,
                    ),
                  ),
                  Text(
                    _currencyFormat.format(invoice.totalAmount),
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: invoice.isPaid ? Colors.green : null,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusChip(Invoice invoice) {
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        invoice.statusDisplayName,
        style: TextStyle(
          color: textColor,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  String _getStatusDisplayName(String status) {
    switch (status) {
      case 'draft': return 'utkast';
      case 'sent': return 'skickade';
      case 'paid': return 'betalda';
      case 'overdue': return 'försenade';
      case 'cancelled': return 'avbrutna';
      default: return status;
    }
  }

  void _createInvoice(BuildContext context) {
    context.go('/invoices/create');
  }

  void _viewInvoice(BuildContext context, int invoiceId) {
    context.go('/invoices/$invoiceId');
  }
}