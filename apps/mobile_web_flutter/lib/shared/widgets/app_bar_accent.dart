import 'package:flutter/material.dart';

PreferredSizeWidget appBarAccent(BuildContext context) {
  final colors = Theme.of(context).colorScheme;
  return PreferredSize(
    preferredSize: const Size.fromHeight(2),
    child: Container(
      height: 2,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [colors.primary, colors.tertiary],
        ),
      ),
    ),
  );
}


