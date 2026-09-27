import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/local_store.dart';
import '../data/medusa_api.dart';
import '../domain/models.dart';

/// Cart state controller.
///
/// Keeps a single Medusa cart and exposes add/update/remove operations that
/// round-trip through the API (single source of truth is the backend cart).
/// The last-known cart is persisted locally and restored on startup so the
/// cart survives restarts and remains visible while offline.
class CartNotifier extends Notifier<AsyncValue<Cart?>> {
  @override
  AsyncValue<Cart?> build() {
    final restored = ref.read(localStoreProvider).readCart();
    return AsyncValue.data(restored);
  }

  MedusaStoreClient get _client => ref.read(medusaClientProvider);

  LocalStore get _store => ref.read(localStoreProvider);

  Future<void> _setCart(Cart cart) async {
    state = AsyncValue.data(cart);
    await _store.writeCart(cart);
  }

  /// Returns the existing cart or creates one on first use.
  Future<Cart> _requireCart() async {
    final existing = state.value;
    if (existing != null) return existing;
    final cart = await _client.createCart();
    await _setCart(cart);
    return cart;
  }

  Future<void> addItem(
      {required String variantId, required int quantity}) async {
    try {
      final cart = await _requireCart();
      final updated = await _client.addLineItem(cart.id,
          variantId: variantId, quantity: quantity);
      await _setCart(updated);
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
      await _setCart(updated);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> removeItem(String lineItemId) async {
    final cart = state.value;
    if (cart == null) return;
    try {
      final updated = await _client.removeLineItem(cart.id, lineItemId);
      await _setCart(updated);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }
}

final cartProvider =
    NotifierProvider<CartNotifier, AsyncValue<Cart?>>(CartNotifier.new);
