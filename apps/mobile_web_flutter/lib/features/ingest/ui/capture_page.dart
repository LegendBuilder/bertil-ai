import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../provider/ingest_providers.dart';
import '../../../shared/services/queue/queue_service.dart';

class CapturePage extends ConsumerWidget {
  const CapturePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final upload = ref.watch(uploadControllerProvider);
    final ctrl = ref.read(uploadControllerProvider.notifier);
    Future<void> pickAndUpload(ImageSource source) async {
      final picker = ImagePicker();
      final picked = await picker.pickImage(source: source, imageQuality: 85);
      if (picked == null) return;
      final bytes = await picked.readAsBytes();
      await ctrl.uploadBytes(bytes as Uint8List, picked.name, meta: {
        'org_id': 1,
        'type': 'receipt',
        'captured_at': DateTime.now().toIso8601String(),
      });
      final state = ref.read(uploadControllerProvider);
      if (state.message != null) {
        // ignore: use_build_context_synchronously
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(state.message!),
          behavior: SnackBarBehavior.floating,
          backgroundColor: state.isDuplicate ? Colors.orange : null,
        ));
        if (!state.isDuplicate && state.lastDocumentId != null) {
          // ignore: use_build_context_synchronously
          Navigator.of(context).pushNamed('/documents/${state.lastDocumentId}');
        }
      }
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Fota', semanticsLabel: 'Fota kvitto')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Consumer(builder: (context, ref, _) {
              final queueFuture = ref.watch(queueServiceProvider);
              return queueFuture.when(
                loading: () => const SizedBox.shrink(),
                error: (_, __) => const SizedBox.shrink(),
                data: (q) => StreamBuilder<int>(
                  stream: q.watchPendingCount(),
                  builder: (context, snap) {
                    final pending = snap.data ?? 0;
                    if (pending <= 0) return const SizedBox.shrink();
                    return ListTile(
                      leading: const Icon(Icons.sync_outlined),
                      title: Text('Kö: $pending väntar'),
                      trailing: OutlinedButton(
                        onPressed: () => q.processQueue(),
                        child: const Text('Försök igen'),
                      ),
                    );
                  },
                ),
              );
            }),
            ElevatedButton.icon(
              onPressed: upload.isUploading ? null : () => pickAndUpload(ImageSource.camera),
              icon: const Icon(Icons.camera_alt_outlined),
              label: const Text('Fota kvitto', semanticsLabel: 'Öppna kamera'),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: upload.isUploading ? null : () => pickAndUpload(ImageSource.gallery),
              icon: const Icon(Icons.upload_file),
              label: const Text('Välj bild från galleri', semanticsLabel: 'Välj bild'),
            ),
            const SizedBox(height: 24),
            if (upload.isUploading) const LinearProgressIndicator(),
            if (upload.lastDocumentId != null) Text('Dokument-ID: ${upload.lastDocumentId}'),
          ],
        ),
      ),
    );
  }
}


