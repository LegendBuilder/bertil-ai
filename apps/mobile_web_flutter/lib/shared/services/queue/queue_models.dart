import 'package:isar/isar.dart';

part 'queue_models.g.dart';

@collection
class UploadJob {
  Id id = Isar.autoIncrement;
  late String filename;
  late List<int> bytes;
  late String metaJson;
  late String status; // pending, processing, done, error
  String? errorMessage;
  DateTime createdAt = DateTime.now();
  int retryCount = 0;
}


