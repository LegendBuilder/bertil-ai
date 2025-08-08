import 'package:flutter/material.dart';
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
                const SizedBox(height: 12),
                const Text('Poster:'),
                const SizedBox(height: 8),
                const Text('(visas när backend-detalj finns)'),
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


