import 'dart:typed_data';

import 'package:bertil_mobile_web_flutter/features/ingest/data/ingest_api.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

class _MockAdapter extends HttpClientAdapter {
  @override
  void close({bool force = false}) {}

  @override
  Future<HttpClientResponse> fetch(RequestOptions options, Stream<List<int>>? requestStream, Future<void>? cancelFuture) async {
    final resp = ResponseBody.fromString('{"documentId":"abc","storagePath":"/worm/ab/cd","duplicate":true}', 200, headers: {
      Headers.contentTypeHeader: ['application/json']
    });
    return resp;
  }
}

void main() {
  test('uploadDocument returns ids', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://localhost'))..httpClientAdapter = _MockAdapter();
    final api = IngestApi(dio);
    final resp = await api.uploadDocument(bytes: Uint8List.fromList([1, 2, 3]), filename: 'a.jpg', meta: {'org_id': 1});
    expect(resp.documentId, 'abc');
    expect(resp.storagePath.isNotEmpty, true);
  });
}


