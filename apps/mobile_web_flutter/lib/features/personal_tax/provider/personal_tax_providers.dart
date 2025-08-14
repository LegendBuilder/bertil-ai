import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/personal_tax_api.dart';

// API provider
final personalTaxApiProvider = Provider((ref) => PersonalTaxApi());

// User profile provider for tax optimization
final userTaxProfileProvider = StateProvider<Map<String, dynamic>>((ref) => {
  'income': 450000,
  'family_status': 'single',
  'age': 35,
  'home_owner': true,
  'work_commute_km': 50,
  'medical_expenses_ytd': 0,
  'charity_donations_ytd': 0,
});

// Tax opportunities discovered from receipts
final taxOpportunitiesProvider = StateProvider<List<Map<String, dynamic>>>((ref) => []);

// Total potential savings tracker
final totalTaxSavingsProvider = StateProvider<double>((ref) => 0.0);

// Tax calendar provider
final taxCalendarProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.read(personalTaxApiProvider);
  return await api.getTaxCalendar();
});

// Receipt analysis provider
final receiptAnalysisProvider = StateProvider<Map<String, dynamic>?>((ref) => null);

// Family tax optimization provider
final familyOptimizationProvider = StateProvider<Map<String, dynamic>?>((ref) => null);

// Pension optimization provider
final pensionOptimizationProvider = StateProvider<Map<String, dynamic>?>((ref) => null);

// Tax refund estimate provider
final refundEstimateProvider = StateProvider<Map<String, dynamic>?>((ref) => null);

// Active tax benefits provider (for notifications)
final activeTaxBenefitsProvider = StateProvider<List<String>>((ref) => []);