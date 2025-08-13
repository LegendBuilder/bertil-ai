import 'dart:convert';
import 'dart:html' as html;

import 'outbox.dart';

class OutboxStorage {
  static const _key = 'outbox_items_v1';

  Future<void> enqueue(OutboxItem item) async {
    final list = html.window.localStorage[_key];
    final items = list == null || list.isEmpty ? <String>[] : (jsonDecode(list) as List).cast<String>();
    items.add(jsonEncode(item.toJson()));
    html.window.localStorage[_key] = jsonEncode(items);
  }

  Future<List<OutboxItem>> list() async {
    final list = html.window.localStorage[_key];
    final items = list == null || list.isEmpty ? <String>[] : (jsonDecode(list) as List).cast<String>();
    return items.map((s) => OutboxItem.fromJson(jsonDecode(s) as Map<String, dynamic>)).toList();
  }

  Future<void> removeById(String id) async {
    final list = html.window.localStorage[_key];
    final items = list == null || list.isEmpty ? <String>[] : (jsonDecode(list) as List).cast<String>();
    final next = items.where((s) => (jsonDecode(s) as Map<String, dynamic>)['id'] != id).toList();
    html.window.localStorage[_key] = jsonEncode(next);
  }
}


