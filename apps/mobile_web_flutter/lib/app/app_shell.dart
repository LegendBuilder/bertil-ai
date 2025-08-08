import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.child});
  final Widget child;

  static const _tabs = [
    _TabItem(label: 'Hem', icon: Icons.home_outlined, route: '/'),
    _TabItem(label: 'Fota', icon: Icons.camera_alt_outlined, route: '/capture'),
    _TabItem(label: 'Dokument', icon: Icons.description_outlined, route: '/documents'),
    _TabItem(label: 'Rapporter', icon: Icons.bar_chart_outlined, route: '/reports'),
    _TabItem(label: 'Konto', icon: Icons.person_outline, route: '/settings'),
  ];

  int _indexForLocation(String location) {
    final idx = _tabs.indexWhere((t) => location == t.route || location.startsWith('${t.route}/'));
    return idx >= 0 ? idx : 0;
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();
    final selected = _indexForLocation(location);

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: selected,
        onDestinationSelected: (idx) => context.go(_tabs[idx].route),
        destinations: [
          for (final t in _tabs)
            NavigationDestination(icon: Icon(t.icon), label: t.label),
        ],
      ),
    );
  }
}

class _TabItem {
  const _TabItem({required this.label, required this.icon, required this.route});
  final String label;
  final IconData icon;
  final String route;
}


