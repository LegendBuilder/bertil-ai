import 'package:bertil_mobile_web_flutter/features/reports/ui/reports_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Reports shows shortcut overlay on ?', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MaterialApp(home: ReportsPage())));
    await tester.pump();
    // Use logical keys shift + slash to trigger overlay reliably in VM
    await tester.sendKeyEvent(LogicalKeyboardKey.shift);
    await tester.sendKeyEvent(LogicalKeyboardKey.slash);
    await tester.pump();
    expect(find.textContaining('Rapporter – kortkommandon'), findsOneWidget);
  });
}


