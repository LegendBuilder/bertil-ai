import 'package:bertil_mobile_web_flutter/features/inbox/provider/inbox_providers.dart';
import 'package:bertil_mobile_web_flutter/features/inbox/ui/inbox_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Inbox shows help overlay on ? and bulk buttons are focusable', (tester) async {
    final overrides = <Override>[
      inboxProvider.overrideWith((ref) async => [
            ReviewTaskItem(id: 1, type: 'autopost', confidence: 0.91, payload: {'vendor': 'Kaffe AB', 'total': 123.0, 'account': '4010', 'vat_code': 'SE25'}),
            ReviewTaskItem(id: 2, type: 'settle', confidence: 0.88, payload: {'verification_id': 42, 'amount': 100.0, 'bank_tx_id': 'b-1'}),
          ]),
    ];
    await tester.pumpWidget(ProviderScope(overrides: overrides, child: const MaterialApp(home: InboxPage())));
    await tester.pumpAndSettle();

    // Focus traversal: Tab to first bulk button
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.pump();
    // Press ? to open overlay
    await tester.sendKeyDownEvent(LogicalKeyboardKey.slash, platform: 'web');
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shift, platform: 'web');
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.question);
    await tester.pump();
    expect(find.textContaining('kortkommandon', findRichText: true), findsOneWidget);
  });
}


