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
                        const Spacer(),
                        Row(
                          children: const [
                            Chip(label: Text('AI: "Vet inte" tillgängligt')),
                            SizedBox(width: 8),
                            Chip(label: Text('WORM 7 år')),
                          ],
                        )
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


