import 'package:bertil_mobile_web_flutter/features/ledger/data/ledger_api.dart';
import 'package:bertil_mobile_web_flutter/features/ledger/provider/ledger_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../provider/ledger_providers.dart';

class VerificationListPage extends ConsumerWidget {
  const VerificationListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncList = ref.watch(recentVerificationsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Verifikationer')),
      body: asyncList.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Kunde inte hÃ¤mta: $e')),
        data: (list) => ListView.separated(
          itemCount: list.length,
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemBuilder: (context, i) {
            final v = list[i];
            return ListTile(
              title: Text('V${v.immutableSeq} Â· ${v.totalAmount.toStringAsFixed(2)} ${v.currency}'),
              subtitle: Text(v.date),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => _VerificationDetailPage(id: v.id, immutableSeq: v.immutableSeq)),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _VerificationDetailPage extends ConsumerWidget {
  const _VerificationDetailPage({required this.id, required this.immutableSeq});
  final int id;
  final int immutableSeq;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.watch(ledgerApiProvider);
    return FutureBuilder<VerificationDetail>( future: api.getVerification(id),
      builder: (context, snap) {
        if (!snap.hasData) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        final VerificationDetail v = snap.data as VerificationDetail;
        return Scaffold(
          appBar: AppBar(title: Text('Verifikation V$immutableSeq')),
          body: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Datum: ${v.date}'),
                Text('Total: ${v.totalAmount.toStringAsFixed(2)} ${v.currency}'),
                if (v.documentLink != null && v.documentLink!.isNotEmpty)
                  Text('Underlag: ${v.documentLink}'),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(child: Text('Audit-hash: ${v.auditHash.isEmpty ? '(saknas)' : v.auditHash}')),
                    if (v.auditHash.isNotEmpty)
                      IconButton(
                        tooltip: 'Kopiera',
                        icon: const Icon(Icons.copy_all_outlined),
                        onPressed: () => Clipboard.setData(ClipboardData(text: v.auditHash)),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                if (v.explainability != null && v.explainability!.isNotEmpty) ...[
                  const Text('VarfÃ¶r valde vi detta?', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 6),
                  Text(v.explainability!),
                  const SizedBox(height: 12),
                ],
                FutureBuilder<List<Map<String, dynamic>>>( future: api.getVerificationFlags(id),
                  builder: (context, snapFlags) {
                    if (!snapFlags.hasData) return const SizedBox.shrink();
                    final List<Map<String, dynamic>> flags = (snapFlags.data as List).cast<Map<String, dynamic>>();
                    if (flags.isEmpty) return const SizedBox.shrink();
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Flaggor', style: TextStyle(fontWeight: FontWeight.w600)),
                        const SizedBox(height: 6),
                        Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          children: [
                            for (final f in flags)
                              Chip(
                                backgroundColor: (f['severity'] == 'error')
                                    ? Colors.red.shade100
                                    : (f['severity'] == 'warning')
                                        ? Colors.orange.shade100
                                        : Colors.green.shade100,
                                label: Text(f['message'] as String),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        if (flags.any((f) => (f['rule_code'] ?? '').toString().startsWith('R-PERIOD')))
                          OutlinedButton.icon(
                            onPressed: () async {
                              final today = DateTime.now();
                              final iso = '${today.year.toString().padLeft(4, '0')}-${today.month.toString().padLeft(2, '0')}-${today.day.toString().padLeft(2, '0')}'
                                  ;
                              await api.correctVerificationDate(id: id, newDateIso: iso);
                              if (context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Datum korrigerat via ombokning')));
                              }
                            },
                            icon: const Icon(Icons.event_available_outlined),
                            label: const Text('Ã…tgÃ¤rda: korrigera datum'),
                          ),
                        Row(children: [
                          if (v.documentLink != null && v.documentLink!.startsWith('/documents/'))
                            OutlinedButton.icon(
                              onPressed: () {
                                final docId = v.documentLink!.split('/documents/').last;
                                Navigator.of(context).pushNamed('/documents/$docId');
                              },
                              icon: const Icon(Icons.open_in_new),
                              label: const Text('Ã…tgÃ¤rda: Ã¶ppna underlag'),
                            )
                          else
                            OutlinedButton.icon(
                              onPressed: () async {
                                // Quick prompt for document id (basic UX for MVP)
                                final controller = TextEditingController();
                                final ok = await showDialog<bool>(
                                  context: context,
                                  builder: (context) => AlertDialog(
                                    title: const Text('Ange dokument-ID'),
                                    content: TextField(controller: controller, decoration: const InputDecoration(hintText: 'klistra in dokument-ID')),
                                    actions: [
                                      TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Avbryt')),
                                      ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Koppla')),
                                    ],
                                  ),
                                );
                                if (ok == true && controller.text.trim().isNotEmpty) {
                                  await api.correctVerificationDocument(id: id, documentId: controller.text.trim());
                                  if (context.mounted) {
                                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Underlag kopplat via ombokning')));
                                  }
                                }
                              },
                              icon: const Icon(Icons.link_outlined),
                              label: const Text('Koppla underlag'),
                            ),
                        ]),
                      ],
                    );
                  },
                ),
                const Text('Poster:'),
                const SizedBox(height: 8),
                Expanded(
                  child: ListView.separated(
                    itemCount: v.entries.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, i) {
                      final e = v.entries[i];
                      final debit = (e['debit'] as num).toDouble();
                      final credit = (e['credit'] as num).toDouble();
                      return ListTile(
                        title: Text('${e['account']} Â· D ${debit.toStringAsFixed(2)} / K ${credit.toStringAsFixed(2)}'),
                        subtitle: Text(e['dimension']?.toString() ?? ''),
                      );
                    },
                  ),
                ),
                const Spacer(),
                Row(
                  children: [
                    Expanded(child: const Text('Append-only: RÃ¤ttning sker med ombokning, aldrig direkt Ã¤ndring.')),
                    OutlinedButton.icon(
                      onPressed: () async {
                        await api.reverseVerification(id);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Ombokning skapad')));
                        }
                      },
                      icon: const Icon(Icons.undo_outlined),
                      label: const Text('Skapa ombokning'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}





