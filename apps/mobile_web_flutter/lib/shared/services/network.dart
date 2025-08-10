import 'dart:async';

import 'package:dio/dio.dart';

class NetworkService {
  NetworkService._internal();
  static final NetworkService _instance = NetworkService._internal();
  factory NetworkService() => _instance;

  final StreamController<NetworkIssue?> _errorController = StreamController<NetworkIssue?>.broadcast();
  Stream<NetworkIssue?> get errors => _errorController.stream;
  void clearError() => _errorController.add(null);

  late final Dio _dio = Dio(
    BaseOptions(
      baseUrl: _resolveBaseUrl(),
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      sendTimeout: const Duration(seconds: 20),
    ),
  )..interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        options.headers['Accept'] = 'application/json';
        final token = _authToken;
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (e, handler) async {
        final req = e.requestOptions;
        final method = req.method.toUpperCase();
        final retriable = method == 'GET' && _isRetriable(e);
        final attempt = (req.extra['retry'] as int?) ?? 0;
        if (retriable && attempt < 3) {
          final delays = [const Duration(milliseconds: 200), const Duration(milliseconds: 500), const Duration(milliseconds: 1000)];
          await Future.delayed(delays[attempt]);
          try {
            req.extra['retry'] = attempt + 1;
            final response = await _dio.fetch(req);
            return handler.resolve(response);
          } catch (_) {}
        }
        final issue = _toIssue(e);
        if (issue != null) {
          _errorController.add(issue);
        }
        return handler.next(e);
      },
    ));

  Dio get client => _dio;
  static String? _authToken;
  static void setAuthToken(String? token) {
    _authToken = token;
  }

  static String _resolveBaseUrl() {
    const envUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (envUrl.isNotEmpty) return envUrl;
    // Force IPv4 loopback to avoid ::1 vs 127.0.0.1 socket issues on Windows when server binds to 127.0.0.1
    return 'http://127.0.0.1:8000';
  }

  bool _isRetriable(DioException e) {
    if (e.type == DioExceptionType.connectionError || e.type == DioExceptionType.receiveTimeout || e.type == DioExceptionType.sendTimeout) {
      return true;
    }
    final status = e.response?.statusCode ?? 0;
    return status == 502 || status == 503 || status == 504;
  }

  NetworkIssue? _toIssue(DioException e) {
    final status = e.response?.statusCode;
    final isTimeout = e.type == DioExceptionType.receiveTimeout || e.type == DioExceptionType.sendTimeout;
    final isConn = e.type == DioExceptionType.connectionError;
    if (isConn || isTimeout || (status != null && status >= 500)) {
      final code = status ?? 0;
      final msg = isConn || isTimeout
          ? 'Server nere: Vi återställer nu. Dina kvitton är säkra.'
          : 'Serverfel ($code). Försök igen om en stund.';
      return NetworkIssue(message: msg, statusCode: code);
    }
    return null;
  }
}

class NetworkIssue {
  NetworkIssue({required this.message, required this.statusCode});
  final String message;
  final int statusCode;
}



