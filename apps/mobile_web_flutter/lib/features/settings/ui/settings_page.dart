import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/provider/auth_providers.dart';

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
          ],
        ),
      ),
    );
  }
}


