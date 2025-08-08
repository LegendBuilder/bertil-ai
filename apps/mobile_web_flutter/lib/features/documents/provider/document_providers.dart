import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/documents_api.dart';

final documentDetailProvider = FutureProvider.family((ref, String id) async {
  final api = ref.watch(documentsApiProvider);
  return api.getDocument(id);
});


