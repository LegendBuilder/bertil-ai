import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'outbox_storage.dart';

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

  final _storage = OutboxStorage();

  Future<void> enqueue(OutboxItem item) => _storage.enqueue(item);

  Future<List<OutboxItem>> list() => _storage.list();

  Future<void> removeById(String id) => _storage.removeById(id);
}


