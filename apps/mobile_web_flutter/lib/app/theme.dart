import 'package:flutter/material.dart';

ThemeData buildTheme() {
  final base = ThemeData.light(useMaterial3: true);
  return base.copyWith(
    colorScheme: base.colorScheme.copyWith(
      primary: const Color(0xFF0B6E4F),
      secondary: const Color(0xFF1B9C85),
      surface: const Color(0xFFF7F8FA),
    ),
    visualDensity: VisualDensity.adaptivePlatformDensity,
    appBarTheme: const AppBarTheme(centerTitle: true),
    snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(minimumSize: const Size(44, 44)),
    ),
    listTileTheme: const ListTileThemeData(
      dense: false,
      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    ),
  );
}


