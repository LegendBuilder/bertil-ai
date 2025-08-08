import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/ledger/ui/dashboard_page.dart';
import '../features/ingest/ui/capture_page.dart';
import '../features/documents/ui/documents_page.dart';
import '../features/reports/ui/reports_page.dart';
import '../features/settings/ui/settings_page.dart';
import 'app_shell.dart';
import '../features/auth/ui/login_page.dart';
import '../features/auth/provider/auth_providers.dart';
import '../features/documents/ui/document_detail_page.dart';
import '../features/ingest/ui/upload_queue_page.dart';
import '../features/ledger/ui/verification_view.dart';
import '../features/ledger/ui/create_verification_page.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authControllerProvider);
  final isLoggedIn = auth.isAuthenticated;
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final loggingIn = state.subloc == '/login';
      if (!isLoggedIn) {
        return loggingIn ? null : '/login';
      }
      if (loggingIn) return '/';
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginPage()),
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(path: '/', builder: (context, state) => const DashboardPage()),
          GoRoute(path: '/capture', builder: (context, state) => const CapturePage()),
          GoRoute(path: '/upload-queue', builder: (context, state) => const UploadQueuePage()),
          GoRoute(path: '/documents', builder: (context, state) => const DocumentsPage()),
          GoRoute(
            path: '/documents/:id',
            builder: (context, state) => DocumentDetailPage(id: state.pathParameters['id']!),
          ),
          GoRoute(path: '/reports', builder: (context, state) => const ReportsPage()),
          GoRoute(path: '/verifications', builder: (context, state) => const VerificationListPage()),
          GoRoute(path: '/verifications/create', builder: (context, state) => const CreateVerificationPage()),
          GoRoute(path: '/settings', builder: (context, state) => const SettingsPage()),
        ],
      ),
    ],
  );
});


