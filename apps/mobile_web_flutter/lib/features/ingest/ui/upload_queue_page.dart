import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

import '../../../shared/services/queue/queue_service.dart';

class UploadQueuePage extends ConsumerWidget {
  const UploadQueuePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (kIsWeb) {
      return const Scaffold(
        body: Center(child: Text('Offline-kö är inte tillgänglig på webben')),
      );
    }
    final queue = ref.watch(queueServiceProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Uppladdningskö')),
      body: queue.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Kö kunde inte öppnas: $e')),
        data: (svc) => StreamBuilder<int>(
          stream: svc.watchPendingCount(),
          builder: (context, snap) {
            final pending = snap.data ?? 0;
            return Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Väntar: $pending'),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      ElevatedButton(
                        onPressed: () => svc.processQueue(),
                        child: const Text('Bearbeta kö'),
                      ),
                    ],
                  )
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}


