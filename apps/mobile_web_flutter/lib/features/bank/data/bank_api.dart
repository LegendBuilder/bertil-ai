import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class BankTxItem {
  BankTxItem({required this.id, required this.date, required this.amount, required this.currency, required this.description, this.counterparty, this.matchedVerificationId});
  final int id;
  final String date;
  final double amount;
  final String currency;
  final String description;
  final String? counterparty;
  final int? matchedVerificationId;
}

class SuggestionItem {
  SuggestionItem({required this.verificationId, required this.immutableSeq, required this.date, required this.total, this.counterparty, required this.score});
  final int verificationId;
  final int immutableSeq;
  final String date;
  final double total;
  final String? counterparty;
  final double score;
}

class BankApi {
  BankApi(this._dio);
  final Dio _dio;

  Future<List<BankTxItem>> listUnmatched({int limit = 50, int offset = 0, String? dateFrom, String? dateTo, double? amountMin, double? amountMax, String? q}) async {
    final qp = {
      'unmatched': 1,
      'limit': limit,
      'offset': offset,
      if (dateFrom != null && dateFrom.isNotEmpty) 'date_from': dateFrom,
      if (dateTo != null && dateTo.isNotEmpty) 'date_to': dateTo,
      if (amountMin != null) 'amount_min': amountMin,
      if (amountMax != null) 'amount_max': amountMax,
      if (q != null && q.isNotEmpty) 'q': q,
    };
    final res = await _dio.get('/bank/transactions', queryParameters: qp);
    final items = (res.data['items'] as List).cast<Map<String, dynamic>>();
    return items
        .map((m) => BankTxItem(
              id: m['id'] as int,
              date: m['date'] as String,
              amount: (m['amount'] as num).toDouble(),
              currency: m['currency'] as String,
              description: m['description'] as String,
              counterparty: m['counterparty'] as String?,
              matchedVerificationId: m['matched_verification_id'] as int?,
            ))
        .toList();
  }

  Future<List<SuggestionItem>> suggestFor(int txId) async {
    final res = await _dio.get('/bank/transactions/$txId/suggest');
    final items = (res.data['items'] as List).cast<Map<String, dynamic>>();
    return items
        .map((m) => SuggestionItem(
              verificationId: m['verification_id'] as int,
              immutableSeq: m['immutable_seq'] as int,
              date: m['date'] as String,
              total: (m['total'] as num).toDouble(),
              counterparty: m['counterparty'] as String?,
              score: (m['score'] as num).toDouble(),
            ))
        .toList();
  }

  Future<void> accept(int txId, int verificationId) async {
    await _dio.post('/bank/transactions/$txId/accept', data: {'verification_id': verificationId});
  }

  Future<void> bulkAccept(List<Map<String, int>> items) async {
    await _dio.post('/bank/transactions/bulk-accept', data: {'items': items});
  }

  Future<void> settle(int txId, int verificationId) async {
    await _dio.post('/bank/transactions/$txId/settle', data: {'verification_id': verificationId});
  }
}

final bankApiProvider = Provider<BankApi>((ref) => BankApi(NetworkService().client));



