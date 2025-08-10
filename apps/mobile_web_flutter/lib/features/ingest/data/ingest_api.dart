import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class UploadResponse {
  UploadResponse({required this.documentId, required this.storagePath, required this.duplicate});
  final String documentId;
  final String storagePath;
  final bool duplicate;
}

class IngestApi {
  IngestApi(this._dio);
  final Dio _dio;

  Future<UploadResponse> uploadDocument({required Uint8List bytes, required String filename, required Map<String, dynamic> meta}) async {
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: filename),
      'meta_json': jsonEncode(meta),
    });
    final res = await _dio.post('/documents', data: form);
    final data = res.data as Map<String, dynamic>;
    return UploadResponse(
      documentId: data['documentId'] as String,
      storagePath: (data['storagePath'] ?? '') as String,
      duplicate: (data['duplicate'] ?? false) as bool,
    );
  }

  Future<Map<String, dynamic>> processOcr(String documentId) async {
    final res = await _dio.post('/documents/$documentId/process-ocr');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> autoPostFromExtracted({
    required String documentId,
    required double total,
    required String dateIso,
    String? vendor,
    String? vatCode,
  }) async {
    final res = await _dio.post('/ai/auto-post', data: {
      'org_id': 1,
      'document_id': documentId,
      'total': total,
      'date': dateIso,
      if (vendor != null) 'vendor': vendor,
      if (vatCode != null) 'vat_code': vatCode,
    });
    return res.data as Map<String, dynamic>;
  }

  Uri vatSkvFileUrl({required int year, required int month}) {
    final base = const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');
    final period = '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}';
    return Uri.parse('$base/reports/vat/declaration/file?period=$period');
  }
}

final ingestApiProvider = Provider<IngestApi>((ref) => IngestApi(NetworkService().client));


