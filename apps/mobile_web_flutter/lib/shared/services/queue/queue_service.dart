import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:isar/isar.dart';
import 'package:path_provider/path_provider.dart';

import '../../services/network.dart';
import '../../utils/crypto.dart';
import '../../../features/ingest/data/ingest_api.dart';
import 'queue_models.dart';

class QueueService {
  QueueService(this._isar, this._api);
  final Isar _isar;
  final IngestApi _api;

  static Future<QueueService> create() async {
    final dir = await getApplicationSupportDirectory();
    final isar = await Isar.open([UploadJobSchema], directory: dir.path);
    return QueueService(isar, IngestApi(NetworkService().client));
  }

  Future<Id> enqueueUpload({required String filename, required Uint8List bytes, required Map<String, dynamic> meta}) async {
    final job = UploadJob()
      ..filename = filename
      ..bytes = bytes
      ..metaJson = jsonEncode(meta)
      ..status = 'pending'
      ..retryCount = 0;
    return _isar.writeTxn(() => _isar.uploadJobs.put(job));
  }

  Future<void> processQueue({int maxRetries = 5}) async {
    final jobs = await _isar.uploadJobs.filter().statusEqualTo('pending').findAll();
    for (final job in jobs) {
      await _isar.writeTxn(() async {
        job.status = 'processing';
        await _isar.uploadJobs.put(job);
      });
      try {
        final meta = jsonDecode(job.metaJson) as Map<String, dynamic>;
        final resp = await _api.uploadDocument(bytes: Uint8List.fromList(job.bytes), filename: job.filename, meta: meta);
        await _isar.writeTxn(() async {
          job.status = 'done';
          await _isar.uploadJobs.put(job);
        });
      } catch (e) {
        await _isar.writeTxn(() async {
          job.retryCount += 1;
          job.status = job.retryCount >= maxRetries ? 'error' : 'pending';
          job.errorMessage = e.toString();
          await _isar.uploadJobs.put(job);
        });
      }
    }
  }

  Stream<int> watchPendingCount() {
    return _isar.uploadJobs.filter().statusEqualTo('pending').watchLazy().asyncMap((_) async {
      return _isar.uploadJobs.filter().statusEqualTo('pending').count();
    });
  }
}

final queueServiceProvider = FutureProvider<QueueService>((ref) async => QueueService.create());


