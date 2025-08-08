import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/ledger_api.dart';

class CreateVerificationPage extends ConsumerStatefulWidget {
  const CreateVerificationPage({super.key});
  @override
  ConsumerState<CreateVerificationPage> createState() => _CreateVerificationPageState();
}

class _CreateVerificationPageState extends ConsumerState<CreateVerificationPage> {
  final _formKey = GlobalKey<FormState>();
  final _dateCtrl = TextEditingController(text: DateTime.now().toIso8601String().split('T').first);
  final _totalCtrl = TextEditingController(text: '0.00');
  final List<_EntryRow> _rows = [
    _EntryRow(account: '1910', debit: 0.0, credit: 0.0),
    _EntryRow(account: '3001', debit: 0.0, credit: 0.0),
  ];

  @override
  void dispose() {
    _dateCtrl.dispose();
    _totalCtrl.dispose();
    super.dispose();
  }

  double get _sumDebit => _rows.fold(0.0, (p, r) => p + (r.debit ?? 0));
  double get _sumCredit => _rows.fold(0.0, (p, r) => p + (r.credit ?? 0));

  @override
  Widget build(BuildContext context) {
    final api = ref.watch(ledgerApiProvider);
    final balanced = (_sumDebit - _sumCredit).abs() < 0.01;
    return Scaffold(
      appBar: AppBar(title: const Text('Skapa verifikation')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(
                controller: _dateCtrl,
                decoration: const InputDecoration(labelText: 'Datum (YYYY-MM-DD)'),
                validator: (v) => (v == null || v.isEmpty) ? 'Obligatoriskt' : null,
              ),
              TextFormField(
                controller: _totalCtrl,
                decoration: const InputDecoration(labelText: 'Totalbelopp'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
              const SizedBox(height: 12),
              const Text('Poster'),
              const SizedBox(height: 8),
              Expanded(
                child: ListView.builder(
                  itemCount: _rows.length,
                  itemBuilder: (context, i) {
                    final row = _rows[i];
                    return Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: TextFormField(
                            initialValue: row.account,
                            decoration: const InputDecoration(labelText: 'Konto'),
                            onChanged: (v) => row.account = v,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextFormField(
                            initialValue: (row.debit ?? 0).toStringAsFixed(2),
                            decoration: const InputDecoration(labelText: 'Debet'),
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            onChanged: (v) => row.debit = double.tryParse(v) ?? 0.0,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextFormField(
                            initialValue: (row.credit ?? 0).toStringAsFixed(2),
                            decoration: const InputDecoration(labelText: 'Kredit'),
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            onChanged: (v) => row.credit = double.tryParse(v) ?? 0.0,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete_outline),
                          onPressed: () => setState(() => _rows.removeAt(i)),
                        )
                      ],
                    );
                  },
                ),
              ),
              Row(
                children: [
                  OutlinedButton.icon(
                    onPressed: () => setState(() => _rows.add(_EntryRow(account: '', debit: 0.0, credit: 0.0))),
                    icon: const Icon(Icons.add),
                    label: const Text('Lägg till rad'),
                  ),
                  const SizedBox(width: 16),
                  Chip(label: Text('Sum D ${_sumDebit.toStringAsFixed(2)} / K ${_sumCredit.toStringAsFixed(2)}'), backgroundColor: balanced ? Colors.green.shade100 : Colors.orange.shade100),
                ],
              ),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: !balanced
                    ? null
                    : () async {
                        if (!_formKey.currentState!.validate()) return;
                        final id = await api.createVerification(
                          orgId: 1,
                          dateIso: _dateCtrl.text,
                          totalAmount: double.tryParse(_totalCtrl.text) ?? 0.0,
                          entries: _rows
                              .map((r) => {
                                    'account': r.account,
                                    'debit': r.debit,
                                    'credit': r.credit,
                                  })
                              .toList(),
                        );
                        if (!mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Skapade verifikation #$id')));
                        Navigator.of(context).pop();
                      },
                child: const Text('Skapa verifikation'),
              )
            ],
          ),
        ),
      ),
    );
  }
}

class _EntryRow {
  _EntryRow({required this.account, this.debit, this.credit});
  String account;
  double? debit;
  double? credit;
}


