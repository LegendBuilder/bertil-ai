import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/closing_api.dart';

class ClosingChecklistPage extends ConsumerStatefulWidget {
  const ClosingChecklistPage({super.key});
  @override
  ConsumerState<ClosingChecklistPage> createState() => _ClosingChecklistPageState();
}

class _ClosingChecklistPageState extends ConsumerState<ClosingChecklistPage> {
  String _start = '';
  String _end = '';
  bool _busy = false;
  @override
  Widget build(BuildContext context) {
    final api = ref.watch(closingApiProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Periodstängning')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Checklista'),
          const SizedBox(height: 8),
          const _ChecklistItem(text: 'Alla verifikationer bokförda'),
          const _ChecklistItem(text: 'Banken avstämd'),
          const _ChecklistItem(text: 'Moms deklarerad'),
          const _ChecklistItem(text: 'Periodiseringar genomförda'),
          const SizedBox(height: 16),
          const Text('Lås period'),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(
              child: TextField(
                decoration: const InputDecoration(labelText: 'Startdatum (YYYY-MM-DD)')
              , onChanged: (v) => setState(() => _start = v.trim()),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                decoration: const InputDecoration(labelText: 'Slutdatum (YYYY-MM-DD)'),
                onChanged: (v) => setState(() => _end = v.trim()),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: _busy || _start.isEmpty || _end.isEmpty
                  ? null
                  : () async {
                      setState(() => _busy = true);
                      try {
                        await api.closePeriod(startDate: _start, endDate: _end);
                        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Period låst')));
                      } finally {
                        setState(() => _busy = false);
                      }
                    },
              child: const Text('Lås'),
            )
          ]),
          const SizedBox(height: 16),
          const Text('Låsta perioder'),
          const SizedBox(height: 8),
          Expanded(
            child: FutureBuilder<List<Map<String, String>>>(
              future: api.getStatus(),
              builder: (context, snap) {
                if (!snap.hasData) return const LinearProgressIndicator();
                final items = snap.data!;
                if (items.isEmpty) return const Text('Inga låsta perioder');
                return ListView.separated(
                  itemCount: items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, i) {
                    final it = items[i];
                    return ListTile(title: Text('${it['start_date']} → ${it['end_date']}'));
                  },
                );
              },
            ),
          ),
        ]),
      ),
    );
  }
}

class _ChecklistItem extends StatelessWidget {
  const _ChecklistItem({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) {
    return Row(children: [
      const Icon(Icons.check_circle_outline, color: Colors.green),
      const SizedBox(width: 8),
      Text(text),
    ]);
  }
}





