import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../provider/reports_providers.dart';
import '../data/reports_api.dart';
import '../../../shared/services/network.dart';
import 'package:url_launcher/url_launcher.dart';

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
                    Consumer(builder: (context, ref, _) {
                      final vat = ref.watch(vatStatusTextProvider);
                      return vat.when(
                        loading: () => const LinearProgressIndicator(),
                        error: (e, st) => const SizedBox.shrink(),
                        data: (txt) => Text(txt, style: const TextStyle(fontWeight: FontWeight.w600)),
                      );
                    }),
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
                onPressed: () async {
                  final uri = Uri.parse(url);
                  if (await canLaunchUrl(uri)) {
                    await launchUrl(uri, mode: LaunchMode.externalApplication);
                  }
                },
                icon: const Icon(Icons.download_outlined),
                label: const Text('Ladda ner SIE'),
              );
            }),
            const SizedBox(height: 24),
            Text('Årsavslut (K2/K3)', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            const _YearEndChecklist(),
          ],
        ),
      ),
    );
  }
}

class _YearEndChecklist extends StatelessWidget {
  const _YearEndChecklist();

  @override
  Widget build(BuildContext context) {
    final items = const [
      ('Verifikationer klara', true),
      ('Periodisering klar', false),
      ('E-sign BankID', false),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final it in items)
          Row(
            children: [
              Icon(it.$2 ? Icons.check_circle_outline : Icons.radio_button_unchecked, color: it.$2 ? Colors.green : null),
              const SizedBox(width: 8),
              Text(it.$1),
            ],
          ),
      ],
    );
  }
}


