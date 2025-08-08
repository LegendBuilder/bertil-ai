import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/document.dart';

class RecentDocumentsController extends StateNotifier<List<DocumentSummary>> {
  RecentDocumentsController() : super(const []);

  void add(DocumentSummary doc) {
    state = [doc, ...state].take(20).toList();
  }
}

final recentDocumentsProvider = StateNotifierProvider<RecentDocumentsController, List<DocumentSummary>>(
  (ref) => RecentDocumentsController(),
);


