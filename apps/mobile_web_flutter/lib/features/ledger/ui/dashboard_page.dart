import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../features/auth/provider/auth_providers.dart';
import '../provider/ledger_providers.dart';
import '../../inbox/provider/inbox_providers.dart';
import 'package:flutter/services.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final pendingCount = ref.watch(pendingTasksCountProvider).maybeWhen(orElse: () => 0, data: (n) => n);
    return Scaffold(
      appBar: AppBar(title: const Text('Hem')),
      body: Shortcuts(
        shortcuts: <LogicalKeySet, Intent>{
          LogicalKeySet(LogicalKeyboardKey.keyG): const ActivateIntent(),
        },
        child: Actions(
          actions: <Type, Action<Intent>>{
            ActivateIntent: CallbackAction<ActivateIntent>(onInvoke: (intent) {
              final keys = RawKeyboard.instance.keysPressed;
              if (keys.contains(LogicalKeyboardKey.keyG)) {
                if (context.mounted) context.go('/inbox');
              }
              return null;
            }),
          },
          child: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (pendingCount > 0)
              Card(
                color: Colors.blue.shade50,
                child: ListTile(
                  leading: const Icon(Icons.inbox_outlined, color: Colors.blue),
                  title: Text('Granska ($pendingCount)', style: const TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: const Text('Autopilot har förslag som väntar på din bekräftelse'),
                  trailing: ElevatedButton(
                    onPressed: () => context.go('/inbox'),
                    child: const Text('Öppna Inbox (G)'),
                  ),
                ),
              ),
            const SizedBox(height: 8),
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
                  final dismissed = ref.watch(dismissedFlagsProvider);
                  final topFlags = t.flags.where((f) => !dismissed.contains(f['rule_code'] as String)).take(3).toList();
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        const Chip(label: Text('Trygghetsmätare')),
                        const SizedBox(width: 8),
                        Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold)),
                      ]),
                      const SizedBox(height: 8),
                      if (topFlags.isNotEmpty)
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            for (final f in topFlags)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 6),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Chip(
                                      backgroundColor: (f['severity'] == 'error')
                                          ? Colors.red.shade100
                                          : (f['severity'] == 'warning')
                                              ? Colors.orange.shade100
                                              : Colors.green.shade100,
                                      label: Text(f['message'] as String),
                                    ),
                                    const SizedBox(width: 8),
                                    if ((f['rule_code'] as String).startsWith('R-011'))
                                      OutlinedButton(
                                        onPressed: () {
                                          // Optimistic dismissal and undo for demo
                                          final code = f['rule_code'] as String;
                                          ref.read(dismissedFlagsProvider.notifier).state = {...dismissed, code};
                                          ScaffoldMessenger.of(context).showSnackBar(
                                            SnackBar(
                                              content: const Text('Datum korrigerat (demo)'),
                                              action: SnackBarAction(
                                                label: 'Ångra',
                                                onPressed: () => ref.read(dismissedFlagsProvider.notifier).state = {...dismissed}..remove(code),
                                              ),
                                            ),
                                          );
                                        },
                                        child: const Text('Korrigera datum'),
                                      )
                                    else if ((f['rule_code'] as String).startsWith('R-001'))
                                      OutlinedButton(
                                        onPressed: () {
                                          context.go('/documents');
                                        },
                                        child: const Text('Koppla underlag'),
                                      )
                                    else
                                      const SizedBox.shrink(),
                                  ],
                                ),
                              ),
                          ],
                        ),
                    ],
                  );
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
                    onPressed: () => context.go(next.route),
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
            Wrap(spacing: 8, runSpacing: 8, children: [
              ElevatedButton.icon(
                onPressed: () => context.go('/capture'),
                icon: const Icon(Icons.camera_alt_outlined),
                label: const Text('Fota kvitto'),
              ),
              OutlinedButton.icon(
                onPressed: () => context.go('/documents'),
                icon: const Icon(Icons.upload_file),
                label: const Text('Ladda upp'),
              ),
            ]),
            const SizedBox(height: 12),
            if (auth.user != null)
              Text('Välkommen, ${auth.user!['name'] ?? 'användare'}', style: const TextStyle(fontWeight: FontWeight.w600)),
          ],
          ),
        ),
          ),
        ),
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


