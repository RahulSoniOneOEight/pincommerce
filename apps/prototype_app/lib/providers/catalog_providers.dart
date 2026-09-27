import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/medusa_api.dart';
import '../domain/models.dart';

/// Catalog providers for the browse flow.
final productsProvider = FutureProvider.autoDispose<List<Product>>((ref) async {
  return ref.watch(medusaClientProvider).listProducts();
});

final productProvider =
    FutureProvider.autoDispose.family<Product, String>((ref, id) async {
  return ref.watch(medusaClientProvider).listProducts().then((products) {
    final match = products.where((p) => p.id == id).firstOrNull;
    if (match != null) return match;
    throw StateError('Product $id not found');
  });
});
