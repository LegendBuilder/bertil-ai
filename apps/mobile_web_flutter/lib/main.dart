import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/app.dart';
import 'shared/services/outbox_replay.dart';

void main() {
  OutboxReplayer().start();
  runApp(const ProviderScope(child: BertilApp()));
}


