// ignore_for_file: use_build_context_synchronously
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
// Dropzone is optional and disabled by default due to version conflicts on web
// import 'package:flutter_dropzone/flutter_dropzone.dart';
import 'package:file_picker/file_picker.dart';
import 'package:image_picker/image_picker.dart';
import '../../../shared/services/queue/queue_service.dart';
// Dropzone behind a feature flag to avoid version conflicts
import '../../ingest/data/ingest_api.dart';
import '../provider/document_list_providers.dart';
import '../domain/document.dart';
import '../../../shared/services/network.dart';
import 'package:flutter/services.dart';
import '../../../shared/widgets/app_bar_accent.dart';
import '../../../shared/widgets/shortcut_help_overlay.dart';
import '../../../shared/widgets/skeleton.dart';

class DocumentsPage extends ConsumerWidget {
  const DocumentsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recent = ref.watch(recentDocumentsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dokument'),
        actions: [
          IconButton(
            tooltip: 'Kortkommandon',
            onPressed: () => ShortcutHelpOverlay.show(context, const [
              MapEntry('N', 'Fota kvitto'),
              MapEntry('U', 'Ladda upp från filer'),
              MapEntry('D', 'Visa tips om dropzone'),
              MapEntry('Tab/Shift+Tab', 'Navigera i listor'),
              MapEntry('?', 'Visa denna hjälp'),
            ], title: 'Dokument – kortkommandon'),
            icon: const Icon(Icons.help_outline),
          ),
        ],
        bottom: appBarAccent(context),
      ),
      body: Shortcuts(
        shortcuts: <LogicalKeySet, Intent>{
          LogicalKeySet(LogicalKeyboardKey.keyN): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.keyU): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.keyD): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.shift, LogicalKeyboardKey.slash): const ActivateIntent(),
        },
        child: Actions(
          actions: <Type, Action<Intent>>{
            ActivateIntent: CallbackAction<ActivateIntent>(onInvoke: (intent) {
              final keys = RawKeyboard.instance.keysPressed;
              if (keys.contains(LogicalKeyboardKey.keyN)) {
                if (context.mounted) context.go('/capture');
              } else if (keys.contains(LogicalKeyboardKey.keyU)) {
                _uploadFromPicker(context, ref);
              } else if (keys.contains(LogicalKeyboardKey.keyD)) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aktivera ENABLE_DROPZONE för DnD')));
              } else if (keys.contains(LogicalKeyboardKey.slash) && keys.contains(LogicalKeyboardKey.shift)) {
                ShortcutHelpOverlay.show(context, const [
                  MapEntry('N', 'Fota kvitto'),
                  MapEntry('U', 'Ladda upp från filer'),
                  MapEntry('D', 'Visa tips om dropzone'),
                  MapEntry('Tab/Shift+Tab', 'Navigera i listor'),
                  MapEntry('?', 'Visa denna hjälp'),
                ], title: 'Dokument – kortkommandon');
              }
              return null;
            }),
          },
          child: recent.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('Låt oss fota ditt första kvitto. Det tar 20 sek.'),
                  const SizedBox(height: 12),
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    ElevatedButton.icon(
                      onPressed: () => context.go('/capture'),
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: const Text('Öppna kamera'),
                    ),
                    OutlinedButton.icon(
                       onPressed: () async {
                         await _uploadFromPicker(context, ref);
                       },
                      icon: const Icon(Icons.upload_file),
                      label: const Text('Ladda upp'),
                    ),
                  ]),
                  const SizedBox(height: 20),
                  const SkeletonBox(width: 200, height: 18),
                  const SizedBox(height: 8),
                  const SkeletonBox(width: 240, height: 18),
                  const SizedBox(height: 8),
                  const SkeletonBox(width: 180, height: 18),
                ],
              ),
            )
          : RefreshIndicator(
              onRefresh: () async {
                // simple pull-to-refresh: no-op on provider (demo), rely on network cache invalidation if added later
                await Future<void>.delayed(const Duration(milliseconds: 300));
              },
              child: DefaultTabController(
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
                      _DocGrid(docs: recent.where((d) => d.status == DocumentStatus.newDoc).toList()),
                      _DocList(docs: recent.where((d) => d.status == DocumentStatus.waitingInfo).toList()),
                      _DocList(docs: recent.where((d) => d.status == DocumentStatus.done).toList()),
                      _DocGrid(docs: recent),
                    ]),
                  ),
                ],
              ),
              ),
            ),
        ),
      ),
      // Optional dropzone area below content
      bottomSheet: kIsWeb && const bool.fromEnvironment('ENABLE_DROPZONE', defaultValue: false)
          ? SizedBox(
              height: 140,
              child: _DropZone(onFiles: (files) async {
                for (final f in files) {
                  final name = await f.getFilename();
                  final bytes = await f.getFileData();
                  await _uploadBytes(context, ref, bytes, name, source: 'dropzone');
                }
              }),
            )
          : null,
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final choice = await showModalBottomSheet<String>(
            context: context,
            showDragHandle: true,
            builder: (ctx) => SafeArea(
              child: Wrap(children: [
                ListTile(
                  leading: const Icon(Icons.camera_alt_outlined),
                  title: const Text('Fota kvitto'),
                  onTap: () => Navigator.pop(ctx, 'camera'),
                ),
                ListTile(
                  leading: const Icon(Icons.upload_file),
                  title: const Text('Ladda upp från filer'),
                  onTap: () => Navigator.pop(ctx, 'upload'),
                ),
              ]),
            ),
          );
          if (choice == 'camera') {
            if (context.mounted) context.go('/capture');
          } else if (choice == 'upload') {
              await _uploadFromPicker(context, ref);
          } else if (choice == 'dropzone') {
              if (kIsWeb) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aktivera dropzone-flagga i build för DnD')));
              } else {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Dropzone endast på webben')));
              }
          }
        },
        icon: const Icon(Icons.add_circle_outline),
        label: const Text('Lägg till dokument'),
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
        return Semantics(
          container: true,
          label: 'Dokument ${d.id.substring(0, 8)} uppladdat ${d.uploadedAt.toLocal()}',
          child: ListTile(
            title: Text('Dokument ${d.id.substring(0, 8)}…'),
            subtitle: Text('Uppladdat ${d.uploadedAt.toLocal()}'),
            trailing: ExcludeSemantics(child: chip),
            onTap: () => context.go('/documents/${d.id}'),
          ),
        );
      },
    );
  }
}

