import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class OutboxItem {
  OutboxItem({required this.id, required this.method, required this.url, required this.body, required this.headers});
  final String id;
  final String method;
  final String url;
  final Map<String, dynamic>? body;
  final Map<String, String>? headers;

  Map<String, dynamic> toJson() => {
        'id': id,
        'method': method,
        'url': url,
        'body': body,
        'headers': headers,
      };

  static OutboxItem fromJson(Map<String, dynamic> m) => OutboxItem(
        id: m['id'] as String,
        method: m['method'] as String,
        url: m['url'] as String,
        body: (m['body'] as Map?)?.cast<String, dynamic>(),
        headers: (m['headers'] as Map?)?.cast<String, String>(),
      );
}

class OutboxService {
  static const _key = 'outbox_items_v1';
  static final OutboxService _instance = OutboxService._internal();
  factory OutboxService() => _instance;
  OutboxService._internal();

  Future<void> enqueue(OutboxItem item) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_key) ?? <String>[];
    list.add(jsonEncode(item.toJson()));
    await prefs.setStringList(_key, list);
  }

  Future<List<OutboxItem>> list() async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_key) ?? <String>[];
    return list.map((s) => OutboxItem.fromJson(jsonDecode(s) as Map<String, dynamic>)).toList();
  }

  Future<void> removeById(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_key) ?? <String>[];
    final next = list.where((s) {
      final m = jsonDecode(s) as Map<String, dynamic>;
      return (m['id'] as String) != id;
    }).toList();
    await prefs.setStringList(_key, next);
  }
}


