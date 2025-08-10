import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/services.dart';
import '../../../shared/widgets/shortcut_help_overlay.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../bank/data/bank_api.dart';

class ReconcilePage extends ConsumerStatefulWidget {
  const ReconcilePage({super.key});
  @override
  ConsumerState<ReconcilePage> createState() => _ReconcilePageState();
}

class _ReconcilePageState extends ConsumerState<ReconcilePage> {
  final Set<int> _selectedTxIds = <int>{};
  String _query = '';
  final TextEditingController _dateFrom = TextEditingController();
  final TextEditingController _dateTo = TextEditingController();
  final TextEditingController _amountMin = TextEditingController();
  final TextEditingController _amountMax = TextEditingController();
  final FocusNode _searchFocus = FocusNode(debugLabel: 'bank_search');

  @override
  void initState() {
    super.initState();
    _loadFilters();
  }

  Future<void> _loadFilters() async {
    final sp = await SharedPreferences.getInstance();
    setState(() {
      _query = sp.getString('bank_q') ?? '';
      _dateFrom.text = sp.getString('bank_df') ?? '';
      _dateTo.text = sp.getString('bank_dt') ?? '';
      _amountMin.text = sp.getString('bank_am') ?? '';
      _amountMax.text = sp.getString('bank_aM') ?? '';
    });
  }

