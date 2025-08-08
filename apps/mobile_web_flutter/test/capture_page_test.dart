import 'package:bertil_mobile_web_flutter/features/ingest/provider/ingest_providers.dart';
import 'package:bertil_mobile_web_flutter/features/ingest/ui/capture_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeUploadController extends UploadController {
  _FakeUploadController() : super((throw UnimplementedError()));

  @override
  Future<void> uploadBytes(_, __, {required Map<String, dynamic> meta}) async {}
}

void main() {
  testWidgets('CapturePage shows buttons', (tester) async {
    await tester.pumpWidget(ProviderScope(
      overrides: [
        uploadControllerProvider.overrideWith((ref) => _FakeUploadController()),
      ],
      child: const MaterialApp(home: CapturePage()),
    ));
    expect(find.text('Fota kvitto'), findsOneWidget);
    expect(find.text('Välj bild från galleri'), findsOneWidget);
  });
}


