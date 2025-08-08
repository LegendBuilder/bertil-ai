import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../ledger/data/ledger_api.dart';
import '../data/reports_api.dart';

final trialBalanceProvider = FutureProvider<TrialBalance>((ref) async {
  final api = ref.watch(reportsApiProvider);
  final year = DateTime.now().year;
  return api.getTrialBalance(year);
});

final complianceScoreProvider = FutureProvider<int>((ref) async {
  final api = ref.watch(ledgerApiProvider);
  final year = DateTime.now().year;
  final trust = await api.getComplianceSummary(year);
  return trust.score;
});


