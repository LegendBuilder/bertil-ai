import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'network.dart';
import 'outbox.dart';

class OutboxReplayer {
  OutboxReplayer._();
  static final OutboxReplayer _instance = OutboxReplayer._();
  factory OutboxReplayer() => _instance;

  Timer? _timer;

  void start({Duration interval = const Duration(seconds: 7)}) {
    _timer?.cancel();
    _timer = Timer.periodic(interval, (_) => _tick());
  }

  void stop() {
    _timer?.cancel();
    _timer = null;
  }

  Future<void> _tick() async {
    try {
      final items = await OutboxService().list();
      if (items.isEmpty) return;
      final dio = NetworkService().client;
      for (final it in items.take(5)) { // avoid burst
        try {
          final req = Options(method: it.method, headers: it.headers);
          final res = await dio.request(it.url, data: it.body, options: req);
          if (res.statusCode != null && res.statusCode! >= 200 && res.statusCode! < 300) {
            await OutboxService().removeById(it.id);
          }
        } catch (_) {
          // backoff on failures automatically by timer interval
        }
      }
    } catch (_) {}
  }
}


