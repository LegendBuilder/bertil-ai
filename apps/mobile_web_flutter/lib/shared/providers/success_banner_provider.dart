import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SuccessBannerController extends StateNotifier<String?> {
  SuccessBannerController() : super(null);
  Timer? _timer;

  void show(String message, {Duration duration = const Duration(seconds: 3)}) {
    state = message;
    _timer?.cancel();
    _timer = Timer(duration, () => hide());
  }

  void hide() {
    state = null;
  }
}

final successBannerProvider =
    StateNotifierProvider<SuccessBannerController, String?>(
  (ref) => SuccessBannerController(),
);















