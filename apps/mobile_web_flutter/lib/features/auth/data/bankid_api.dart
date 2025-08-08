import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/network.dart';

class BankIdApi {
  BankIdApi(this._dio);
  final Dio _dio;

  Future<({String orderRef, String autoStartToken})> init() async {
    final res = await _dio.post('/auth/bankid/init');
    final data = res.data as Map<String, dynamic>;
    return (orderRef: data['orderRef'] as String, autoStartToken: data['autoStartToken'] as String);
  }

  Future<({String status, Map<String, dynamic>? user})> status(String orderRef) async {
    final res = await _dio.get('/auth/bankid/status', queryParameters: {'orderRef': orderRef});
    final data = res.data as Map<String, dynamic>;
    return (status: data['status'] as String, user: data['user'] as Map<String, dynamic>?);
  }
}

final bankIdApiProvider = Provider<BankIdApi>((ref) {
  return BankIdApi(NetworkService().client);
});


