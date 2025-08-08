import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/document.dart';

class RecentDocumentsController extends StateNotifier<List<DocumentSummary>> {
  RecentDocumentsController() : super(const []);

  void add(DocumentSummary doc) {
    state = [doc, ...state].take(20).toList();
  }

  void markStatus(String id, DocumentStatus status) {
    state = [
      for (final d in state)
        if (d.id == id)
          (DocumentSummary(id: d.id, uploadedAt: d.uploadedAt, status: status))
        else
          d
    ];
  }
}

final recentDocumentsProvider = StateNotifierProvider<RecentDocumentsController, List<DocumentSummary>>(
  (ref) => RecentDocumentsController(),
);


