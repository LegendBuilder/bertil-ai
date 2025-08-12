import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';

class QueueService {
  QueueService();
  static Future<QueueService> create() async => QueueService();
  Future<int> enqueueUpload({required String filename, required Uint8List bytes, required Map<String, dynamic> meta}) async => 0;
  Future<void> processQueue({int maxRetries = 5}) async {}
  Stream<int> watchPendingCount() async* {}
}

final queueServiceProvider = FutureProvider<QueueService>((ref) async => QueueService.create());


