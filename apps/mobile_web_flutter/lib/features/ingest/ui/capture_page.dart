import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:file_picker/file_picker.dart';
import 'package:image_picker/image_picker.dart';
import '../../ingest/data/ingest_api.dart';
import '../../documents/provider/document_list_providers.dart';
import '../../documents/domain/document.dart';
import '../../../shared/providers/success_banner_provider.dart';
import '../../../shared/services/analytics.dart';
import '../../../shared/services/queue/queue_service.dart';

class CapturePage extends ConsumerStatefulWidget {
  const CapturePage({super.key});
  @override
  ConsumerState<CapturePage> createState() => _CapturePageState();
}

class _CapturePageState extends ConsumerState<CapturePage> {
  bool _busy = false;
  String? _message;

  Future<void> _pickAndUpload() async {
    setState(() {
      _busy = true;
      _message = 'Väljer fil…';
    });
    Uint8List? pickedBytes;
    String filename = 'image.jpg';
    if (kIsWeb) {
      final result = await FilePicker.platform.pickFiles(type: FileType.image, allowMultiple: false, withData: true);
      if (result == null || result.files.isEmpty) {
        setState(() {
          _busy = false;
          _message = 'Ingen fil vald';
        });
        return;
      }
      final file = result.files.first;
      pickedBytes = Uint8List.fromList(file.bytes!);
      filename = file.name;
    } else {
      final xfile = await ImagePicker().pickImage(source: ImageSource.camera, imageQuality: 85);
      if (xfile == null) {
        setState(() {
          _busy = false;
          _message = 'Ingen bild tagen';
        });
        return;
      }
      pickedBytes = await xfile.readAsBytes();
      filename = xfile.name;
    }
    final api = ref.read(ingestApiProvider);
    try {
      setState(() => _message = 'Laddar upp…');
      final uploaded = await api.uploadDocument(bytes: pickedBytes!, filename: filename, meta: {'source': kIsWeb ? 'web_upload' : 'camera'});
      AnalyticsService.logEvent('capture_upload_success');
      setState(() => _message = 'Bearbetar OCR…');
      final ocr = await api.processOcr(uploaded.documentId);
      AnalyticsService.logEvent('ocr_extraction_success');
      setState(() => _message = 'Skapar verifikation…');
      final fields = (ocr['fields'] as List).cast<Map<String, dynamic>>();
      double total = 0.0;
      String dateIso = DateTime.now().toIso8601String().substring(0, 10);
      String? vendor;
      for (final f in fields) {
        final key = (f['key'] as String).toLowerCase();
        final val = (f['value'] ?? '').toString();
        if (key.contains('total') || key.contains('belopp')) {
          final parsed = double.tryParse(val.replaceAll(',', '.').replaceAll(RegExp(r'[^0-9\.]'), ''));
          if (parsed != null) total = parsed;
        } else if (key.contains('date') || key.contains('datum')) {
          dateIso = DateTime.tryParse(val)?.toIso8601String().substring(0, 10) ?? dateIso;
        } else if (key.contains('vendor') || key.contains('motpart') || key.contains('leverantör')) {
          vendor = val;
        }
      }
      await api.autoPostFromExtracted(documentId: uploaded.documentId, total: total, dateIso: dateIso, vendor: vendor);
      AnalyticsService.logEvent('autopost_success');
      // Insert to recent documents for immediate visibility
      ref.read(recentDocumentsProvider.notifier).add(
            DocumentSummary(id: uploaded.documentId, uploadedAt: DateTime.now(), status: DocumentStatus.newDoc),
          );
      ref.read(successBannerProvider.notifier).show('Bokfört ✅');
      if (mounted) {
        setState(() {
          _busy = false;
          _message = 'Bokfört ✅';
        });
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Klart! Vi har bokfört detta.')));
      }
    } catch (e) {
      // Offline fallback: queue job
      try {
        final svc = await QueueService.create();
        await svc.enqueueUpload(filename: filename, bytes: pickedBytes!, meta: {'source': kIsWeb ? 'web_upload' : 'camera'});
        AnalyticsService.logEvent('enqueue_offline');
        if (mounted) {
          setState(() {
            _busy = false;
            _message = 'Offline: tillagd i uppladdningskön';
          });
        }
      } catch (_) {
        setState(() {
          _busy = false;
          _message = 'Misslyckades: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Fota / Ladda upp')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Ladda upp ett kvitto (webb) – kameraflöde kommer i mobil.'),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _busy ? null : _pickAndUpload,
              icon: const Icon(Icons.upload_file),
              label: const Text('Välj bild'),
            ),
            const SizedBox(height: 12),
            if (_busy) const LinearProgressIndicator(),
            if (_message != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(_message!)),
            const SizedBox(height: 24),
            Expanded(
              child: CustomPaint(
                painter: _OverlayGuidesPainter(),
                child: const Center(child: Text('Placera kvittot tydligt i bild – undvik blänk.')),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OverlayGuidesPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {}
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
