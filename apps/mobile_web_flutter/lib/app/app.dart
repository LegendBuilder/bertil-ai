import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'router.dart';
import 'theme.dart';
import '../shared/services/network.dart';
import '../shared/providers/success_banner_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../shared/providers/coachmarks_provider.dart';

class BertilApp extends ConsumerStatefulWidget {
  const BertilApp({super.key});

  @override
  ConsumerState<BertilApp> createState() => _BertilAppState();
}

class _BertilAppState extends ConsumerState<BertilApp> {
  String? _lastShownIssue;

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'Bertil',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      routerConfig: router,
      builder: (context, child) {
        return Stack(
          children: [
            Semantics(
              label: 'Bertil huvudapp',
              explicitChildNodes: true,
              child: child ?? const SizedBox.shrink(),
            ),
            // First-run coachmarks (very light): show only once
            Consumer(builder: (context, ref, _) {
              final visible = ref.watch(coachmarksVisibleProvider);
              if (!visible) return const SizedBox.shrink();
              return FutureBuilder<bool>(
                future: _shouldShowCoachmarks(),
                builder: (context, snap) {
                  if (snap.data != true) return const SizedBox.shrink();
                return Positioned.fill(
                  child: IgnorePointer(
                    ignoring: false,
                    child: Container(
                      color: Colors.black.withOpacity(0.4),
                      child: Center(
                        child: Card(
                          margin: const EdgeInsets.all(24),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Text('Välkommen! Så här kommer du igång:'),
                                const SizedBox(height: 8),
                                const Text('1) Logga in (eller testa demo)'),
                                const Text('2) Lägg till ett dokument (fota eller ladda upp)'),
                                const Text('3) Se “Bokfört ✅” – klart!'),
                                const SizedBox(height: 12),
                                FilledButton(
                                  onPressed: () async {
                                    final sp = await SharedPreferences.getInstance();
                                    await sp.setBool('coachmarks_seen', true);
                                      ref.read(coachmarksVisibleProvider.notifier).state = false;
                                  },
                                  child: const Text('Jag är med!'),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                );
                },
              );
            }),
            // Gentle success banner
            Positioned(
              top: 12,
              left: 12,
              right: 12,
              child: Consumer(builder: (context, ref, _) {
                final msg = ref.watch(successBannerProvider);
                if (msg == null) return const SizedBox.shrink();
                return Material(
                  elevation: 4,
                  borderRadius: BorderRadius.circular(10),
                  color: Theme.of(context).colorScheme.primary,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                    child: Row(
                      children: [
                        const Icon(Icons.check_circle_outline, color: Colors.white),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(msg, style: const TextStyle(color: Colors.white)),
                        ),
                        TextButton(
                          onPressed: () => ref.read(successBannerProvider.notifier).hide(),
                          child: const Text('Stäng', style: TextStyle(color: Colors.white)),
                        )
                      ],
                    ),
                  ),
                );
              }),
            ),
            // Global network issue snackbar (ephemeral, auto-dismiss)
            Consumer(builder: (context, ref, _) {
              return StreamBuilder<NetworkIssue?>(
                stream: NetworkService().errors,
                builder: (context, snap) {
                  final issue = snap.data;
                  if (issue != null && issue.message != _lastShownIssue) {
                    _lastShownIssue = issue.message;
                    // Show as snackbar and clear stored issue so UI isn't obstructive
                    WidgetsBinding.instance.addPostFrameCallback((_) {
                      if (!mounted) return;
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Row(
                            children: [
                              const Icon(Icons.wifi_off, color: Colors.white),
                              const SizedBox(width: 8),
                              Expanded(child: Text(issue.message)),
                            ],
                          ),
                          backgroundColor: Colors.red.shade700,
                          behavior: SnackBarBehavior.floating,
                          duration: const Duration(seconds: 5),
                          action: SnackBarAction(
                            label: 'Stäng',
                            textColor: Colors.white,
                            onPressed: () {},
                          ),
                        ),
                      );
                      // Also clear the error so the stream returns to null
                      NetworkService().clearError();
                    });
                  }
                  return const SizedBox.shrink();
                },
              );
            }),
          ],
        );
      },
    );
  }
}

Future<bool> _shouldShowCoachmarks() async {
  final sp = await SharedPreferences.getInstance();
  return !(sp.getBool('coachmarks_seen') ?? false);
}


