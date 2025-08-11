import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../../shared/services/network.dart';
import '../provider/inbox_providers.dart';
import '../../../shared/widgets/shortcut_help_overlay.dart';
import 'package:flutter/services.dart';
import '../../../shared/services/analytics.dart';

// Moved model and provider to provider/inbox_providers.dart

class InboxPage extends ConsumerStatefulWidget {
  const InboxPage({super.key});
  @override
  ConsumerState<InboxPage> createState() => _InboxPageState();
}

class _InboxPageState extends ConsumerState<InboxPage> {
  final Set<int> _selected = <int>{};
  @override
  Widget build(BuildContext context) {
    final tasks = ref.watch(inboxProvider);
    final dio = NetworkService().client;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Autopilot Inbox'),
        actions: [
          IconButton(
            tooltip: 'Kortkommandon',
            onPressed: () => ShortcutHelpOverlay.show(context, const [
              MapEntry('A', 'Godkänn markerade'),
              MapEntry('U', 'Ångra markerade'),
              MapEntry('Mellanslag', 'Markera/avmarkera rad'),
              MapEntry('Tab/Shift+Tab', 'Navigera i listan'),
              MapEntry('?', 'Visa denna hjälp'),
            ], title: 'Autopilot Inbox – kortkommandon'),
            icon: const Icon(Icons.help_outline),
          ),
        ],
      ),
      body: Shortcuts(
        shortcuts: <LogicalKeySet, Intent>{
          LogicalKeySet(LogicalKeyboardKey.keyA): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.keyU): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.shift, LogicalKeyboardKey.slash): const ActivateIntent(),
        },
        child: Actions(
          actions: <Type, Action<Intent>>{
            ActivateIntent: CallbackAction<ActivateIntent>(onInvoke: (intent) {
              final keys = RawKeyboard.instance.keysPressed;
              if (keys.contains(LogicalKeyboardKey.keyA)) {
                AnalyticsService.logEvent('inbox_bulk_approve');
                _bulkApprove(dio);
              } else if (keys.contains(LogicalKeyboardKey.keyU)) {
                AnalyticsService.logEvent('inbox_bulk_undo');
                _bulkUndo(dio);
              } else if (keys.contains(LogicalKeyboardKey.slash) && keys.contains(LogicalKeyboardKey.shift)) {
                ShortcutHelpOverlay.show(context, [
                  const MapEntry('A', 'Godkänn markerade'),
                  const MapEntry('U', 'Ångra markerade'),
                  const MapEntry('Mellanslag', 'Markera/avmarkera rad'),
                  const MapEntry('Tab/Shift+Tab', 'Navigera i listan'),
                  const MapEntry('?', 'Visa denna hjälp'),
                ], title: 'Autopilot Inbox – kortkommandon');
              }
              return null;
            }),
          },
          child: tasks.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, st) => Center(child: Text('Kunde inte hämta: $e')),
            data: (list) {
              if (list.isEmpty) return const Center(child: Text('Inget att granska'));
              return Column(children: [
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: Row(children: [
                    Semantics(
                      button: true,
                      label: 'Godkänn markerade rader. Kortkommando A',
                      child: Focus(
                        child: FilledButton.icon(
                          onPressed: _selected.isEmpty ? null : () => _bulkApprove(dio),
                          icon: const Icon(Icons.check),
                          label: const Text('Godkänn (A)'),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Semantics(
                      button: true,
                      label: 'Ångra markerade rader. Kortkommando U',
                      child: Focus(
                        child: OutlinedButton.icon(
                          onPressed: _selected.isEmpty ? null : () => _bulkUndo(dio),
                          icon: const Icon(Icons.undo),
                          label: const Text('Ångra (U)'),
                        ),
                      ),
                    ),
                    const Spacer(),
                    Tooltip(
                      message: 'Kortkommandon (?)',
                      child: IconButton(
                        onPressed: () => ShortcutHelpOverlay.show(context, [
                          const MapEntry('A', 'Godkänn markerade'),
                          const MapEntry('U', 'Ångra markerade'),
                          const MapEntry('Mellanslag', 'Markera/avmarkera rad'),
                          const MapEntry('Tab/Shift+Tab', 'Navigera i listan'),
                          const MapEntry('?', 'Visa denna hjälp'),
                        ], title: 'Autopilot Inbox – kortkommandon'),
                        icon: const Icon(Icons.help_outline),
                      ),
                    ),
                  ]),
                ),
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: () async { setState(() {}); },
                    child: ListView.separated(
                    itemCount: list.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, i) {
                      final it = list[i];
                      final sel = _selected.contains(it.id);
                      return Semantics(
                        container: true,
                        label: 'Rad ${i + 1} av ${list.length}: ${it.type}',
                        child: FocusTraversalOrder(
                          order: NumericFocusOrder(i.toDouble()),
                        child: ListTile(
                          leading: Checkbox(
                            value: sel,
                            onChanged: (v) => setState(() => v == true ? _selected.add(it.id) : _selected.remove(it.id)),
                            autofocus: i == 0,
                          ),
                          title: Text('${it.type} • ${(it.confidence * 100).toStringAsFixed(0)}%'),
                          subtitle: Text(_explain(it)),
                          onTap: () => setState(() => sel ? _selected.remove(it.id) : _selected.add(it.id)),
                        ),
                        ),
                      );
                    },
                    ),
                  ),
                )
              ]);
            },
          ),
        ),
      ),
    );
  }

  String _explain(ReviewTaskItem it) {
    final p = it.payload;
    switch (it.type) {
      case 'autopost':
        final vendor = p['vendor'] ?? p['counterparty'] ?? '';
        final total = p['total'] ?? p['amount'] ?? '';
        final account = p['account'] ?? p['expense_account'] ?? '';
        final vat = p['vat_code'] ?? p['vat_rate'] ?? '';
        return 'Föreslår bokföring: $vendor • $total • konto $account • moms $vat'.trim();
      case 'settle':
        final vid = p['verification_id'] ?? p['ref'] ?? '';
        final amt = p['amount'] ?? p['total'] ?? '';
        final bank = p['bank_tx_id'] ?? '';
        return 'Matcha bankhändelse $bank mot verifikation $vid • belopp $amt'.trim();
      case 'vat':
        final period = p['period'] ?? '';
        final net = p['net'] ?? '';
        final pay = p['to_pay'] ?? '';
        return 'Momsdeklaration $period: netto $net • att betala $pay'.trim();
      default:
        return p.toString();
    }
  }

  Future<void> _bulkApprove(Dio dio) async {
    for (final id in _selected.toList()) {
      await dio.post('/review/$id/complete');
    }
    if (mounted) setState(() => _selected.clear());
    ref.invalidate(inboxProvider);
  }

  Future<void> _bulkUndo(Dio dio) async {
    for (final id in _selected.toList()) {
      await dio.post('/review/$id/reopen');
    }
    if (mounted) setState(() => _selected.clear());
    ref.invalidate(inboxProvider);
  }
}





