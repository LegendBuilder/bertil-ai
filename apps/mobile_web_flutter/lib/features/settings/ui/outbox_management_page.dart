import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/services/outbox.dart';

class OutboxManagementPage extends ConsumerStatefulWidget {
  const OutboxManagementPage({super.key});

  @override
  ConsumerState<OutboxManagementPage> createState() => _OutboxManagementPageState();
}

class _OutboxManagementPageState extends ConsumerState<OutboxManagementPage> {
  Future<List<OutboxItem>>? _future;

  @override
  void initState() {
    super.initState();
    _future = OutboxService().list();
  }

  Future<void> _reload() async {
    setState(() => _future = OutboxService().list());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Utkorg (offline)')),
      body: FutureBuilder<List<OutboxItem>>(
        future: _future,
        builder: (context, snap) {
          final items = snap.data ?? [];
          if (items.isEmpty) return const Center(child: Text('Inget i utkorgen'));
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, i) {
              final it = items[i];
              return ListTile(
                title: Text('${it.method} ${it.url}'),
                subtitle: Text(jsonEncode(it.body ?? {}), maxLines: 2, overflow: TextOverflow.ellipsis),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.refresh),
                      onPressed: () async {
                        // naive retry: rely on periodic replayer, just restart
                        try { await OutboxService().enqueue(it); } catch (_) {}
                        await OutboxService().removeById(it.id);
                        await _reload();
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete),
                      onPressed: () async {
                        await OutboxService().removeById(it.id);
                        await _reload();
                      },
                    ),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}


