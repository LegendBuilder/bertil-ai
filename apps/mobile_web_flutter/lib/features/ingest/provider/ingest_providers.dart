import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/ingest_api.dart';
import '../../../shared/utils/crypto.dart';
import '../../documents/provider/document_list_providers.dart';
import '../../documents/domain/document.dart';
import '../../../shared/services/queue/queue_service.dart';

class UploadState {
  const UploadState({this.isUploading = false, this.message, this.lastDocumentId, this.isDuplicate = false});
  final bool isUploading;
  final String? message;
  final String? lastDocumentId;
  final bool isDuplicate;

  UploadState copyWith({bool? isUploading, String? message, String? lastDocumentId, bool? isDuplicate}) => UploadState(
        isUploading: isUploading ?? this.isUploading,
        message: message ?? this.message,
        lastDocumentId: lastDocumentId ?? this.lastDocumentId,
        isDuplicate: isDuplicate ?? this.isDuplicate,
      );
}

class UploadController extends StateNotifier<UploadState> {
  UploadController(this._api, this._recentDocs, this._queueServiceFuture) : super(const UploadState());
  final IngestApi _api;
  final RecentDocumentsController _recentDocs;
  final Future<QueueService> _queueServiceFuture;

  Future<void> uploadBytes(Uint8List bytes, String filename, {required Map<String, dynamic> meta}) async {
    state = state.copyWith(isUploading: true, message: 'Laddar upp…');
    final start = DateTime.now();
    final checksum = sha256Hex(bytes);
    final withHash = Map<String, dynamic>.from(meta)..['hash_sha256'] = checksum;
    // Try immediate upload; on failure enqueue
    try {
      final resp = await _api.uploadDocument(bytes: bytes, filename: filename, meta: withHash);
      final worm = resp.storagePath.isNotEmpty ? ' (WORM-lagrad)' : '';
      // If not duplicate, run OCR then auto-post
      if (!resp.duplicate) {
        final ocr = await _api.processOcr(resp.documentId);
        // derive fields
        final fields = (ocr['fields'] as List?)?.cast<Map<String, dynamic>>() ?? const [];
        String? dateIso;
        String? vendor;
        double? total;
        for (final f in fields) {
          final k = (f['key'] as String).toLowerCase();
          final v = f['value'] as String;
          if (k == 'date') dateIso = v;
          if (k == 'vendor') vendor = v;
          if (k == 'total') total = double.tryParse(v.replaceAll(',', '.'));
        }
        if (total != null && dateIso != null) {
          await _api.autoPostFromExtracted(documentId: resp.documentId, total: total, dateIso: dateIso!, vendor: vendor);
        }
      }
      final elapsed = DateTime.now().difference(start).inMilliseconds / 1000.0;
      final msg = resp.duplicate
          ? 'Dubblett upptäckt – vi har redan detta kvitto$worm'
          : 'Uppladdat → Läser → Bokfört ✅$worm (${elapsed.toStringAsFixed(1)} s)';
      state = state.copyWith(isUploading: false, lastDocumentId: resp.documentId, isDuplicate: resp.duplicate, message: msg);
      if (!resp.duplicate) {
        _recentDocs.add(DocumentSummary(id: resp.documentId, uploadedAt: DateTime.now()));
      }
    } catch (e) {
      final q = await _queueServiceFuture;
      await q.enqueueUpload(filename: filename, bytes: bytes, meta: withHash);
      state = state.copyWith(isUploading: false, message: 'Offline – lagt i kö. Vi försöker igen automatiskt.');
    }
  }
}

final uploadControllerProvider = StateNotifierProvider<UploadController, UploadState>((ref) {
  final api = ref.watch(ingestApiProvider);
  final recent = ref.watch(recentDocumentsProvider.notifier);
  final queue = ref.watch(queueServiceProvider.future);
  return UploadController(api, recent, queue);
});


