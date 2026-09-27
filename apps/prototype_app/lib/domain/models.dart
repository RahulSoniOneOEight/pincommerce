/// Immutable domain models for the PinCommerce storefront.
///
/// JSON parsing is deliberately tolerant: Medusa storefront payloads can vary
/// slightly between releases, so every field degrades to a safe default rather
/// than throwing during deserialization.
library;

/// A monetary amount expressed in a currency's minor unit (e.g. paise for INR,
/// cents for USD).
class Money {
  const Money({required this.amount, required this.currencyCode});

  final int amount;
  final String currencyCode;

  /// Formats the amount as a human-readable string, e.g. "₹1,999" or "$20.50".
  String get formatted {
    final major = amount / 100;
    final text = major == major.roundToDouble()
        ? major.toStringAsFixed(0)
        : major.toStringAsFixed(2);
    switch (currencyCode.toUpperCase()) {
      case 'INR':
        return '₹$text';
      case 'USD':
        return '\$$text';
      case 'EUR':
        return '€$text';
      case 'GBP':
        return '£$text';
      default:
        return '${currencyCode.toUpperCase()} $text';
    }
  }

  Map<String, dynamic> toJson() => <String, dynamic>{
        'amount': amount,
        'currency_code': currencyCode,
      };
}

/// A sellable product, flattened to a single default variant for the
/// browse → add-to-cart flow.
class Product {
  const Product({
    required this.id,
    required this.title,
    this.description,
    this.thumbnail,
    this.variantId,
    this.price,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    final variants = (json['variants'] as List<dynamic>? ?? const <dynamic>[])
        .whereType<Map<String, dynamic>>()
        .toList();

    String? variantId;
    Money? price;
    if (variants.isNotEmpty) {
      final variant = variants.first;
      variantId = variant['id'] as String?;

      final prices = variant['prices'];
      Map<String, dynamic>? firstPrice;
      if (prices is List &&
          prices.isNotEmpty &&
          prices.first is Map<String, dynamic>) {
        firstPrice = prices.first as Map<String, dynamic>;
      }

      num? amount;
      final calculated = variant['calculated_price'];
      if (calculated is Map<String, dynamic> &&
          calculated['calculated_amount'] is num) {
        amount = calculated['calculated_amount'] as num;
      } else if (firstPrice != null && firstPrice['amount'] is num) {
        amount = firstPrice['amount'] as num;
      }

      if (amount != null) {
        final currency = (firstPrice?['currency_code'] as String?) ??
            json['currency_code'] as String? ??
            'INR';
        price = Money(amount: amount.toInt(), currencyCode: currency);
      }
    }

    return Product(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String?,
      thumbnail: json['thumbnail'] as String?,
      variantId: variantId,
      price: price,
    );
  }

  final String id;
  final String title;
  final String? description;
  final String? thumbnail;
  final String? variantId;
  final Money? price;

  /// Compact serialization for the local catalog cache (round-trips with
  /// [Product.fromCacheJson]).
  Map<String, dynamic> toCacheJson() => <String, dynamic>{
        'id': id,
        'title': title,
        'description': description,
        'thumbnail': thumbnail,
        'variant_id': variantId,
        'price_amount': price?.amount,
        'price_currency': price?.currencyCode,
      };

  static Product fromCacheJson(Map<String, dynamic> json) => Product(
        id: json['id'] as String? ?? '',
        title: json['title'] as String? ?? '',
        description: json['description'] as String?,
        thumbnail: json['thumbnail'] as String?,
        variantId: json['variant_id'] as String?,
        price: json['price_amount'] == null
            ? null
            : Money(
                amount: (json['price_amount'] as num).toInt(),
                currencyCode: json['price_currency'] as String? ?? 'INR',
              ),
      );
}

/// A line item within a [Cart].
class CartLineItem {
  const CartLineItem({
    required this.id,
    required this.title,
    required this.quantity,
    this.unitPrice,
    this.total,
  });

  factory CartLineItem.fromJson(Map<String, dynamic> json) {
    Money? fromMinor(num? amount, String? currency) => amount == null
        ? null
        : Money(amount: amount.toInt(), currencyCode: currency ?? 'INR');
    return CartLineItem(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      quantity: (json['quantity'] as num?)?.toInt() ?? 0,
      unitPrice: fromMinor(
          json['unit_price'] as num?, json['currency_code'] as String?),
      total: fromMinor(json['total'] as num?, json['currency_code'] as String?),
    );
  }

  final String id;
  final String title;
  final int quantity;
  final Money? unitPrice;
  final Money? total;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'title': title,
        'quantity': quantity,
        'unit_price': unitPrice?.amount,
        'total': total?.amount,
        'currency_code': unitPrice?.currencyCode ?? total?.currencyCode,
      };
}

/// A Medusa shopping cart with its line items and totals.
class Cart {
  const Cart(
      {required this.id, this.items = const <CartLineItem>[], this.total});

  factory Cart.fromJson(Map<String, dynamic> json) {
    final items = (json['items'] as List<dynamic>? ?? const <dynamic>[])
        .whereType<Map<String, dynamic>>()
        .map(CartLineItem.fromJson)
        .toList();
    final total = json['total'] as num?;
    return Cart(
      id: json['id'] as String? ?? '',
      items: items,
      total: total == null
          ? null
          : Money(
              amount: total.toInt(),
              currencyCode: json['currency_code'] as String? ?? 'INR'),
    );
  }

  final String id;
  final List<CartLineItem> items;
  final Money? total;

  int get itemCount => items.fold(0, (sum, item) => sum + item.quantity);

  Map<String, dynamic> toJson() => <String, dynamic>{
        'id': id,
        'items': items.map((e) => e.toJson()).toList(),
        'total': total?.amount,
        'currency_code': total?.currencyCode,
      };
}

/// A shipping/billing address sent to Medusa.
class Address {
  const Address({
    required this.firstName,
    required this.lastName,
    required this.address1,
    required this.city,
    required this.postalCode,
    required this.countryCode,
  });

  final String firstName;
  final String lastName;
  final String address1;
  final String city;
  final String postalCode;
  final String countryCode;

  Map<String, dynamic> toJson() => <String, dynamic>{
        'first_name': firstName,
        'last_name': lastName,
        'address_1': address1,
        'city': city,
        'postal_code': postalCode,
        'country_code': countryCode,
      };
}
