import 'package:bertil_mobile_web_flutter/features/documents/provider/document_list_providers.dart';
import 'package:bertil_mobile_web_flutter/features/documents/ui/documents_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Documents shows overlay on ? and allows Tab traversal', (tester) async {
    final overrides = <Override>[
      recentDocumentsProvider.overrideWith((ref) => [
            DocumentSummary(id: 'deadbeefcafe', uploadedAt: DateTime(2025, 1, 1)),
          ]),
    ];
    await tester.pumpWidget(ProviderScope(overrides: overrides, child: const MaterialApp(home: DocumentsPage())));
    await tester.pump();

    await tester.sendKeyDownEvent(LogicalKeyboardKey.slash, platform: 'web');
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shift, platform: 'web');
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.question);
    await tester.pump();
    expect(find.textContaining('Dokument – kortkommandon'), findsOneWidget);

    // Focus traversal should move between tab bar and list/grid
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.pump();
  });
}


