import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../provider/auth_providers.dart';

class LoginPage extends ConsumerWidget {
  const LoginPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(authControllerProvider);
    final ctrl = ref.read(authControllerProvider.notifier);
    ref.listen(authControllerProvider, (prev, next) {
      if (next.isAuthenticated) {
        context.go('/');
      }
    });
    return Scaffold(
      appBar: AppBar(title: const Text('BankID inloggning')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Logga in med BankID för att komma igång.'),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: state.isLoading ? null : () => ctrl.startBankId(),
              icon: const Icon(Icons.login),
              label: const Text('Starta BankID'),
            ),
            const SizedBox(height: 16),
            if (state.message != null) Text(state.message!),
            const Spacer(),
            if (state.isLoading) const LinearProgressIndicator(),
          ],
        ),
      ),
    );
  }
}


