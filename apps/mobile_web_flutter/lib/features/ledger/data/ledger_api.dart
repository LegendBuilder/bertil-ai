import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class TrustSummary {
  TrustSummary({required this.score, required this.flags});
  final int score;
  final List<Map<String, dynamic>> flags;
}

class LedgerApi {
  LedgerApi(this._dio);
  final Dio _dio;

  Future<TrustSummary> getComplianceSummary(int year) async {
    final res = await _dio.get('/compliance/summary', queryParameters: {'year': year});
    final data = res.data as Map<String, dynamic>;
    return TrustSummary(score: data['score'] as int, flags: (data['flags'] as List).cast<Map<String, dynamic>>());
  }
}

final ledgerApiProvider = Provider<LedgerApi>((ref) => LedgerApi(NetworkService().client));


