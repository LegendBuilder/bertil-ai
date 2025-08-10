import 'package:flutter/material.dart';

class ShortcutHelpOverlay extends StatelessWidget {
  const ShortcutHelpOverlay({super.key, required this.entries, this.title = 'Kortkommandon'});
  final List<MapEntry<String, String>> entries;
  final String title;

  static void show(BuildContext context, List<MapEntry<String, String>> entries, {String title = 'Kortkommandon'}) {
    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(title, style: Theme.of(ctx).textTheme.titleMedium),
                    IconButton(
                      tooltip: 'Stäng',
                      onPressed: () => Navigator.of(ctx).pop(),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                ...entries.map((e) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              border: Border.all(color: Colors.grey.shade400),
                              borderRadius: BorderRadius.circular(6),
                              color: Colors.grey.shade100,
                            ),
                            child: Text(e.key, style: const TextStyle(fontFamily: 'monospace')),
                          ),
                          const SizedBox(width: 12),
                          Expanded(child: Text(e.value)),
                        ],
                      ),
                    )),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return const SizedBox.shrink();
  }
}




