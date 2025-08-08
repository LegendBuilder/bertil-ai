import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/documents_api.dart';

final explainabilityProvider = Provider.family<String, DocumentDetail>((ref, doc) {
  // Build a quick lookup for fields
  final fields = {for (final f in doc.extractedFields) f.key.toLowerCase(): f.value};
  final vendor = (fields['vendor'] ?? '').toLowerCase();
  final total = fields['total'];

  // Simple, human-friendly reason strings (stubbed logic for MVP)
  if (vendor.contains('kaffe') || vendor.contains('café') || vendor.contains('fika')) {
    return 'Valde konto 5811 (representation) baserat på leverantören "${fields['vendor'] ?? 'okänd'}" och låg summa${total != null ? ' (${total} kr)' : ''}.';
  }
  if (vendor.contains('taxi')) {
    return 'Valde konto 5611 (personbilskostnader) baserat på leverantören "${fields['vendor'] ?? 'okänd'}".';
  }
  if (vendor.contains('shell') || vendor.contains('circle k') || vendor.contains('preem')) {
    return 'Valde konto 5611 (drivmedel) baserat på bränslestation.';
  }

  return 'Förslag valt automatiskt baserat på leverantör och belopp. Du kan alltid välja "Vet inte" så löser vi det åt dig.';
});


