// ignore_for_file: use_build_context_synchronously
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:file_picker/file_picker.dart';
import 'package:image_picker/image_picker.dart';
import 'package:go_router/go_router.dart';
import '../../ingest/data/ingest_api.dart';
import '../../documents/provider/document_list_providers.dart';
import '../../documents/domain/document.dart';
import '../../../shared/providers/success_banner_provider.dart';
import '../../../shared/services/analytics.dart';
import '../../../shared/services/queue/queue_service.dart';
import '../provider/personal_tax_providers.dart';
import '../data/personal_tax_api.dart';

class EnhancedCapturePage extends ConsumerStatefulWidget {
  const EnhancedCapturePage({super.key});
  @override
  ConsumerState<EnhancedCapturePage> createState() => _EnhancedCapturePageState();
}

class _EnhancedCapturePageState extends ConsumerState<EnhancedCapturePage> {
  bool _busy = false;
  String? _message;
  Map<String, dynamic>? _detectedTaxBenefits;
  bool _showTaxAnalysis = false;

  Future<void> _pickAndUpload() async {
    setState(() {
      _busy = true;
      _message = 'Välj eller fota dokument…';
      _detectedTaxBenefits = null;
      _showTaxAnalysis = false;
    });
    
    Uint8List? pickedBytes;
    String filename = 'image.jpg';
    
    if (kIsWeb) {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.image, 
        allowMultiple: false, 
        withData: true
      );
      if (result == null || result.files.isEmpty) {
        setState(() {
          _busy = false;
          _message = 'Ingen fil vald';
        });
        return;
      }
      final file = result.files.first;
      pickedBytes = Uint8List.fromList(file.bytes!);
      filename = file.name;
    } else {
      final xfile = await ImagePicker().pickImage(
        source: ImageSource.camera, 
        imageQuality: 85
      );
      if (xfile == null) {
        setState(() {
          _busy = false;
          _message = 'Ingen bild tagen';
        });
        return;
      }
      pickedBytes = await xfile.readAsBytes();
      filename = xfile.name;
    }

