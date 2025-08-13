import 'dart:async';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

import '../services/outbox_replay.dart';

final connectivityProvider = StreamProvider<bool>((ref) async* {
  if (kIsWeb) {
    // Web: listen to navigator.onLine via periodic check
    bool last = true;
    while (true) {
      final online = _isWebOnline();
      if (online && !last) {
        OutboxReplayer().start();
      }
      last = online;
      yield online;
      await Future.delayed(const Duration(seconds: 3));
    }
  } else {
    final conn = Connectivity();
    await for (final status in conn.onConnectivityChanged) {
      final online = status != ConnectivityResult.none;
      if (online) OutboxReplayer().start();
      yield online;
    }
  }
});

bool _isWebOnline() => true; // fallback; robust detection can be added with js interop


