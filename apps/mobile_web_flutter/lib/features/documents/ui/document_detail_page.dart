import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../provider/document_providers.dart';

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
                        const Text('Exempel: "Valde 5811 (representation) p.g.a. ‘Lunch’ + 12% moms + belopp < 300 kr."'),
                        const Spacer(),
                        Wrap(spacing: 8, runSpacing: 8, children: const [
                          Chip(label: Text('AI: "Vet inte" tillgängligt')),
                          Chip(label: Text('WORM 7 år')),
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


