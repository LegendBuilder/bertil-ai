import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class TrialBalance {
  TrialBalance({required this.year, required this.accounts, required this.total});
  final int year;
  final Map<String, double> accounts;
  final double total;
}

class ReportsApi {
  ReportsApi(this._dio);
  final Dio _dio;

  Future<TrialBalance> getTrialBalance(int year) async {
    final res = await _dio.get('/trial-balance', queryParameters: {'year': year});
    final data = res.data as Map<String, dynamic>;
    return TrialBalance(
      year: data['year'] as int,
      accounts: (data['accounts'] as Map).map((k, v) => MapEntry(k.toString(), (v as num).toDouble())),
      total: (data['total'] as num).toDouble(),
    );
  }

  Uri sieExportUrl(int year) {
    final base = const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');
    return Uri.parse('$base/exports/sie?year=$year');
  }
}

final reportsApiProvider = Provider<ReportsApi>((ref) => ReportsApi(NetworkService().client));


