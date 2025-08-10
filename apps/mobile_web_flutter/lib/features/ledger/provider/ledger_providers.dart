import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/ledger_api.dart';
import '../../documents/provider/document_list_providers.dart';
import '../domain/next_action.dart';

/// Local, ephemeral set of dismissed compliance flags (by rule_code) for optimistic UI.
final dismissedFlagsProvider = StateProvider<Set<String>>((ref) => <String>{});

final trustSummaryProvider = FutureProvider<TrustSummary>((ref) async {
  final api = ref.watch(ledgerApiProvider);
  final now = DateTime.now();
  final year = now.year;
  return api.getComplianceSummary(year);
});

final recentVerificationsProvider = FutureProvider<List<VerificationSummary>>((ref) async {
  final api = ref.watch(ledgerApiProvider);
  return api.listVerifications(year: DateTime.now().year);
});

final nextActionProvider = Provider<NextAction>((ref) {
  final recentDocs = ref.watch(recentDocumentsProvider);
  if (recentDocs.isEmpty) {
    return NextAction(
      title: 'Fota ditt första kvitto',
      subtitle: 'Det tar 20 sekunder – vi sköter resten',
      route: '/capture',
      ctaLabel: 'Öppna kamera',
    );
  }
  return NextAction(
    title: 'Granska senaste dokument',
    subtitle: 'Säkerställ att allt ser rätt ut',
    route: '/documents/${recentDocs.first.id}',
    ctaLabel: 'Öppna',
  );
});


