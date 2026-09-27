import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/medusa_api.dart';
import '../domain/models.dart';

/// Cart state controller.
///
/// Keeps a single Medusa cart alive in memory and exposes add/update/remove
/// operations that always round-trip through the API (single source of truth
/// is the backend cart).
class CartNotifier extends Notifier<AsyncValue<Cart?>> {
  @override
  AsyncValue<Cart?> build() => const AsyncValue.data(null);

  MedusaStoreClient get _client => ref.read(medusaClientProvider);

  /// Returns the existing cart or creates one on first use.
  Future<Cart> _requireCart() async {
    final existing = state.value;
    if (existing != null) return existing;
    final cart = await _client.createCart();
    state = AsyncValue.data(cart);
    return cart;
  }

  Future<void> addItem(
      {required String variantId, required int quantity}) async {
    try {
      final cart = await _requireCart();
      final updated = await _client.addLineItem(cart.id,
          variantId: variantId, quantity: quantity);
      state = AsyncValue.data(updated);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> updateQuantity(String lineItemId, int quantity) async {
    if (quantity <= 0) return removeItem(lineItemId);
    final cart = state.value;
    if (cart == null) return;
    try {
      final updated =
          await _client.updateLineItem(cart.id, lineItemId, quantity: quantity);
      state = AsyncValue.data(updated);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> removeItem(String lineItemId) async {
    final cart = state.value;
    if (cart == null) return;
    try {
      final updated = await _client.removeLineItem(cart.id, lineItemId);
      state = AsyncValue.data(updated);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }
}

final cartProvider =
    NotifierProvider<CartNotifier, AsyncValue<Cart?>>(CartNotifier.new);
