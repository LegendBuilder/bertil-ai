class Customer {
  final int? id;
  final int? orgId;
  final String name;
  final String? orgnr;
  final String? vatNumber;
  final String? email;
  final String? address;
  final String? postalCode;
  final String? city;
  final String country;
  final int paymentTerms;
  final DateTime? createdAt;

  Customer({
    this.id,
    this.orgId,
    required this.name,
    this.orgnr,
    this.vatNumber,
    this.email,
    this.address,
    this.postalCode,
    this.city,
    this.country = 'SE',
    this.paymentTerms = 30,
    this.createdAt,
  });

  factory Customer.fromJson(Map<String, dynamic> json) {
    return Customer(
      id: json['id'],
      orgId: json['org_id'],
      name: json['name'],
      orgnr: json['orgnr'],
      vatNumber: json['vat_number'],
      email: json['email'],
      address: json['address'],
      postalCode: json['postal_code'],
      city: json['city'],
      country: json['country'] ?? 'SE',
      paymentTerms: json['payment_terms'] ?? 30,
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      if (orgId != null) 'org_id': orgId,
      'name': name,
      if (orgnr != null) 'orgnr': orgnr,
      if (vatNumber != null) 'vat_number': vatNumber,
      if (email != null) 'email': email,
      if (address != null) 'address': address,
      if (postalCode != null) 'postal_code': postalCode,
      if (city != null) 'city': city,
      'country': country,
      'payment_terms': paymentTerms,
      if (createdAt != null) 'created_at': createdAt!.toIso8601String(),
    };
  }

  Customer copyWith({
    int? id,
    int? orgId,
    String? name,
    String? orgnr,
    String? vatNumber,
    String? email,
    String? address,
    String? postalCode,
    String? city,
    String? country,
    int? paymentTerms,
    DateTime? createdAt,
  }) {
    return Customer(
      id: id ?? this.id,
      orgId: orgId ?? this.orgId,
      name: name ?? this.name,
      orgnr: orgnr ?? this.orgnr,
      vatNumber: vatNumber ?? this.vatNumber,
      email: email ?? this.email,
      address: address ?? this.address,
      postalCode: postalCode ?? this.postalCode,
      city: city ?? this.city,
      country: country ?? this.country,
      paymentTerms: paymentTerms ?? this.paymentTerms,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  String get displayAddress {
    final parts = <String>[];
    if (address?.isNotEmpty == true) parts.add(address!);
    if (postalCode?.isNotEmpty == true && city?.isNotEmpty == true) {
      parts.add('$postalCode $city');
    }
    return parts.join(', ');
  }

  @override
  String toString() => 'Customer(id: $id, name: $name)';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Customer &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          name == other.name;

  @override
  int get hashCode => id.hashCode ^ name.hashCode;
}