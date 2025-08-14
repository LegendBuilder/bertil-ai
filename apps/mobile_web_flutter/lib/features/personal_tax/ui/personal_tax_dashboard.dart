import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../provider/personal_tax_providers.dart';

class PersonalTaxDashboard extends ConsumerStatefulWidget {
  const PersonalTaxDashboard({super.key});

  @override
  ConsumerState<PersonalTaxDashboard> createState() => _PersonalTaxDashboardState();
}

class _PersonalTaxDashboardState extends ConsumerState<PersonalTaxDashboard> {
  
  @override
  Widget build(BuildContext context) {
    final totalSavings = ref.watch(totalTaxSavingsProvider);
    final taxOpportunities = ref.watch(taxOpportunitiesProvider);
    final userProfile = ref.watch(userTaxProfileProvider);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Skatteavdrag'),
        actions: [
          IconButton(
            tooltip: 'Hjälp',
            onPressed: () {},
            icon: const Icon(Icons.help_outline),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Summary Card matching the existing trust meter style
            Card(
              color: Colors.blue.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.savings_outlined, color: Colors.blue),
                        const SizedBox(width: 8),
                        const Text(
                          'Upptäckta avdrag',
                          style: TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${totalSavings.toStringAsFixed(0)} kr sparas',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.blue,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Potential skatteåterbäring upptäckt av AI',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Quick Actions - matching documents page style
            Wrap(spacing: 8, runSpacing: 8, children: [
              ElevatedButton.icon(
                onPressed: () => _scanReceipt(context),
                icon: const Icon(Icons.camera_alt_outlined),
                label: const Text('Fota kvitto med avdrag'),
              ),
              OutlinedButton.icon(
                onPressed: () => _optimizeFamily(context),
                icon: const Icon(Icons.family_restroom_outlined),
                label: const Text('Familjeoptimering'),
              ),
            ]),
            const SizedBox(height: 8),
            Wrap(spacing: 8, runSpacing: 8, children: [
              OutlinedButton.icon(
                onPressed: () => _optimizePensions(context),
                icon: const Icon(Icons.account_balance_outlined),
                label: const Text('IPS & pension'),
              ),
              OutlinedButton.icon(
                onPressed: () => _estimateRefund(context),
                icon: const Icon(Icons.calculate_outlined),
                label: const Text('Beräkna återbäring'),
              ),
            ]),
            
            const SizedBox(height: 24),
            
            // Discovered Opportunities
            if (taxOpportunities.isNotEmpty) ...[
              const Text(
                'Upptäckta avdrag',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
              
              ...taxOpportunities.map((opportunity) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: _getCategoryColor(opportunity['category']),
                    child: Icon(
                      _getCategoryIcon(opportunity['category']),
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                  title: Text(
                    opportunity['category'] ?? 'Avdrag',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    opportunity['description'] ?? 'Skatteoptimering upptäckt',
                  ),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        '${opportunity['savings']?.toStringAsFixed(0) ?? '0'} kr',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.green[700],
                        ),
                      ),
                      Text(
                        '${((opportunity['confidence'] ?? 0.5) * 100).toStringAsFixed(0)}% confidence',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
              )).toList(),
            ],
            
            const SizedBox(height: 24),
            
            // User Profile Summary
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Skatteprofil',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _buildProfileRow('Årsinkomst', '${userProfile['income']} kr'),
                    _buildProfileRow('Familjesituation', _translateFamilyStatus(userProfile['family_status'])),
                    _buildProfileRow('Ålder', userProfile['age'].toString()),
                    _buildProfileRow('Bostadsägare', userProfile['home_owner'] ? 'Ja' : 'Nej'),
                    _buildProfileRow('Pendling', '${userProfile['work_commute_km']} km'),
                    const SizedBox(height: 12),
                    ElevatedButton(
                      onPressed: () => _editProfile(context),
                      child: const Text('Uppdatera profil'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  String _translateFamilyStatus(String status) {
    switch (status) {
      case 'single':
        return 'Singel';
      case 'married':
        return 'Gift';
      case 'sambo':
        return 'Sambo';
      default:
        return status;
    }
  }
  
  Widget _buildActionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color, size: 32),
              const SizedBox(height: 8),
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 12,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildProfileRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey[600])),
          Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
  
  Color _getCategoryColor(String? category) {
    switch (category?.toLowerCase()) {
      case 'rot':
        return Colors.orange;
      case 'rut':
        return Colors.blue;
      case 'medical expenses':
        return Colors.red;
      case 'work equipment':
        return Colors.purple;
      case 'travel expenses':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
  
  IconData _getCategoryIcon(String? category) {
    switch (category?.toLowerCase()) {
      case 'rot':
        return Icons.home_repair_service;
      case 'rut':
        return Icons.cleaning_services;
      case 'medical expenses':
        return Icons.local_hospital;
      case 'work equipment':
        return Icons.work;
      case 'travel expenses':
        return Icons.directions_car;
      default:
        return Icons.savings;
    }
  }
  
  void _scanReceipt(BuildContext context) {
    // Navigate to receipt scanning with tax analysis
    context.go('/enhanced-capture');
  }
  
  void _optimizeFamily(BuildContext context) {
    // Show family optimization dialog
    _showFamilyOptimizationDialog(context);
  }
  
  void _optimizePensions(BuildContext context) {
    // Show pension optimization dialog
    _showPensionOptimizationDialog(context);
  }
  
  void _estimateRefund(BuildContext context) {
    // Show refund estimation dialog
    _showRefundEstimationDialog(context);
  }
  
  void _editProfile(BuildContext context) {
    // Show profile editing dialog
    _showProfileEditDialog(context);
  }
  
  void _showFamilyOptimizationDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Familjeoptimering'),
        content: const Text(
          'AI kommer analysera din familjesituation för att hitta optimala skattestrategier för gifta par, sambos och barn.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Avbryt'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _runFamilyOptimization();
            },
            child: const Text('Optimera'),
          ),
        ],
      ),
    );
  }
  
