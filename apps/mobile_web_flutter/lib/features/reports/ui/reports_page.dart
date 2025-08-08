import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../provider/reports_providers.dart';
import '../data/reports_api.dart';
import '../../../shared/services/network.dart';

class ReportsPage extends ConsumerWidget {
  const ReportsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tb = ref.watch(trialBalanceProvider);
    final comp = ref.watch(complianceScoreProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Rapporter')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Momsstatus', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            tb.when(
              loading: () => const LinearProgressIndicator(),
              error: (e, st) => const Text('Kunde inte hämta bokföringsdata'),
              data: (trial) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('År ${trial.year} – Total: ${trial.total.toStringAsFixed(2)} kr'),
                    const SizedBox(height: 8),
                    comp.when(
                      loading: () => const LinearProgressIndicator(),
                      error: (e, st) => const Text('Trygghet: okänd'),
                      data: (score) => Text(score >= 80
                          ? 'Allt redo ✅'
                          : score >= 50
                              ? '⚠️ Vissa saker kvar'
                              : '❌ blockerat'),
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 16),
            Text('Export', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Builder(builder: (context) {
              final url = ReportsApi(NetworkService().client).sieExportUrl(DateTime.now().year).toString();
              return OutlinedButton.icon(
                onPressed: () {
                  // TODO: add url_launcher usage for download
                },
                icon: const Icon(Icons.download_outlined),
                label: const Text('Ladda ner SIE'),
              );
            }),
          ],
        ),
      ),
    );
  }
}


