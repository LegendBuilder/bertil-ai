import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../data/bankid_api.dart';
import '../../../shared/services/network.dart';

class AuthState {
  const AuthState({this.isLoading = false, this.isAuthenticated = false, this.message, this.user});
  final bool isLoading;
  final bool isAuthenticated;
  final String? message;
  final Map<String, dynamic>? user;

  AuthState copyWith({bool? isLoading, bool? isAuthenticated, String? message, Map<String, dynamic>? user}) => AuthState(
        isLoading: isLoading ?? this.isLoading,
        isAuthenticated: isAuthenticated ?? this.isAuthenticated,
        message: message ?? this.message,
        user: user ?? this.user,
      );
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._api) : super(const AuthState());
  final BankIdApi _api;
  Timer? _pollTimer;

  Future<void> startBankId() async {
    state = state.copyWith(isLoading: true, message: 'Startar BankID...');
    final init = await _api.init();
    // Try launch BankID app via autostart token (web will no-op)
    final uri = Uri.parse('bankid:///?autostarttoken=${init.autoStartToken}&redirect=null');
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
    } catch (_) {}
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (t) async {
      final s = await _api.status(init.orderRef);
      if (s.status == 'complete') {
        t.cancel();
        // Accept optional token if backend provides it
        final token = (s as dynamic).token as String?; // ignore: avoid_dynamic_calls
        NetworkService.setAuthToken(token);
        state = state.copyWith(isLoading: false, isAuthenticated: true, message: 'Inloggad', user: s.user);
      } else {
        state = state.copyWith(isLoading: true, message: 'Väntar på BankID...');
      }
    });
  }

  void loginDemo() {
    final user = {'subject': 'DEMO-USER', 'name': 'Demo Användare'};
    NetworkService.setAuthToken('demo-token');
    state = state.copyWith(isLoading: false, isAuthenticated: true, message: 'Inloggad (demo)', user: user);
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  final api = ref.watch(bankIdApiProvider);
  return AuthController(api);
});