  Future<void> _saveFilters() async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString('bank_q', _query);
    await sp.setString('bank_df', _dateFrom.text);
    await sp.setString('bank_dt', _dateTo.text);
    await sp.setString('bank_am', _amountMin.text);
    await sp.setString('bank_aM', _amountMax.text);
  }

  @override
  Widget build(BuildContext context) {
    final api = ref.watch(bankApiProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Stäm av konto'),
        actions: [
          IconButton(
            tooltip: 'Uppdatera',
            onPressed: () => setState(() {}),
            icon: const Icon(Icons.refresh),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(children: [
              Expanded(
                child: TextField(
                  focusNode: _searchFocus,
                  decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Sök text eller motpart…', isDense: true, border: OutlineInputBorder()),
                  onChanged: (v) async {
                    setState(() => _query = v.trim());
                    await _saveFilters();
                  },
                ),
              ),
              const SizedBox(width: 8),
              Tooltip(
                message: 'Datum från',
                child: SizedBox(width: 140, child: TextField(controller: _dateFrom, decoration: const InputDecoration(isDense: true, hintText: 'Från YYYY-MM-DD', border: OutlineInputBorder()), onChanged: (_) => _saveFilters())),
              ),
              const SizedBox(width: 8),
              Tooltip(
                message: 'Datum till',
                child: SizedBox(width: 140, child: TextField(controller: _dateTo, decoration: const InputDecoration(isDense: true, hintText: 'Till YYYY-MM-DD', border: OutlineInputBorder()), onChanged: (_) => _saveFilters())),
              ),
              const SizedBox(width: 8),
              Tooltip(
                message: 'Belopp min',
                child: SizedBox(width: 120, child: TextField(controller: _amountMin, keyboardType: TextInputType.number, decoration: const InputDecoration(isDense: true, hintText: 'Min', border: OutlineInputBorder()), onChanged: (_) => _saveFilters())),
              ),
              const SizedBox(width: 8),
              Tooltip(
                message: 'Belopp max',
                child: SizedBox(width: 120, child: TextField(controller: _amountMax, keyboardType: TextInputType.number, decoration: const InputDecoration(isDense: true, hintText: 'Max', border: OutlineInputBorder()), onChanged: (_) => _saveFilters())),
              ),
              const SizedBox(width: 8),
              Tooltip(
                message: 'Bulk acceptera valda (om förslag finns)',
                child: FilledButton.icon(
                  onPressed: _selectedTxIds.isEmpty
                      ? null
                      : () async {
                          final items = <Map<String, int>>[];
                          for (final txId in _selectedTxIds) {
                            final sugg = await api.suggestFor(txId);
                            if (sugg.isNotEmpty) {
                              items.add({"tx_id": txId, "verification_id": sugg.first.verificationId});
                            }
                          }
                          if (items.isNotEmpty) {
                            await api.bulkAccept(items);
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Accepterade ${items.length} transaktioner')));
                            }
                            setState(() => _selectedTxIds.clear());
                          }
                        },
                  icon: const Icon(Icons.done_all),
                  label: Text('Acceptera (${_selectedTxIds.length})'),
                ),
              ),
            ]),
          ),
        ),
      ),
      body: Shortcuts(
        shortcuts: <LogicalKeySet, Intent>{
          LogicalKeySet(LogicalKeyboardKey.slash): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.keyA): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.keyR): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.shift, LogicalKeyboardKey.slash): const ActivateIntent(),
        },
        child: Actions(
          actions: <Type, Action<Intent>>{
            ActivateIntent: CallbackAction<ActivateIntent>(onInvoke: (intent) {
              final keys = RawKeyboard.instance.keysPressed;
              if (keys.contains(LogicalKeyboardKey.slash)) {
                _searchFocus.requestFocus();
              } else if (keys.contains(LogicalKeyboardKey.keyA)) {
                // Trigger bulk accept
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Tryck på knappen Acceptera för att köra')));
              } else if (keys.contains(LogicalKeyboardKey.keyR)) {
                setState(() {});
              } else if (keys.contains(LogicalKeyboardKey.slash) && keys.contains(LogicalKeyboardKey.shift)) {
                // Shortcut overlay
                ShortcutHelpOverlay.show(context, const [
                  MapEntry('/', 'Fokus i sökfältet'),
                  MapEntry('A', 'Acceptera markerade (via knappen)'),
                  MapEntry('R', 'Uppdatera listan'),
                  MapEntry('Tab/Shift+Tab', 'Navigera i filter och lista'),
                  MapEntry('?', 'Visa denna hjälp'),
                ], title: 'Bank – kortkommandon');
              }
              return null;
            }),
          },
          child: Focus(
            autofocus: true,
            child: FutureBuilder<List<BankTxItem>>(
              future: api.listUnmatched(
                q: _query.isEmpty ? null : _query,
                dateFrom: _dateFrom.text.isEmpty ? null : _dateFrom.text,
                dateTo: _dateTo.text.isEmpty ? null : _dateTo.text,
                amountMin: double.tryParse(_amountMin.text),
                amountMax: double.tryParse(_amountMax.text),
              ),
              builder: (context, snap) {
                if (!snap.hasData) return const Center(child: CircularProgressIndicator());
                var items = snap.data!;
                if (_query.isNotEmpty) {
                  final q = _query.toLowerCase();
                  items = items
                      .where((e) => e.description.toLowerCase().contains(q) || (e.counterparty ?? '').toLowerCase().contains(q))
                      .toList();
                }
                if (items.isEmpty) return const Center(child: Text('Inget att stämma av'));
                return ListView.separated(
                  itemCount: items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final tx = items[i];
                    final sel = _selectedTxIds.contains(tx.id);
                    return ExpansionTile(
                      title: Row(children: [
                        Checkbox(value: sel, onChanged: (v) => setState(() => v == true ? _selectedTxIds.add(tx.id) : _selectedTxIds.remove(tx.id))),
                        Expanded(
                          child: Semantics(
                            label: 'Transaktion ${tx.date} belopp ${tx.amount.toStringAsFixed(2)} ${tx.currency}',
                            child: Text('${tx.date}  ${tx.amount.toStringAsFixed(2)} ${tx.currency}'),
                          ),
                        ),
                      ]),
                      subtitle: Text(tx.description),
                      children: [
                        FutureBuilder<List<SuggestionItem>>(
                          future: api.suggestFor(tx.id),
                          builder: (context, s) {
                            if (!s.hasData) return const LinearProgressIndicator();
                            final sugg = s.data!;
                            if (sugg.isEmpty) return const ListTile(title: Text('Inga förslag'));
                            return Column(
                              children: sugg
                                  .map((sg) => ListTile(
                                        title: Semantics(label: 'Förslag V${sg.immutableSeq} belopp ${sg.total.toStringAsFixed(2)}', child: Text('V${sg.immutableSeq} · ${sg.total.toStringAsFixed(2)}')),
                                        subtitle: Text('${sg.date}  ${sg.counterparty ?? ''}  score ${(sg.score * 100).toStringAsFixed(0)}%'),
                                        trailing: Wrap(spacing: 8, children: [
                                          ElevatedButton(
                                            onPressed: () async {
                                              await api.accept(tx.id, sg.verificationId);
                                              if (context.mounted) {
                                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Matchad')));
                                              }
                                            },
                                            child: const Text('Acceptera'),
                                          ),
                                          OutlinedButton(
                                            onPressed: () async {
                                              await api.settle(tx.id, sg.verificationId);
                                              if (context.mounted) {
                                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Avräknad')));
                                              }
                                            },
                                            child: const Text('Avräkna'),
                                          ),
                                        ]),
                                      ))
                                  .toList(),
                            );
                          },
                        )
                      ],
                    );
                  },
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}


