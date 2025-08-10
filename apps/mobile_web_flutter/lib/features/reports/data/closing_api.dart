import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class ClosingApi {
  ClosingApi(this._dio);
  final Dio _dio;

  Future<List<Map<String, String>>> getStatus({int orgId = 1}) async {
    final res = await _dio.get('/period/status', queryParameters: {'org_id': orgId});
    final items = (res.data['locked'] as List).cast<Map<String, dynamic>>();
    return items
        .map((m) => {
              'start_date': m['start_date'] as String,
              'end_date': m['end_date'] as String,
            })
        .toList();
  }

  Future<void> closePeriod({required String startDate, required String endDate, int orgId = 1}) async {
    await _dio.post('/period/close', data: {'org_id': orgId, 'start_date': startDate, 'end_date': endDate});
  }
}

final closingApiProvider = Provider<ClosingApi>((ref) => ClosingApi(NetworkService().client));





