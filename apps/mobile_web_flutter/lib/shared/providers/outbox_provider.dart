import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/outbox.dart';

final outboxCountProvider = StreamProvider<int>((ref) async* {
  // very simple polling of count every few seconds
  final service = OutboxService();
  while (true) {
    final items = await service.list();
    yield items.length;
    await Future.delayed(const Duration(seconds: 5));
  }
});


