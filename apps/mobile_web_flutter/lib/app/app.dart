import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'router.dart';
import 'theme.dart';
import '../shared/services/network.dart';

class BertilApp extends ConsumerWidget {
  const BertilApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'Bertil',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      routerConfig: router,
      builder: (context, child) {
        return Stack(
          children: [
            Semantics(
              label: 'Bertil huvudapp',
              explicitChildNodes: true,
              child: child ?? const SizedBox.shrink(),
            ),
            // Global network issue surface
            Positioned(
              left: 16,
              right: 16,
              bottom: 16,
              child: Consumer(builder: (context, ref, _) {
                // Create a stream listener to errors
                return StreamBuilder<NetworkIssue?>(
                  stream: NetworkService().errors,
                  builder: (context, snap) {
                    final issue = snap.data;
                    if (issue == null) return const SizedBox.shrink();
                    return Material(
                      elevation: 6,
                      borderRadius: BorderRadius.circular(12),
                      color: Colors.red.shade700,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        child: Row(
                          children: [
                            const Icon(Icons.wifi_off, color: Colors.white),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(issue.message, style: const TextStyle(color: Colors.white)),
                            ),
                            TextButton(
                              onPressed: () => NetworkService().clearError(),
                              child: const Text('Stäng', style: TextStyle(color: Colors.white)),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                );
              }),
            ),
          ],
        );
      },
    );
  }
}


