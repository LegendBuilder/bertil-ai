import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../provider/document_list_providers.dart';

class DocumentsPage extends ConsumerWidget {
  const DocumentsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recent = ref.watch(recentDocumentsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Dokument')),
      body: recent.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('Låt oss fota ditt första kvitto. Det tar 20 sek.'),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    onPressed: () => Navigator.of(context).pushNamed('/capture'),
                    icon: const Icon(Icons.camera_alt_outlined),
                    label: const Text('Öppna kamera'),
                  ),
                ],
              ),
            )
          : ListView.separated(
              itemCount: recent.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, i) {
                final d = recent[i];
                return ListTile(
                  title: Text('Dokument ${d.id.substring(0, 8)}…'),
                  subtitle: Text('Uppladdat ${d.uploadedAt.toLocal()}'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.of(context).pushNamed('/documents/${d.id}'),
                );
              },
            ),
    );
  }
}


