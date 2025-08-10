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

  Future<Map<String, dynamic>> getVatReport({required int year, required int month}) async {
    final period = '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}';
    final res = await _dio.get('/reports/vat', queryParameters: {'period': period, 'format': 'json'});
    return (res.data as Map<String, dynamic>);
  }

  Future<Map<String, num>> getVatDeclaration({required int year, required int month}) async {
    final period = '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}';
    final res = await _dio.get('/reports/vat/declaration', queryParameters: {'period': period});
    final data = res.data as Map<String, dynamic>;
    final boxes = (data['boxes'] as Map).map((k, v) => MapEntry(k.toString(), (v as num)));
    return boxes;
  }

$'), '').replaceAll(RegExp(r'/+$'), '');
  Uri sieExportUrl(int year) {
    final base = _dio.options.baseUrl.replaceAll(RegExp(r'/+$'), '');
    return Uri.parse('$base/exports/sie?year=$year');
  }

  Uri verificationsPdfUrl(int year) {
    final base = _dio.options.baseUrl.replaceAll(RegExp(r'/+$'), '');
    return Uri.parse('$base/exports/verifications.pdf?year=$year');
  }

  Uri vatReportPdfUrl({required int year, required int month}) {
    final base = _dio.options.baseUrl.replaceAll(RegExp(r'/+$'), '');
    final period = '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}';
    return Uri.parse('$base/reports/vat?period=$period&format=pdf');
  }

  Uri vatSkvFileUrl({required int year, required int month}) {
    final base = _dio.options.baseUrl.replaceAll(RegExp(r'/+$'), '');
    final period = '${year.toString().padLeft(4, '0')}-${month.toString().padLeft(2, '0')}';
    return Uri.parse('$base/reports/vat/declaration/file?period=$period');
  }

  Future<void> importSie({required List<int> bytes, required String filename}) async {
    // Rely on filename extension; contentType optional
    final form = FormData.fromMap({'file': MultipartFile.fromBytes(bytes, filename: filename)});
    await _dio.post('/imports/sie', data: form);
  }
}

final reportsApiProvider = Provider<ReportsApi>((ref) => ReportsApi(NetworkService().client));


