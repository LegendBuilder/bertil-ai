import 'dart:typed_data';
// ignore: unused_import
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:image/image.dart' as img;

import '../provider/ingest_providers.dart';
import '../../../shared/services/queue/queue_service.dart';

class CapturePage extends ConsumerWidget {
  const CapturePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final upload = ref.watch(uploadControllerProvider);
    final ctrl = ref.read(uploadControllerProvider.notifier);

    Future<void> _processAndUpload(Uint8List bytes, String filename) async {
      var processed = bytes;
      try {
        final decoded = img.decodeImage(processed);
        if (decoded != null && decoded.width > 0 && decoded.height > 0) {
          final w = decoded.width;
          final h = decoded.height;
          final meanLuma = _estimateLuma(decoded);
          if (meanLuma > 230) {
            // ignore: use_build_context_synchronously
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Blänk upptäckt – vinkla kvittot och försök igen')));
          }
          final targetRatio = 4 / 5;
          final currentRatio = w / h;
          if ((currentRatio - targetRatio).abs() > 0.05) {
            int newW = w;
            int newH = (w / targetRatio).round();
            if (newH > h) {
              newH = h;
              newW = (h * targetRatio).round();
            }
            final x = (w - newW) ~/ 2;
            final y = (h - newH) ~/ 2;
            final cropped = img.copyCrop(decoded, x: x, y: y, width: newW, height: newH);
            processed = Uint8List.fromList(img.encodeJpg(cropped, quality: 90));
          }
        }
      } catch (_) {}

      await ctrl.uploadBytes(processed, filename, meta: {
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

    Future<void> pickAndUpload(ImageSource source) async {
      final picker = ImagePicker();
      final picked = await picker.pickImage(source: source, imageQuality: 85);
      if (picked == null) return;
      final bytes = await picked.readAsBytes();
      await _processAndUpload(bytes as Uint8List, picked.name);
    }

    Future<void> pickBatch() async {
      final picker = ImagePicker();
      final picked = await picker.pickMultiImage(imageQuality: 85);
      if (picked.isEmpty) return;
      for (final p in picked) {
        final bytes = await p.readAsBytes();
        await _processAndUpload(bytes as Uint8List, p.name);
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
            // Live overlay guides (static preview area)
            Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  height: 220,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.black12,
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                CustomPaint(
                  size: const Size(double.infinity, 200),
                  painter: _OverlayGuidesPainter(),
                ),
                const Positioned(
                  bottom: 8,
                  child: Text('Lägg kvittot inom ramen'),
                ),
              ],
            ),
            const SizedBox(height: 12),
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
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: upload.isUploading ? null : pickBatch,
              icon: const Icon(Icons.collections_outlined),
              label: const Text('Batch: välj flera'),
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

double _estimateLuma(img.Image im) {
  // sample a grid of pixels
  final stepX = (im.width / 20).clamp(1, im.width).toInt();
  final stepY = (im.height / 20).clamp(1, im.height).toInt();
  int samples = 0;
  double sum = 0;
  for (int y = 0; y < im.height; y += stepY) {
    for (int x = 0; x < im.width; x += stepX) {
      final c = im.getPixel(x, y);
      final r = img.getRed(c);
      final g = img.getGreen(c);
      final b = img.getBlue(c);
      // Rec. 601 luma
      final luma = 0.299 * r + 0.587 * g + 0.114 * b;
      sum += luma;
      samples++;
    }
  }
  return samples == 0 ? 0 : (sum / samples);
}


