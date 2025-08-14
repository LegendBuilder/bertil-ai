import '../../../shared/services/network.dart';

class PersonalTaxApi {
  final NetworkService _networkService = NetworkService();

  /// Analyze a receipt for personal tax deductions
  Future<Map<String, dynamic>> analyzeReceiptForAvdrag({
    required Map<String, dynamic> receiptData,
    required Map<String, dynamic> userProfile,
  }) async {
    try {
      final response = await _networkService.client.post(
        '/personal-tax/analyze-receipt',
        data: {
          'receipt_data': receiptData,
          'user_profile': userProfile,
        },
      );
      
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to analyze receipt for tax benefits: $e');
    }
  }

  /// Optimize family taxes
  Future<Map<String, dynamic>> optimizeFamilyTaxes({
    required Map<String, dynamic> familyData,
  }) async {
    try {
      final response = await _networkService.client.post(
        '/personal-tax/optimize-family-taxes',
        data: {
          'family_data': familyData,
        },
      );
      
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to optimize family taxes: $e');
    }
  }

  /// Get pension optimization recommendations
  Future<Map<String, dynamic>> optimizePensions({
    required Map<String, dynamic> financialData,
  }) async {
    try {
      final response = await _networkService.client.post(
        '/personal-tax/pension-optimization',
        data: {
          'financial_data': financialData,
        },
      );
      
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to optimize pensions: $e');
    }
  }

  /// Get tax calendar with important dates
  Future<Map<String, dynamic>> getTaxCalendar() async {
    try {
      final response = await _networkService.client.get('/personal-tax/tax-calendar');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to get tax calendar: $e');
    }
  }

  /// Estimate tax refund
  Future<Map<String, dynamic>> estimateRefund({
    required Map<String, dynamic> incomeData,
  }) async {
    try {
      final response = await _networkService.client.post(
        '/personal-tax/estimate-refund',
        data: {
          'income_data': incomeData,
        },
      );
      
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to estimate refund: $e');
    }
  }

  /// Generate skattedeklaration (when API available)
  Future<Map<String, dynamic>> generateSkattedeklaration() async {
    try {
      final response = await _networkService.client.post(
        '/personal-tax/generate-skattedeklaration',
        data: {},
      );
      
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to generate skattedeklaration: $e');
    }
  }
}