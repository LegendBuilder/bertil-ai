import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../provider/document_list_providers.dart';
import '../domain/document.dart';

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
          : DefaultTabController(
              length: 4,
              child: Column(
                children: [
                  const TabBar(tabs: [
                    Tab(text: 'Nya'),
                    Tab(text: 'Väntar info'),
                    Tab(text: 'Klara'),
                    Tab(text: 'Alla'),
                  ]),
                  Expanded(
                    child: TabBarView(children: [
                      _DocList(docs: recent.where((d) => d.status == DocumentStatus.newDoc).toList()),
                      _DocList(docs: recent.where((d) => d.status == DocumentStatus.waitingInfo).toList()),
                      _DocList(docs: recent.where((d) => d.status == DocumentStatus.done).toList()),
                      _DocList(docs: recent),
                    ]),
                  ),
                ],
              ),
            ),
    );
  }
}

class _DocList extends StatelessWidget {
  const _DocList({required this.docs});
  final List<DocumentSummary> docs;

  @override
  Widget build(BuildContext context) {
    if (docs.isEmpty) return const Center(child: Text('Inga dokument här'));
    return ListView.separated(
      itemCount: docs.length,
      separatorBuilder: (_, __) => const Divider(height: 1),
      itemBuilder: (context, i) {
        final d = docs[i];
        final chip = d.status == DocumentStatus.newDoc
            ? const Chip(label: Text('Ny'))
            : d.status == DocumentStatus.waitingInfo
                ? const Chip(label: Text('Väntar info'))
                : const Chip(label: Text('Klar'));
        return ListTile(
          title: Text('Dokument ${d.id.substring(0, 8)}…'),
          subtitle: Text('Uppladdat ${d.uploadedAt.toLocal()}'),
          trailing: chip,
          onTap: () => Navigator.of(context).pushNamed('/documents/${d.id}'),
        );
      },
    );
  }
}


