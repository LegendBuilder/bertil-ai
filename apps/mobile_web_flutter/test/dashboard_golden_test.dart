import 'package:bertil_mobile_web_flutter/app/app.dart';
import 'package:bertil_mobile_web_flutter/features/auth/provider/auth_providers.dart';
import 'package:bertil_mobile_web_flutter/features/auth/data/bankid_api.dart';
import 'package:bertil_mobile_web_flutter/features/ledger/data/ledger_api.dart';
import 'package:bertil_mobile_web_flutter/features/ledger/provider/ledger_providers.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Dashboard golden basic', (tester) async {
    final overrides = <Override>[
      authControllerProvider.overrideWith((ref) {
        final c = AuthController(BankIdApi(Dio()));
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
  Future<TrustSummary> getComplianceSummary(int year) async => TrustSummary(score: 90, flags: const []);

  @override
  Future<List<VerificationSummary>> listVerifications({int? year}) async => [];

  @override
  Future<VerificationDetail> getVerification(int id) async =>
      VerificationDetail(id: id, immutableSeq: 1, date: '2025-01-01', totalAmount: 0, currency: 'SEK', entries: const [], auditHash: '');

  @override
  Future<List<Map<String, dynamic>>> getVerificationFlags(int id) async => [];

  @override
  Future<Map<String, dynamic>> correctVerificationDate({required int id, required String newDateIso}) async => {};

  @override
  Future<Map<String, dynamic>> correctVerificationDocument({required int id, required String documentId}) async => {};

  @override
  Future<int> createVerification({required int orgId, required String dateIso, required double totalAmount, String currency = 'SEK', double? vatAmount, String? counterparty, String? documentLink, required List<Map<String, dynamic>> entries}) async => 1;

  @override
  Future<Map<String, dynamic>> reverseVerification(int id) async => {};
}