    try {
      setState(() {
        _message = 'Laddar upp och analyserar…';
      });

      // Step 1: Upload for business processing (existing flow)
      final ingestApi = ref.read(ingestApiProvider);
      final uploaded = await ingestApi.uploadDocument(
        bytes: pickedBytes,
        filename: filename,
        meta: {'source': kIsWeb ? 'web_upload' : 'camera'},
      );
      
      // Create uploadResult format for backward compatibility
      final uploadResult = {
        'documentId': uploaded.documentId,
        'vendor': 'Unknown',
        'total': 0.0,
        'date': DateTime.now().toIso8601String().split('T')[0],
        'category': 'general',
        'description': '',
      };

      setState(() {
        _message = 'Analyserar för skatteavdrag…';
      });

      // Step 2: Analyze for personal tax benefits (NEW)
      await _analyzeTaxBenefits(uploadResult);

      setState(() {
        _message = 'Klart! Dokument sparat och skatteavdrag upptäckta.';
        _showTaxAnalysis = true;
      });

      // Update document list and analytics
      ref.invalidate(recentDocumentsProvider);
      AnalyticsService.logEvent('document_uploaded_with_tax_analysis', {
        'filename': filename,
        'has_tax_benefits': _detectedTaxBenefits != null,
        'tax_savings': _detectedTaxBenefits?['analysis']?['total_potential_savings'] ?? 0,
      });

      // Show success banner
      ref.read(successBannerProvider.notifier).show(
        'Dokument uppladdat! Skatteavdrag upptäckta: ${(_detectedTaxBenefits?['analysis']?['total_potential_savings'] ?? 0).toStringAsFixed(0)} SEK'
      );

    } catch (e) {
      setState(() {
        _message = 'Fel vid uppladdning: $e';
      });
    } finally {
      setState(() {
        _busy = false;
      });
    }
  }

  Future<void> _analyzeTaxBenefits(Map<String, dynamic> uploadResult) async {
    try {
      final personalTaxApi = ref.read(personalTaxApiProvider);
      final userProfile = ref.read(userTaxProfileProvider);

      // Extract receipt data from upload result
      final receiptData = {
        'vendor': uploadResult['vendor'] ?? 'Unknown',
        'total': uploadResult['total'] ?? 0.0,
        'date': uploadResult['date'] ?? DateTime.now().toIso8601String().split('T')[0],
        'category': uploadResult['category'] ?? 'general',
        'description': uploadResult['description'] ?? '',
      };

      // Analyze for tax benefits
      final taxAnalysis = await personalTaxApi.analyzeReceiptForAvdrag(
        receiptData: receiptData,
        userProfile: userProfile,
      );

      setState(() {
        _detectedTaxBenefits = taxAnalysis;
      });

      // Update global tax opportunities
      if (taxAnalysis['analysis'] != null) {
        final opportunities = ref.read(taxOpportunitiesProvider.notifier);
        final currentOpportunities = ref.read(taxOpportunitiesProvider);
        
        // Add new opportunities
        final newOpportunities = <Map<String, dynamic>>[];
        for (String category in taxAnalysis['analysis']['opportunities_by_category'].keys) {
          final categoryOpportunities = taxAnalysis['analysis']['opportunities_by_category'][category];
          for (var opp in categoryOpportunities) {
            newOpportunities.add({
              'category': category,
              'description': opp['description'],
              'savings': opp['tax_savings'],
              'confidence': opp['confidence'],
              'receipt': receiptData['vendor'],
            });
          }
        }
        
        opportunities.state = [...currentOpportunities, ...newOpportunities];

        // Update total savings
        final totalSavings = ref.read(totalTaxSavingsProvider.notifier);
        final additionalSavings = taxAnalysis['analysis']['total_potential_savings'] ?? 0.0;
        totalSavings.state = totalSavings.state + additionalSavings;
      }

    } catch (e) {
      debugPrint('Error analyzing tax benefits: $e');
      // Don't fail the entire upload if tax analysis fails
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart kvittoscanning'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Enhanced description
            Card(
              color: Colors.blue[50],
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.auto_awesome, color: Colors.blue[700]),
                        const SizedBox(width: 8),
                        const Text(
                          'AI-driven kvittoanalys',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Ladda upp ditt kvitto så kommer vår AI automatiskt:\n'
                      '• Bokföra för företag\n'
                      '• Upptäcka privata skatteavdrag\n'
                      '• Beräkna potentiella besparingar\n'
                      '• Föreslå optimeringsstrategier',
                      style: TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 24),

            // Upload button
            ElevatedButton.icon(
              onPressed: _busy ? null : _pickAndUpload,
              icon: _busy 
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Icon(Icons.camera_alt),
              label: Text(_busy ? 'Analyserar...' : 'Fota eller ladda upp kvitto'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue[700],
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                textStyle: const TextStyle(fontSize: 16),
              ),
            ),

            const SizedBox(height: 16),

            // Status message
            if (_message != null)
              Card(
                color: _message!.contains('Fel') ? Colors.red[50] : Colors.green[50],
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Row(
                    children: [
                      Icon(
                        _message!.contains('Fel') ? Icons.error : Icons.info,
                        color: _message!.contains('Fel') ? Colors.red[700] : Colors.green[700],
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _message!,
                          style: TextStyle(
                            color: _message!.contains('Fel') ? Colors.red[700] : Colors.green[700],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 24),

            // Tax analysis results
            if (_showTaxAnalysis && _detectedTaxBenefits != null)
              Expanded(
                child: SingleChildScrollView(
                  child: Card(
                    elevation: 4,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.savings, color: Colors.green[700]),
                              const SizedBox(width: 8),
                              const Text(
                                'Discovered Tax Benefits',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                          
                          const SizedBox(height: 16),
                          
                          // Total savings
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.green[50],
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Potential Tax Savings:',
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                                Text(
                                  '${(_detectedTaxBenefits!['analysis']?['total_potential_savings'] ?? 0).toStringAsFixed(0)} SEK',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: Colors.green[700],
                                    fontSize: 16,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          
                          const SizedBox(height: 16),
                          
                          // Recommendations
                          if (_detectedTaxBenefits!['analysis']?['recommendations'] != null)
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'AI Recommendations:',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                ...(_detectedTaxBenefits!['analysis']['recommendations'] as List)
                                    .map<Widget>((rec) => Padding(
                                          padding: const EdgeInsets.symmetric(vertical: 4),
                                          child: Row(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Icon(Icons.lightbulb, 
                                                   color: Colors.amber[700], 
                                                   size: 16),
                                              const SizedBox(width: 8),
                                              Expanded(child: Text(rec.toString())),
                                            ],
                                          ),
                                        ))
                                    .toList(),
                              ],
                            ),

                          const SizedBox(height: 16),

                          // Action buttons
                          Row(
                            children: [
                              Expanded(
                                child: ElevatedButton(
                                  onPressed: () => context.go('/personal-tax'),
                                  child: const Text('View Tax Dashboard'),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: OutlinedButton(
                                  onPressed: () => _pickAndUpload(),
                                  child: const Text('Upload Another'),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}