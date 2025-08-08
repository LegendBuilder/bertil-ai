import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../provider/ledger_providers.dart';

class VerificationListPage extends ConsumerWidget {
  const VerificationListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncList = ref.watch(recentVerificationsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Verifikationer')),
      body: asyncList.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Kunde inte hämta: $e')),
        data: (list) => ListView.separated(
          itemCount: list.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (context, i) {
            final v = list[i];
            return ListTile(
              title: Text('V${v.immutableSeq} · ${v.totalAmount.toStringAsFixed(2)} ${v.currency}'),
              subtitle: Text(v.date),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => _VerificationDetailPage(id: v.id, immutableSeq: v.immutableSeq)),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _VerificationDetailPage extends ConsumerWidget {
  const _VerificationDetailPage({required this.id, required this.immutableSeq});
  final int id;
  final int immutableSeq;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.watch(ledgerApiProvider);
    return FutureBuilder(
      future: api.getVerification(id),
      builder: (context, snap) {
        if (!snap.hasData) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        final v = snap.data!;
        return Scaffold(
          appBar: AppBar(title: Text('Verifikation V$immutableSeq')),
          body: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Datum: ${v.date}'),
                Text('Total: ${v.totalAmount.toStringAsFixed(2)} ${v.currency}'),
                if (v.documentLink != null && v.documentLink!.isNotEmpty)
                  Text('Underlag: ${v.documentLink}'),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(child: Text('Audit-hash: ${v.auditHash.isEmpty ? '(saknas)' : v.auditHash}')),
                    if (v.auditHash.isNotEmpty)
                      IconButton(
                        tooltip: 'Kopiera',
                        icon: const Icon(Icons.copy_all_outlined),
                        onPressed: () => Clipboard.setData(ClipboardData(text: v.auditHash)),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                if (v.explainability != null && v.explainability!.isNotEmpty) ...[
                  const Text('Varför valde vi detta?', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 6),
                  Text(v.explainability!),
                  const SizedBox(height: 12),
                ],
                const Text('Poster:'),
                const SizedBox(height: 8),
                Expanded(
                  child: ListView.separated(
                    itemCount: v.entries.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, i) {
                      final e = v.entries[i];
                      final debit = (e['debit'] as num).toDouble();
                      final credit = (e['credit'] as num).toDouble();
                      return ListTile(
                        title: Text('${e['account']} · D ${debit.toStringAsFixed(2)} / K ${credit.toStringAsFixed(2)}'),
                        subtitle: Text(e['dimension']?.toString() ?? ''),
                      );
                    },
                  ),
                ),
                const Spacer(),
                const Text('Append-only: Rättning sker med ombokning, aldrig direkt ändring.'),
              ],
            ),
          ),
        );
      },
    );
  }
}


