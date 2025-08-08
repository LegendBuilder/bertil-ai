import 'dart:io';

import 'package:bertil_mobile_web_flutter/app/app.dart';
import 'package:bertil_mobile_web_flutter/features/auth/provider/auth_providers.dart';
import 'package:bertil_mobile_web_flutter/features/ledger/data/ledger_api.dart';
import 'package:bertil_mobile_web_flutter/features/ledger/provider/ledger_providers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Dashboard golden basic', (tester) async {
    final overrides = <Override>[
      authControllerProvider.overrideWith((ref) {
        final c = AuthController(BankIdApi(FakeDio()));
        c.state = const AuthState(isAuthenticated: true, user: {'name': 'Anna'});
        return c;
      }),
      ledgerApiProvider.overrideWithValue(_MockLedgerApi()),
    ];
    await tester.pumpWidget(ProviderScope(overrides: overrides, child: const BertilApp()));
    await tester.pumpAndSettle();
    expect(find.textContaining('Skatteverks-klart'), findsOneWidget);
  });
}

class _MockLedgerApi implements LedgerApi {
  @override
  Dio get _dio => throw UnimplementedError();

  @override
  Future<TrustSummary> getComplianceSummary(int year) async => TrustSummary(score: 90, flags: const []);
}

class FakeDio extends Dio {}


