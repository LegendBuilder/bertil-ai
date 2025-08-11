import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class VatCodeItem {
  VatCodeItem({required this.code, required this.description, required this.rate, required this.reverseCharge});
  final String code;
  final String description;
  final double rate;
  final bool reverseCharge;
}

class VatApi {
  VatApi(this._dio);
  final Dio _dio;

  Future<List<VatCodeItem>> listCodes() async {
    final res = await _dio.get('/vat/codes');
    final items = (res.data['items'] as List).cast<Map<String, dynamic>>();
    return items
        .map((m) => VatCodeItem(
              code: m['code'] as String,
              description: m['description'] as String,
              rate: (m['rate'] as num).toDouble(),
              reverseCharge: (m['reverse_charge'] as bool?) ?? false,
            ))
        .toList();
  }
}

final vatApiProvider = Provider<VatApi>((ref) => VatApi(NetworkService().client));










