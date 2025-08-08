import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../provider/document_providers.dart';
import '../provider/document_list_providers.dart';
import '../domain/document.dart';
import '../provider/explainability_provider.dart';
import '../../ingest/data/ingest_api.dart';
import '../../ledger/data/ledger_api.dart';

class DocumentDetailPage extends ConsumerWidget {
  const DocumentDetailPage({super.key, required this.id});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncDoc = ref.watch(documentDetailProvider(id));
    return Scaffold(
      appBar: AppBar(title: Text('Dokument $id')),
      body: asyncDoc.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Fel: $e')),
        data: (doc) => LayoutBuilder(
          builder: (context, constraints) {
            final maxW = constraints.maxWidth;
            final maxH = constraints.maxHeight;
            return Row(
              children: [
                Expanded(
                  flex: 3,
                  child: Stack(
                    children: [
                      Semantics(
                        label: 'Dokumentbild',
                        child: Positioned.fill(
                          child: Image.network(
                            doc.imageUrl,
                            fit: BoxFit.contain,
                            errorBuilder: (_, __, ___) => const Center(child: Text('Bild saknas')),
                          ),
                        ),
                      ),
                      ...doc.boxes.map((b) {
                        return Positioned(
                          left: b.x * maxW,
                          top: b.y * maxH,
                          width: b.w * maxW,
                          height: b.h * maxH,
                          child: IgnorePointer(
                            child: Container(
                              decoration: BoxDecoration(
                                border: Border.all(color: Colors.amber, width: 2),
                                color: Colors.amber.withOpacity(0.1),
                              ),
                              child: Align(
                                alignment: Alignment.topLeft,
                                child: Container(
                                  color: Colors.amber,
                                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                                  child: Text(b.label, style: const TextStyle(fontSize: 10, color: Colors.black)),
                                ),
                              ),
                            ),
                          ),
                        );
                      }),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  flex: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('OCR-text:'),
                        const SizedBox(height: 8),
                        Text(doc.ocrText.isEmpty ? '(tom stub)' : doc.ocrText),
                        const SizedBox(height: 16),
                        const Text('Fält (AI)'),
                        const SizedBox(height: 8),
                        for (final f in doc.extractedFields)
                          ListTile(
                            dense: true,
                            contentPadding: EdgeInsets.zero,
                            title: Text('${f.key}: ${f.value}'),
                            subtitle: LinearProgressIndicator(
                              value: f.confidence.clamp(0.0, 1.0),
                              minHeight: 6,
                            ),
                          ),
                        const SizedBox(height: 16),
                        const Text('Varför valde vi detta?'),
                        const SizedBox(height: 8),
                        Builder(builder: (context) {
                          final reason = ref.watch(explainabilityProvider(doc));
                          return Text(reason);
                        }),
                        const Spacer(),
                        Wrap(spacing: 8, runSpacing: 8, children: [
                          ElevatedButton(
                            onPressed: () {
                              ref.read(recentDocumentsProvider.notifier).markStatus(id, DocumentStatus.waitingInfo);
                              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Markerad som "Väntar info"')));
                            },
                            child: const Text('Vet inte'),
                          ),
                          ElevatedButton(
                            onPressed: () async {
                              // auto-post stub using extracted fields
                              final vendor = doc.extractedFields.firstWhere(
                                (f) => f.key.toLowerCase() == 'vendor',
                                orElse: () => doc.extractedFields.first,
                              ).value;
                              final totalStr = doc.extractedFields.firstWhere(
                                (f) => f.key.toLowerCase() == 'total',
                                orElse: () => doc.extractedFields.first,
                              ).value;
                              final total = double.tryParse(totalStr.replaceAll(',', '.')) ?? 0.0;
                              final dateIso = doc.extractedFields.firstWhere(
                                (f) => f.key.toLowerCase() == 'date',
                                orElse: () => doc.extractedFields.first,
                              ).value;
                              final api = IngestApi(NetworkService().client);
                              final res = await api.autoPostFromExtracted(documentId: id, total: total, dateIso: dateIso, vendor: vendor);
                              // On success, mark doc as done
                              // ignore: use_build_context_synchronously
                              ref.read(recentDocumentsProvider.notifier).markStatus(id, DocumentStatus.done);
                              // ignore: use_build_context_synchronously
                              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Bokfört ✅ (V#${res['id']})')));
                            },
                            child: const Text('Bokför automatiskt'),
                          ),
                          OutlinedButton(
                            onPressed: () async {
                              final api = LedgerApi(NetworkService().client);
                              final r = await api._dio.get('/verifications/by-document/$id');
                              final data = r.data as Map<String, dynamic>;
                              final verId = data['id'] as int?;
                              if (verId != null) {
                                if (context.mounted) {
                                  Navigator.of(context).pushNamed('/verifications');
                                }
                              } else {
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Ingen verifikation hittad ännu')));
                                }
                              }
                            },
                            child: const Text('Öppna verifikation'),
                          ),
                          ElevatedButton(
                            onPressed: () {
                              ref.read(recentDocumentsProvider.notifier).markStatus(id, DocumentStatus.done);
                              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Markerad som Klar')));
                            },
                            child: const Text('Markera Klar'),
                          ),
                          const Chip(label: Text('WORM 7 år')),
                        ])
                      ],
                    ),
                  ),
                )
              ],
            );
          },
        ),
      ),
    );
  }
}


