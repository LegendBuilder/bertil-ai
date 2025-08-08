import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/ledger_api.dart';

final trustSummaryProvider = FutureProvider<TrustSummary>((ref) async {
  final api = ref.watch(ledgerApiProvider);
  final now = DateTime.now();
  final year = now.year;
  return api.getComplianceSummary(year);
});


