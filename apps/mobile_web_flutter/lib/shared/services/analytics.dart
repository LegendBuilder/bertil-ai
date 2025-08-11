import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb, debugPrint;

import '../services/network.dart';

class AnalyticsService {
  static Future<void> logEvent(String name, [Map<String, dynamic>? params]) async {
    // Always log to console in debug for visibility
    if (kDebugMode) {
      debugPrint('Analytics: $name ${params ?? {}}');
    }
    // Best-effort fire-and-forget to backend metrics endpoint
    try {
      await NetworkService().client.post(
        '/metrics/event',
        data: {
          'name': name,
          'params': params ?? <String, dynamic>{},
          'platform': kIsWeb ? 'web' : 'mobile',
        },
      );
    } catch (_) {
      // Do not surface analytics failures to end users
    }
  }
}









