import 'dart:convert';

import 'package:isar/isar.dart';
import 'package:path_provider/path_provider.dart';

import 'outbox.dart';

part 'outbox_storage_io.g.dart';

@collection
class OutboxEntity {
  Id id = Isar.autoIncrement;
  late String itemId;
  late String json;
}

class OutboxStorage {
  static Isar? _isar;

  Future<Isar> _db() async {
    if (_isar != null) return _isar!;
    final dir = await getApplicationDocumentsDirectory();
    _isar = await Isar.open([OutboxEntitySchema], directory: dir.path);
    return _isar!;
  }

  Future<void> enqueue(OutboxItem item) async {
    final isar = await _db();
    await isar.writeTxn(() async {
      final e = OutboxEntity()
        ..itemId = item.id
        ..json = jsonEncode(item.toJson());
      await isar.outboxEntitys.put(e);
    });
  }

  Future<List<OutboxItem>> list() async {
    final isar = await _db();
    final rows = await isar.outboxEntitys.where().findAll();
    return rows.map((e) => OutboxItem.fromJson(jsonDecode(e.json) as Map<String, dynamic>)).toList();
  }

  Future<void> removeById(String id) async {
    final isar = await _db();
    final rows = await isar.outboxEntitys.where().filter().itemIdEqualTo(id).findAll();
    await isar.writeTxn(() async {
      for (final r in rows) {
        await isar.outboxEntitys.delete(r.id);
      }
    });
  }
}


