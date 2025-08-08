import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../features/auth/provider/auth_providers.dart';
import '../provider/ledger_providers.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Hem')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!auth.isAuthenticated)
              const MaterialBanner(
                content: Text('Ej inloggad – logga in för att spara och bokföra.'),
                actions: [SizedBox.shrink()],
              ),
            Consumer(builder: (context, ref, _) {
              final trust = ref.watch(trustSummaryProvider);
              return trust.when(
                loading: () => const LinearProgressIndicator(),
                error: (e, st) => const Chip(label: Text('Trygghet: okänd')),
                data: (t) {
                  final color = t.score >= 80
                      ? Colors.green
                      : t.score >= 50
                          ? Colors.orange
                          : Colors.red;
                  final label = t.score >= 80
                      ? 'Skatteverks-klart ✅'
                      : t.score >= 50
                          ? '⚠️ ${t.flags.length} saker kvar'
                          : '❌ blockerat';
                  return Row(children: [
                    Chip(label: Text('Trygghetsmätare')),
                    const SizedBox(width: 8),
                    Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold)),
                  ]);
                },
              );
            }),
            const SizedBox(height: 16),
            Consumer(builder: (context, ref, _) {
              final next = ref.watch(nextActionProvider);
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.flash_on_outlined, color: Colors.blue),
                  title: Text(next.title),
                  subtitle: Text(next.subtitle),
                  trailing: ElevatedButton(
                    onPressed: () => Navigator.of(context).pushNamed(next.route),
                    child: Text(next.ctaLabel),
                  ),
                ),
              );
            }),
            const SizedBox(height: 16),
            Text('Tidslinje', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            SizedBox(
              height: 96,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: const [
                  _TimelineCard(title: 'Inkomst', amount: '+12 450 kr'),
                  _TimelineCard(title: 'Kostnad', amount: '-8 120 kr'),
                  _TimelineCard(title: 'Moms', amount: 'Att betala 4 330 kr'),
                ],
              ),
            ),
            ElevatedButton.icon(
              onPressed: () => Navigator.of(context).pushNamed('/capture'),
              icon: const Icon(Icons.camera_alt_outlined),
              label: const Text('Fota kvitto'),
            ),
            const SizedBox(height: 12),
            if (auth.user != null)
              Text('Välkommen, ${auth.user!['name'] ?? 'användare'}', style: const TextStyle(fontWeight: FontWeight.w600)),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Hem'),
          NavigationDestination(icon: Icon(Icons.camera_alt_outlined), label: 'Fota'),
          NavigationDestination(icon: Icon(Icons.description_outlined), label: 'Dokument'),
          NavigationDestination(icon: Icon(Icons.bar_chart_outlined), label: 'Rapporter'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Konto'),
        ],
        onDestinationSelected: (idx) {
          if (idx == 1) {
            Navigator.of(context).pushNamed('/capture');
          }
        },
        selectedIndex: 0,
      ),
    );
  }
}

class _TimelineCard extends StatelessWidget {
  const _TimelineCard({required this.title, required this.amount});
  final String title;
  final String amount;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 12),
      child: SizedBox(
        width: 220,
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
                const Spacer(),
                Text(amount),
              ],
            ),
          ),
        ),
      ),
    );
  }
}