class _DocGrid extends StatelessWidget {
  const _DocGrid({required this.docs});
  final List<DocumentSummary> docs;

  @override
  Widget build(BuildContext context) {
    if (docs.isEmpty) return const Center(child: Text('Inga dokument här'));
    final w = MediaQuery.of(context).size.width;
    final crossAxisCount = w > 1200 ? 4 : w > 800 ? 3 : 2;
    return GridView.builder(
      padding: const EdgeInsets.all(12),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: crossAxisCount,
        childAspectRatio: 1,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
      ),
      itemCount: docs.length,
      itemBuilder: (context, i) {
        final d = docs[i];
        final chip = d.status == DocumentStatus.newDoc
            ? const Chip(label: Text('Ny'))
            : d.status == DocumentStatus.waitingInfo
                ? const Chip(label: Text('Väntar info'))
                : const Chip(label: Text('Klar'));
        final thumbUrl = '${NetworkService().client.options.baseUrl}/documents/${d.id}/thumbnail';
        return InkWell(
          onTap: () => context.go('/documents/${d.id}'),
          child: Hero(
            tag: 'doc_${d.id}',
            child: Card(
            clipBehavior: Clip.hardEdge,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  child: Stack(children: [
                    Positioned.fill(
                      child: Semantics(
                        label: 'Dokumentminiatyr',
                        image: true,
                          child: Image.network(thumbUrl, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const Center(child: Icon(Icons.receipt_long_outlined, size: 32))),
                      ),
                    ),
                  ]),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(d.id.substring(0, 6), style: const TextStyle(fontWeight: FontWeight.w600)),
                      ExcludeSemantics(child: chip),
                    ],
                  ),
                )
              ],
            ),
          ),
          ),
        );
      },
    );
  }
}

Future<void> _uploadFromPicker(BuildContext context, WidgetRef ref) async {
  Uint8List? bytes;
  String filename = 'image.jpg';
  if (kIsWeb) {
    final result = await FilePicker.platform.pickFiles(type: FileType.image, allowMultiple: false, withData: true);
    if (result == null || result.files.isEmpty) return;
    bytes = Uint8List.fromList(result.files.first.bytes!);
    filename = result.files.first.name;
  } else {
    final xfile = await ImagePicker().pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (xfile == null) return;
    bytes = await xfile.readAsBytes();
    filename = xfile.name;
  }
  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Laddar upp…')));
  try {
    await _uploadBytes(context, ref, bytes!, filename, source: kIsWeb ? 'web_upload' : 'gallery');
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Misslyckades: $e')));
    }
  }
}

Future<void> _uploadBytes(BuildContext context, WidgetRef ref, Uint8List bytes, String filename, {required String source}) async {
  final api = ref.read(ingestApiProvider);
  try {
    final uploaded = await api.uploadDocument(bytes: bytes, filename: filename, meta: {'source': source});
    await api.processOcr(uploaded.documentId);
    // Add to recent list immediately for visibility
    ref.read(recentDocumentsProvider.notifier).add(
          DocumentSummary(id: uploaded.documentId, uploadedAt: DateTime.now(), status: DocumentStatus.newDoc),
        );
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Klart! Dokument uppladdat.')));
      context.go('/documents/${uploaded.documentId}');
    }
  } catch (e) {
    // Offline fallback: enqueue job for later upload (non-web only)
    if (kIsWeb) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Offline-läge stöds inte i webbläsaren. Försök igen.')));
      }
      return;
    }
    final svc = await QueueService.create();
    await svc.enqueueUpload(filename: filename, bytes: bytes, meta: {'source': source});
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Offline: tillagd i uppladdningskön')));
      context.go('/upload-queue');
    }
  }
}

// DropOverlay removed while we ensure version compatibility of the dropzone plugin.
class _DropZone extends StatefulWidget {
  const _DropZone({required this.onFiles});
  final Future<void> Function(List<HtmlFile> files) onFiles;
  @override
  State<_DropZone> createState() => _DropZoneState();
}

  // typedef HtmlFile = DropzoneFile; // disabled until plugin alignment
  typedef HtmlFile = dynamic; // allow calls in demo without plugin

class _DropZoneState extends State<_DropZone> {
  bool _highlight = false;
  @override
  Widget build(BuildContext context) {
    return Stack(children: [
      // DropzoneView(
      //   onCreated: (c) => _ctrl = c,
      //   onDropMultiple: (files) async => widget.onFiles(files),
      //   onHover: () => setState(() => _highlight = true),
      //   onLeave: () => setState(() => _highlight = false),
      // ),
      AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        decoration: BoxDecoration(
          border: Border.all(color: _highlight ? Colors.blue : Colors.transparent, width: 2),
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Center(child: Text('Dra & släpp filer här')),
      )
    ]);
  }
}


