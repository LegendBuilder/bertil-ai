import 'dart:typed_data';

import 'package:bertil_mobile_web_flutter/features/ingest/data/ingest_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class _MockAdapter extends HttpClientAdapter {
  int _count = 0;
  @override
  void close({bool force = false}) {}

  @override
  Future<HttpClientResponse> fetch(RequestOptions options, Stream<List<int>>? requestStream, Future<void>? cancelFuture) async {
    _count += 1;
    if (_count == 1 && options.path.endsWith('/documents')) {
      final resp = ResponseBody.fromString('{"documentId":"abc","storagePath":"/worm/ab/cd","duplicate":false}', 200, headers: {
        Headers.contentTypeHeader: ['application/json']
      });
      return resp;
    }
    if (_count == 2 && options.path.endsWith('/documents/abc/process-ocr')) {
      final resp = ResponseBody.fromString('{"status":"processed","documentId":"abc","fields":[{"key":"date","value":"2025-01-15","confidence":0.9},{"key":"total","value":"123.45","confidence":0.95}]}', 200, headers: {
        Headers.contentTypeHeader: ['application/json']
      });
      return resp;
    }
    if (_count == 3 && options.path.endsWith('/ai/auto-post')) {
      final resp = ResponseBody.fromString('{"id":1,"immutable_seq":1}', 200, headers: {
        Headers.contentTypeHeader: ['application/json']
      });
      return resp;
    }
    return ResponseBody.fromString('{}', 200);
  }
}

void main() {
  test('uploadDocument + processOcr + autoPost works', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://localhost'))..httpClientAdapter = _MockAdapter();
    final api = IngestApi(dio);
    final resp = await api.uploadDocument(bytes: Uint8List.fromList([1, 2, 3]), filename: 'a.jpg', meta: {'org_id': 1});
    expect(resp.documentId, 'abc');
    final ocr = await api.processOcr(resp.documentId);
    expect(ocr['status'], 'processed');
    final auto = await api.autoPostFromExtracted(documentId: 'abc', total: 123.45, dateIso: '2025-01-15');
    expect((auto['immutable_seq'] ?? 1) >= 1, true);
  });
}


