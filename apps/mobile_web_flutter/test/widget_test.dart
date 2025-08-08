import 'package:bertil_mobile_web_flutter/app/app.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

import 'package:bertil_mobile_web_flutter/features/auth/provider/auth_providers.dart';
import 'package:bertil_mobile_web_flutter/features/auth/data/bankid_api.dart';

void main() {
  testWidgets('App renders dashboard and bottom nav when authenticated', (tester) async {
    await tester.pumpWidget(ProviderScope(
      overrides: [
        authControllerProvider.overrideWith((ref) {
          final c = AuthController(BankIdApi(Dio(BaseOptions(baseUrl: 'http://localhost'))));
          c.state = const AuthState(isAuthenticated: true);
          return c;
        }),
      ],
      child: const BertilApp(),
    ));
    expect(find.text('Hem'), findsOneWidget);
    expect(find.text('Fota kvitto'), findsOneWidget);
    expect(find.text('Dokument'), findsOneWidget);
    expect(find.text('Rapporter'), findsOneWidget);
    expect(find.text('Konto'), findsOneWidget);
  });
}


