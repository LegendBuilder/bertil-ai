import 'package:bertil_mobile_web_flutter/features/documents/provider/document_list_providers.dart';
import 'package:bertil_mobile_web_flutter/features/documents/ui/documents_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('DocumentsPage shows empty state then list', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: DocumentsPage())));
    expect(find.textContaining('Smarta listor'), findsOneWidget);

    // Populate recent docs and rebuild
    final container = ProviderScope.containerOf(tester.element(find.byType(DocumentsPage)));
    container.read(recentDocumentsProvider.notifier).add(
          // ignore: prefer_const_constructors
          DocumentSummary(id: 'deadbeef', uploadedAt: DateTime(2024, 1, 1)),
        );
    await tester.pump();
    expect(find.textContaining('Dokument'), findsWidgets);
  });
}


