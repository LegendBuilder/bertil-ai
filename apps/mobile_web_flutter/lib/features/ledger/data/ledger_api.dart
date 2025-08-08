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

class VerificationDetail {
  VerificationDetail({required this.id, required this.immutableSeq, required this.date, required this.totalAmount, required this.currency, required this.entries, required this.auditHash, this.explainability, this.documentLink});
  final int id;
  final int immutableSeq;
  final String date;
  final double totalAmount;
  final String currency;
  final List<Map<String, dynamic>> entries;
  final String auditHash;
  final String? explainability;
  final String? documentLink;
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

  Future<VerificationDetail> getVerification(int id) async {
    final res = await _dio.get('/verifications/$id');
    final data = res.data as Map<String, dynamic>;
    return VerificationDetail(
      id: data['id'] as int,
      immutableSeq: data['immutable_seq'] as int,
      date: data['date'] as String,
      totalAmount: (data['total_amount'] as num).toDouble(),
      currency: data['currency'] as String,
      entries: (data['entries'] as List).cast<Map<String, dynamic>>(),
      auditHash: (data['audit_hash'] ?? '') as String,
      explainability: (data['explainability'] as String?),
      documentLink: (data['document_link'] as String?),
    );
  }

  Future<int> createVerification({
    required int orgId,
    required String dateIso,
    required double totalAmount,
    String currency = 'SEK',
    double? vatAmount,
    String? counterparty,
    String? documentLink,
    required List<Map<String, dynamic>> entries,
  }) async {
    final body = {
      'org_id': orgId,
      'date': dateIso,
      'total_amount': totalAmount,
      'currency': currency,
      if (vatAmount != null) 'vat_amount': vatAmount,
      if (counterparty != null) 'counterparty': counterparty,
      if (documentLink != null) 'document_link': documentLink,
      'entries': entries,
    };
    final res = await _dio.post('/verifications', data: body);
    final data = res.data as Map<String, dynamic>;
    return data['id'] as int;
  }
}

final ledgerApiProvider = Provider<LedgerApi>((ref) => LedgerApi(NetworkService().client));


