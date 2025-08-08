import 'dart:convert';
import 'dart:typed_data';

import 'package:crypto/crypto.dart' as crypto;

String sha256Hex(Uint8List bytes) {
  final digest = crypto.sha256.convert(bytes);
  return digest.toString();
}


