import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/local_store.dart';
import '../data/medusa_api.dart';
import '../domain/models.dart';

/// Catalog providers for the browse flow.
///
/// The product list is cached locally and served as a fallback when the backend
/// is unreachable, giving the storefront basic offline behaviour.
final productsProvider = FutureProvider.autoDispose<List<Product>>((ref) async {
  final client = ref.watch(medusaClientProvider);
  final store = ref.watch(localStoreProvider);
  try {
    final products = await client.listProducts();
    await store.writeCatalog(products);
    return products;
  } catch (_) {
    final cached = store.readCatalog();
    if (cached.isNotEmpty) return cached;
    rethrow;
  }
});

final productProvider =
    FutureProvider.autoDispose.family<Product, String>((ref, id) async {
  return ref.watch(medusaClientProvider).listProducts().then((products) {
    final match = products.where((p) => p.id == id).firstOrNull;
    if (match != null) return match;
    throw StateError('Product $id not found');
  });
});
