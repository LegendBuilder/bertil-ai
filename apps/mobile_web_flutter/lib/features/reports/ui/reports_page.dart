import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../provider/reports_providers.dart';
import '../data/reports_api.dart';
import '../../../shared/services/network.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:file_picker/file_picker.dart';
// Avoid dart:io for web; use FilePicker with withData
import '../../../shared/services/analytics.dart';
import '../../../shared/widgets/skeleton.dart';
import '../../../shared/widgets/shortcut_help_overlay.dart';
import 'package:flutter/services.dart';

class ReportsPage extends ConsumerWidget {
  const ReportsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tb = ref.watch(trialBalanceProvider);
    final comp = ref.watch(complianceScoreProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Rapporter'),
        actions: [
          IconButton(
            tooltip: 'Kortkommandon',
            onPressed: () => ShortcutHelpOverlay.show(context, const [
              MapEntry('V', 'Exportera momsfil (SKV)'),
              MapEntry('E', 'Exportera SIE'),
              MapEntry('P', 'Öppna PDF-rapporter'),
              MapEntry('Tab/Shift+Tab', 'Navigera mellan knappar och paneler'),
              MapEntry('?', 'Visa denna hjälp'),
            ], title: 'Rapporter – kortkommandon'),
            icon: const Icon(Icons.help_outline),
          ),
        ],
      ),
      body: Shortcuts(
        shortcuts: <LogicalKeySet, Intent>{
          LogicalKeySet(LogicalKeyboardKey.keyV): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.keyE): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.keyP): const ActivateIntent(),
          LogicalKeySet(LogicalKeyboardKey.tab): const NextFocusIntent(),
          LogicalKeySet(LogicalKeyboardKey.shift, LogicalKeyboardKey.slash): const ActivateIntent(),
        },
        child: Actions(
          actions: <Type, Action<Intent>>{
            ActivateIntent: CallbackAction<ActivateIntent>(onInvoke: (intent) {
              final keys = RawKeyboard.instance.keysPressed;
              if (keys.contains(LogicalKeyboardKey.keyV)) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Kortkommando V: momsfil')));
              } else if (keys.contains(LogicalKeyboardKey.keyE)) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Kortkommando E: SIE-export')));
              } else if (keys.contains(LogicalKeyboardKey.keyP)) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Kortkommando P: PDF-rapporter')));
              } else if (keys.contains(LogicalKeyboardKey.slash) && keys.contains(LogicalKeyboardKey.shift)) {
                ShortcutHelpOverlay.show(context, const [
                  MapEntry('V', 'Exportera momsfil (SKV)'),
                  MapEntry('E', 'Exportera SIE'),
                  MapEntry('P', 'Öppna PDF-rapporter'),
                  MapEntry('Tab/Shift+Tab', 'Navigera mellan knappar och paneler'),
                  MapEntry('?', 'Visa denna hjälp'),
                ], title: 'Rapporter – kortkommandon');
              }
              return null;
            }),
          },
          child: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Consumer(builder: (context, ref, _) {
              final year = ref.watch(selectedYearProvider);
              return Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
                Text('År $year'),
                IconButton(
                  tooltip: 'Föregående år',
                  onPressed: () => ref.read(selectedYearProvider.notifier).state = year - 1,
                  icon: const Icon(Icons.chevron_left),
                ),
                IconButton(
                  tooltip: 'Nästa år',
                  onPressed: () => ref.read(selectedYearProvider.notifier).state = year + 1,
                  icon: const Icon(Icons.chevron_right),
                ),
              ]);
            }),
            const SizedBox(height: 8),
            Text('Momsstatus', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
             tb.when(
              loading: () => const LinearProgressIndicator(),
              error: (e, st) => const Text('Kunde inte hämta bokföringsdata'),
              data: (trial) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('År ${trial.year} – Total: ${trial.total.toStringAsFixed(2)} kr'),
                    const SizedBox(height: 8),
                     const SkeletonBox(width: 220, height: 14),
                     const SizedBox(height: 6),
                     const SkeletonBox(width: 180, height: 14),
                     const SizedBox(height: 6),
                    Consumer(builder: (context, ref, _) {
                      final vat = ref.watch(vatStatusTextProvider);
                      return vat.when(
                        loading: () => const LinearProgressIndicator(),
                        error: (e, st) => const SizedBox.shrink(),
                        data: (txt) => Text(txt, style: const TextStyle(fontWeight: FontWeight.w600)),
                      );
                    }),
                    const SizedBox(height: 8),
                    comp.when(
                      loading: () => const LinearProgressIndicator(),
                      error: (e, st) => const Text('Trygghet: okänd'),
                      data: (score) => Text(score >= 80
                          ? 'Allt redo ✅'
                          : score >= 50
                              ? '⚠️ Vissa saker kvar'
                              : '❌ blockerat'),
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 16),
            Semantics(label: 'Export', child: Text('Export', style: Theme.of(context).textTheme.titleMedium)),
            const SizedBox(height: 8),
            // Use Wrap to avoid horizontal overflow on smaller screens
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                Builder(builder: (context) {
                  final url = ReportsApi(NetworkService().client).sieExportUrl(DateTime.now().year).toString();
                  return OutlinedButton.icon(
                    onPressed: () async {
                      final uri = Uri.parse(url);
                      final ok = await canLaunchUrl(uri) && await launchUrl(
                        uri,
                        mode: LaunchMode.externalApplication,
                        webOnlyWindowName: '_blank',
                      );
                      if (ok) AnalyticsService.logEvent('export_sie_clicked');
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(ok ? 'SIE export skickad till nedladdning' : 'Kunde inte öppna exportlänk')),
                      );
                    },
                    icon: const Icon(Icons.download_outlined, semanticLabel: 'Ladda ner SIE'),
                    label: const Text('Ladda ner SIE'),
                  );
                }),
                Builder(builder: (context) {
                  final url = ReportsApi(NetworkService().client).verificationsPdfUrl(DateTime.now().year).toString();
                  return OutlinedButton.icon(
                    onPressed: () async {
                      final uri = Uri.parse(url);
                      final ok = await canLaunchUrl(uri) && await launchUrl(
                        uri,
                        mode: LaunchMode.externalApplication,
                        webOnlyWindowName: '_blank',
                      );
                      if (ok) AnalyticsService.logEvent('export_pdf_clicked');
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(ok ? 'PDF öppnas' : 'Kunde inte öppna PDF-länk')),
                      );
                    },
                    icon: const Icon(Icons.picture_as_pdf_outlined, semanticLabel: 'Öppna verifikationslista PDF'),
                    label: const Text('Verifikationslista (PDF)'),
                  );
                }),
                Builder(builder: (context) {
                  return OutlinedButton.icon(
                    onPressed: () async {
                      final res = await FilePicker.platform.pickFiles(
                        type: FileType.custom,
                        allowedExtensions: ['se', 'sie', 'txt'],
                        withData: true,
                      );
                      if (res != null && res.files.isNotEmpty) {
                        final file = res.files.first;
                        final bytes = file.bytes;
                        if (bytes == null) return;
                        await ReportsApi(NetworkService().client).importSie(bytes: bytes, filename: file.name);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('SIE importerat')));
                        }
                      }
                    },
                    icon: const Icon(Icons.upload_file, semanticLabel: 'Importera SIE'),
                    label: const Text('Importera SIE'),
                  );
                }),
                Builder(builder: (context) {
                  final year = ref.read(selectedYearProvider);
                  final month = DateTime.now().month;
                  final url = ReportsApi(NetworkService().client).vatReportPdfUrl(year: year, month: month).toString();
                  return OutlinedButton.icon(
                    onPressed: () async {
                      final uri = Uri.parse(url);
                      final ok = await canLaunchUrl(uri) && await launchUrl(
                        uri,
                        mode: LaunchMode.externalApplication,
                        webOnlyWindowName: '_blank',
                      );
                      if (ok) AnalyticsService.logEvent('export_vat_pdf');
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(ok ? 'PDF öppnas' : 'Kunde inte öppna PDF-länk')),
                      );
                    },
                    icon: const Icon(Icons.receipt_long_outlined, semanticLabel: 'Öppna momsrapport PDF'),
                    label: const Text('Momsrapport (PDF)')
                  );
                }),
                Builder(builder: (context) {
                  final year = ref.read(selectedYearProvider);
                  final month = DateTime.now().month;
                  final url = ReportsApi(NetworkService().client).vatSkvFileUrl(year: year, month: month).toString();
                  return OutlinedButton.icon(
                    onPressed: () async {
                      final uri = Uri.parse(url);
                      final can = await canLaunchUrl(uri);
                      if (can) {
                        final ok = await launchUrl(uri, mode: LaunchMode.externalApplication, webOnlyWindowName: '_blank');
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(ok ? 'Momsfil exporteras' : 'Kunde inte öppna momsfil-länk')));
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Momsfil export inaktiverad')));
                      }
                    },
                    icon: const Icon(Icons.file_download, semanticLabel: 'Exportera momsfil till Skatteverket'),
                    label: const Text('Momsfil (SKV)'),
                  );
                }),
              ],
            ),
            const SizedBox(height: 24),
            Text('Moms per kod (innevarande månad)', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            FutureBuilder<Map<String, dynamic>>(
              future: ReportsApi(NetworkService().client).getVatReport(year: ref.read(selectedYearProvider), month: DateTime.now().month),
              builder: (context, snap) {
                if (!snap.hasData) return const LinearProgressIndicator();
                final data = snap.data!;
                final byCode = (data['by_code'] as Map?)?.map((k, v) => MapEntry(k.toString(), (v as num).toInt())) ?? <String, int>{};
                if (byCode.isEmpty) return const Text('Inga kodade verifikationer');
                return Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final e in byCode.entries)
                      Semantics(
                        label: 'Moms kod ${e.key} antal ${e.value}',
                        child: Chip(label: Text('${e.key}: ${e.value}')),
                      ),
                  ],
                );
              },
            ),
            const SizedBox(height: 24),
            Text('Momsdeklaration (rutnätsrutor)', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            FutureBuilder<Map<String, num>>(
              future: ReportsApi(NetworkService().client).getVatDeclaration(year: ref.read(selectedYearProvider), month: DateTime.now().month),
              builder: (context, snap) {
                if (!snap.hasData) return const LinearProgressIndicator();
                final boxes = snap.data!;
                final order = ['05', '06', '07', '30', '31', '32', '48', '49'];
                return Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final k in order)
                      Semantics(
                        label: 'Ruta $k värde ${(boxes[k] ?? 0).toStringAsFixed(2)}',
                        child: Chip(label: Text('$k: ${(boxes[k] ?? 0).toStringAsFixed(2)}')),
                      ),
                  ],
                );
              },
            ),
            const SizedBox(height: 24),
            Text('Årsavslut (K2/K3)', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            const _YearEndChecklist(),
          ],
        ),
          ),
        ),
        ),
      ),
    );
  }
}

class _YearEndChecklist extends StatelessWidget {
  const _YearEndChecklist();

  @override
  Widget build(BuildContext context) {
    final items = const [
      ('Verifikationer klara', true),
      ('Periodisering klar', false),
      ('E-sign BankID', false),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final it in items)
          Row(
            children: [
              Icon(it.$2 ? Icons.check_circle_outline : Icons.radio_button_unchecked, color: it.$2 ? Colors.green : null),
              const SizedBox(width: 8),
              Text(it.$1),
            ],
          ),
      ],
    );
  }
}


