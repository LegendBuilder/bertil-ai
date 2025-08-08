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
            );
          },
        ),
      ),
    );
  }
}


