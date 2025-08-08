import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class TrustSummary {
  TrustSummary({required this.score, required this.flags});
  final int score;
  final List<Map<String, dynamic>> flags;
}

class VerificationSummary {
  VerificationSummary({required this.id, required this.immutableSeq, required this.date, required this.totalAmount, required this.currency});
  final int id;
  final int immutableSeq;
  final String date;
  final double totalAmount;
  final String currency;
}

class LedgerApi {
  LedgerApi(this._dio);
  final Dio _dio;

  Future<TrustSummary> getComplianceSummary(int year) async {
    final res = await _dio.get('/compliance/summary', queryParameters: {'year': year});
    final data = res.data as Map<String, dynamic>;
    return TrustSummary(score: data['score'] as int, flags: (data['flags'] as List).cast<Map<String, dynamic>>());
  }

  Future<List<VerificationSummary>> listVerifications({int? year}) async {
    final res = await _dio.get('/verifications', queryParameters: year != null ? {'year': year} : null);
    final list = (res.data as List).cast<Map<String, dynamic>>();
    return list
        .map((e) => VerificationSummary(
              id: e['id'] as int,
              immutableSeq: e['immutable_seq'] as int,
              date: e['date'] as String,
              totalAmount: (e['total_amount'] as num).toDouble(),
              currency: e['currency'] as String,
            ))
        .toList();
  }
}

final ledgerApiProvider = Provider<LedgerApi>((ref) => LedgerApi(NetworkService().client));


