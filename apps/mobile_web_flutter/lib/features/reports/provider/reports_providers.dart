import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../ledger/data/ledger_api.dart';
import '../data/reports_api.dart';

final selectedYearProvider = StateProvider<int>((ref) => DateTime.now().year);

final trialBalanceProvider = FutureProvider<TrialBalance>((ref) async {
  final api = ref.watch(reportsApiProvider);
  final year = ref.watch(selectedYearProvider);
  return api.getTrialBalance(year);
});

final complianceScoreProvider = FutureProvider<int>((ref) async {
  final api = ref.watch(ledgerApiProvider);
  final year = ref.watch(selectedYearProvider);
  final trust = await api.getComplianceSummary(year);
  return trust.score;
});

final vatStatusTextProvider = FutureProvider<String>((ref) async {
  final tb = await ref.watch(trialBalanceProvider.future);
  // Heuristik: tolka 2610-2619 som utgående moms (positiv), 2640-2649 som ingående moms (negativ)
  double utgaende = 0;
  double ingaende = 0;
  for (final entry in tb.accounts.entries) {
    final acc = entry.key;
    final amt = entry.value;
    if (acc.startsWith('261') || acc.startsWith('262') || acc.startsWith('263')) {
      utgaende += amt.abs();
    }
    if (acc.startsWith('264')) {
      ingaende += amt.abs();
    }
  }
  final attBetala = (utgaende - ingaende).clamp(-999999999.0, 999999999.0);
  if (attBetala > 0.01) return 'Denna period: ${attBetala.toStringAsFixed(2)} kr att betala';
  if (attBetala < -0.01) return 'Denna period: ${(-attBetala).toStringAsFixed(2)} kr att få tillbaka';
  return 'Denna period: 0 kr';
});


