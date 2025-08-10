import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';
import '../domain/document.dart';

class OcrBox {
  OcrBox({required this.x, required this.y, required this.w, required this.h, required this.label});
  final double x;
  final double y;
  final double w;
  final double h;
  final String label;
}

class ExtractedFieldData {
  ExtractedFieldData({required this.key, required this.value, required this.confidence});
  final String key;
  final String value;
  final double confidence;
}

class DocumentDetail {
  DocumentDetail({
    required this.id,
    required this.ocrText,
    required this.boxes,
    required this.imageUrl,
    required this.extractedFields,
  });
  final String id;
  final String ocrText;
  final List<OcrBox> boxes;
  final String imageUrl;
  final List<ExtractedFieldData> extractedFields;
}

class DocumentsApi {
  DocumentsApi(this._dio);
  final Dio _dio;

  Future<List<DocumentSummary>> listDocuments({int limit = 20, int offset = 0}) async {
    final res = await _dio.get('/documents', queryParameters: {'limit': limit, 'offset': offset});
    final items = (res.data['items'] as List).cast<Map<String, dynamic>>();
    return items
        .map((m) => DocumentSummary(
              id: m['id'] as String,
              uploadedAt: DateTime.tryParse((m['created_at'] ?? '') as String) ?? DateTime.now(),
              status: DocumentStatus.newDoc,
            ))
        .toList();
  }

  Future<DocumentDetail> getDocument(String id) async {
    final res = await _dio.get('/documents/$id');
    final data = res.data as Map<String, dynamic>;
    final meta = data['meta'] as Map<String, dynamic>;
    final ocr = data['ocr'] as Map<String, dynamic>;
    final boxesRaw = (ocr['boxes'] as List? ?? []).cast<Map<String, dynamic>>();
    final boxes = boxesRaw
        .map((b) => OcrBox(
              x: (b['x'] as num).toDouble(),
              y: (b['y'] as num).toDouble(),
              w: (b['w'] as num).toDouble(),
              h: (b['h'] as num).toDouble(),
              label: b['label'] as String,
            ))
        .toList();
    final extracted = ((data['extracted_fields'] as List?) ?? [])
        .cast<Map<String, dynamic>>()
        .map((e) => ExtractedFieldData(
              key: e['key'] as String,
              value: e['value'] as String,
              confidence: (e['confidence'] as num).toDouble(),
            ))
        .toList();
    return DocumentDetail(
      id: meta['id'] as String,
      ocrText: (ocr['text'] ?? '') as String,
      boxes: boxes,
      imageUrl: _resolveAbsoluteUrl((meta['storageUrl'] ?? '') as String),
      extractedFields: extracted,
    );
  }

  String _resolveAbsoluteUrl(String storageUrl) {
    if (storageUrl.startsWith('http')) return storageUrl;
    final base = _dio.options.baseUrl.replaceAll(RegExp(r'/+$'), '');
    if (storageUrl.startsWith('/')) {
      return '$base$storageUrl';
    }
    return '$base/$storageUrl';
  }
}

final documentsApiProvider = Provider<DocumentsApi>((ref) => DocumentsApi(NetworkService().client));


