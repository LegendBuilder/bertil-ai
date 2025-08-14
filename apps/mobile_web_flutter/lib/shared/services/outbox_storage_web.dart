import 'dart:convert';
import 'package:idb_shim/idb_browser.dart';
import 'package:idb_shim/idb.dart';

import 'outbox.dart';

class OutboxStorage {
  static const _dbName = 'bertil_outbox_db';
  static const _store = 'outbox';
  Database? _db;

  Future<Database> _open() async {
    if (_db != null) return _db!;
    final factory = getIdbFactory()!;
    _db = await factory.open(_dbName, version: 1, onUpgradeNeeded: (e) {
      final db = e.database;
      if (!db.objectStoreNames.contains(_store)) {
        db.createObjectStore(_store, autoIncrement: true, keyPath: 'key');
      }
    });
    return _db!;
  }

  Future<void> enqueue(OutboxItem item) async {
    final db = await _open();
    final txn = db.transaction(_store, idbModeReadWrite);
    final store = txn.objectStore(_store);
    await store.put({
      'id': item.id,
      'json': jsonEncode(item.toJson()),
    });
    await txn.completed;
  }

  Future<List<OutboxItem>> list() async {
    final db = await _open();
    final txn = db.transaction(_store, idbModeReadOnly);
    final store = txn.objectStore(_store);
    final values = await store.getAll(null);
    await txn.completed;
    return values
        .map((v) => (v as Map).cast<String, Object?>())
        .map((m) => OutboxItem.fromJson(jsonDecode(m['json'] as String) as Map<String, dynamic>))
        .toList();
  }

  Future<void> removeById(String id) async {
    final db = await _open();
    final txn = db.transaction(_store, idbModeReadWrite);
    final store = txn.objectStore(_store);
    final cursors = await store.openCursor(autoAdvance: false);
    await for (final c in cursors) {
      final m = (c.value as Map).cast<String, Object?>();
      final data = jsonDecode(m['json'] as String) as Map<String, dynamic>;
      if (data['id'] == id) {
        await c.delete();
        break;
      }
      c.next();
    }
    await txn.completed;
  }
}


