import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class OcrBox {
  OcrBox({required this.x, required this.y, required this.w, required this.h, required this.label});
  final double x;
  final double y;
  final double w;
  final double h;
  final String label;
}

class DocumentDetail {
  DocumentDetail({required this.id, required this.ocrText, required this.boxes, required this.imageUrl});
  final String id;
  final String ocrText;
  final List<OcrBox> boxes;
  final String imageUrl;
}

class DocumentsApi {
  DocumentsApi(this._dio);
  final Dio _dio;

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
    return DocumentDetail(
      id: meta['id'] as String,
      ocrText: (ocr['text'] ?? '') as String,
      boxes: boxes,
      imageUrl: (meta['storageUrl'] ?? '') as String,
    );
  }
}

final documentsApiProvider = Provider<DocumentsApi>((ref) => DocumentsApi(NetworkService().client));


