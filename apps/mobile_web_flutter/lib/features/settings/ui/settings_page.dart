import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/provider/auth_providers.dart';
import '../../../shared/providers/feature_flags_provider.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final user = auth.user;
    return Scaffold(
      appBar: AppBar(title: const Text('Konto')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (user != null) ...[
              Text('Namn: ${user['name'] ?? '-'}'),
              Text('BankID-subject: ${user['subject'] ?? '-'}'),
            ] else ...[
              const Text('Ej inloggad'),
            ],
            const SizedBox(height: 16),
            Consumer(builder: (context, ref, _) {
              final enabled = ref.watch(enhancedAutomationProvider);
              return SwitchListTile(
                title: const Text('Förstärkt automation'),
                subtitle: const Text('Använd förbättrade AI-förklaringar och insikter'),
                value: enabled,
                onChanged: (v) => ref.read(enhancedAutomationProvider.notifier).state = v,
              );
            }),
          ],
        ),
      ),
    );
  }
}


