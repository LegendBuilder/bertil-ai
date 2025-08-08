class DocumentSummary {
  DocumentSummary({required this.id, required this.uploadedAt, this.status = DocumentStatus.newDoc});
  final String id;
  final DateTime uploadedAt;
  DocumentStatus status;
}

enum DocumentStatus { newDoc, waitingInfo, done }


