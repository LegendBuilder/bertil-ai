import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/services/network.dart';

class ReviewTaskItem {
  ReviewTaskItem({required this.id, required this.type, required this.confidence, required this.payload});
  final int id;
  final String type; // e.g., autopost | settle | vat
  final double confidence;
  final Map<String, dynamic> payload;
}

final inboxProvider = FutureProvider<List<ReviewTaskItem>>((ref) async {
  final dio = NetworkService().client;
  final res = await dio.get('/review/inbox');
  final items = (res.data['items'] as List).cast<Map<String, dynamic>>();
  return items
      .map((m) => ReviewTaskItem(
            id: m['id'] as int,
            type: m['type'] as String,
            confidence: (m['confidence'] as num).toDouble(),
            payload: (m['payload'] as Map).cast<String, dynamic>(),
          ))
      .toList();
});

final pendingTasksCountProvider = FutureProvider<int>((ref) async {
  final items = await ref.watch(inboxProvider.future);
  return items.length;
});