  void _showPensionOptimizationDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Pensionsoptimering'),
        content: const Text(
          'Få personliga rekommendationer för IPS, tjänstepension och andra pensionssparande för att maximera skatteavdrag.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Avbryt'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _runPensionOptimization();
            },
            child: const Text('Optimera'),
          ),
        ],
      ),
    );
  }
  
  void _showRefundEstimationDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Beräkna skatteåterbäring'),
        content: const Text(
          'Beräkna din uppskattade skatteåterbäring baserat på upptäckta avdrag och preliminära skattebetalningar.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Avbryt'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _runRefundEstimation();
            },
            child: const Text('Beräkna'),
          ),
        ],
      ),
    );
  }
  
  void _showProfileEditDialog(BuildContext context) {
    final profileNotifier = ref.read(userTaxProfileProvider.notifier);
    final currentProfile = ref.read(userTaxProfileProvider);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Uppdatera skatteprofil'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                decoration: const InputDecoration(labelText: 'Årsinkomst (kr)'),
                keyboardType: TextInputType.number,
                controller: TextEditingController(text: currentProfile['income'].toString()),
                onChanged: (value) {
                  final income = int.tryParse(value) ?? currentProfile['income'];
                  profileNotifier.update((state) => {...state, 'income': income});
                },
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(labelText: 'Familjesituation'),
                value: currentProfile['family_status'],
                items: const [
                  DropdownMenuItem(value: 'single', child: Text('Singel')),
                  DropdownMenuItem(value: 'married', child: Text('Gift')),
                  DropdownMenuItem(value: 'sambo', child: Text('Sambo')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    profileNotifier.update((state) => {...state, 'family_status': value});
                  }
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Avbryt'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Spara'),
          ),
        ],
      ),
    );
  }
  
  void _runFamilyOptimization() async {
    try {
      final api = ref.read(personalTaxApiProvider);
      final userProfile = ref.read(userTaxProfileProvider);
      
      final result = await api.optimizeFamilyTaxes(
        familyData: {
          'status': userProfile['family_status'],
          'user_income': userProfile['income'],
          'spouse_income': 320000, // Demo value
          'children': [], // Demo value
        },
      );
      
      ref.read(familyOptimizationProvider.notifier).state = result;
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Familjeoptimering klar!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }
  
  void _runPensionOptimization() async {
    try {
      final api = ref.read(personalTaxApiProvider);
      final userProfile = ref.read(userTaxProfileProvider);
      
      final result = await api.optimizePensions(
        financialData: {
          'annual_income': userProfile['income'],
          'age': userProfile['age'],
          'existing_pension': 450000, // Demo value
          'risk_tolerance': 'moderate',
        },
      );
      
      ref.read(pensionOptimizationProvider.notifier).state = result;
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Pensionsoptimering klar!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }
  
  void _runRefundEstimation() async {
    try {
      final api = ref.read(personalTaxApiProvider);
      final userProfile = ref.read(userTaxProfileProvider);
      
      final result = await api.estimateRefund(
        incomeData: {
          'gross_income': userProfile['income'],
          'preliminary_tax_paid': userProfile['income'] * 0.32, // Demo calculation
          'discovered_deductions': [
            {'category': 'ROT', 'amount': 15000},
            {'category': 'IPS', 'amount': 7000},
            {'category': 'Medical', 'amount': 3000},
          ],
        },
      );
      
      ref.read(refundEstimateProvider.notifier).state = result;
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Skatteåterbäring beräknad!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }
}