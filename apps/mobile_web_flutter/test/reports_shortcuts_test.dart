import 'package:bertil_mobile_web_flutter/features/reports/ui/reports_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Reports shows shortcut overlay on ?', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: ReportsPage())));
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.slash, platform: 'web');
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shift, platform: 'web');
    await tester.pump();
    // Some environments need '?' direct
    await tester.sendKeyDownEvent(LogicalKeyboardKey.question);
    await tester.pump();
    expect(find.textContaining('Rapporter – kortkommandon'), findsOneWidget);
  });
}


