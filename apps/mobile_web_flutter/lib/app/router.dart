import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/ledger/ui/dashboard_page.dart';
import '../features/ingest/ui/capture_page.dart';
import '../features/documents/ui/documents_page.dart';
import '../features/reports/ui/reports_page.dart';
import '../features/reports/ui/closing_checklist_page.dart';
import '../features/settings/ui/settings_page.dart';
import '../features/settings/ui/outbox_management_page.dart';
import 'app_shell.dart';
import '../features/auth/ui/login_page.dart';
import '../features/auth/provider/auth_providers.dart';
import '../features/documents/ui/document_detail_page.dart';
import '../features/ingest/ui/upload_queue_page.dart';
import '../features/ledger/ui/verification_view.dart';
import '../features/ledger/ui/create_verification_page.dart';
import '../features/bank/ui/reconcile_page.dart';
import '../features/inbox/ui/inbox_page.dart';
import '../features/personal_tax/ui/personal_tax_dashboard.dart';
import '../features/personal_tax/ui/enhanced_capture_page.dart';
import '../features/invoices/ui/invoices_page.dart';
import '../features/invoices/ui/create_invoice_page.dart';
import '../features/invoices/ui/invoice_detail_page.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authControllerProvider);
  final isLoggedIn = auth.isAuthenticated;
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final loggingIn = state.uri.path == '/login';
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
          GoRoute(path: '/reports/closing', builder: (context, state) => const ClosingChecklistPage()),
          GoRoute(path: '/verifications', builder: (context, state) => const VerificationListPage()),
          GoRoute(path: '/verifications/create', builder: (context, state) => const CreateVerificationPage()),
          GoRoute(path: '/bank/reconcile', builder: (context, state) => const ReconcilePage()),
          GoRoute(path: '/inbox', builder: (context, state) => const InboxPage()),
          GoRoute(path: '/invoices', builder: (context, state) => const InvoicesPage()),
          GoRoute(path: '/invoices/create', builder: (context, state) => const CreateInvoicePage()),
          GoRoute(
            path: '/invoices/:id',
            builder: (context, state) => InvoiceDetailPage(invoiceId: int.parse(state.pathParameters['id']!)),
          ),
          GoRoute(path: '/personal-tax', builder: (context, state) => const PersonalTaxDashboard()),
          GoRoute(path: '/enhanced-capture', builder: (context, state) => const EnhancedCapturePage()),
          GoRoute(path: '/settings', builder: (context, state) => const SettingsPage()),
          GoRoute(path: '/settings/outbox', builder: (context, state) => const OutboxManagementPage()),
        ],
      ),
    ],
  );
});




