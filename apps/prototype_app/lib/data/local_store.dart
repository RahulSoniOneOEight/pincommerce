import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../domain/models.dart';

/// App-wide [SharedPreferences].
///
/// This provider is overridden in `main()` after the async
/// `SharedPreferences.getInstance()` completes. It must not be read before that
/// override is installed.
final sharedPreferencesProvider = Provider<SharedPreferences>(
  (ref) => throw UnimplementedError(
    'sharedPreferencesProvider must be overridden in main()',
  ),
);

/// Lightweight JSON persistence for the cart and product catalog.
///
/// Gives the storefront offline capability: the last-known cart and catalog
/// survive restarts and are served when the backend is unreachable.
class LocalStore {
  LocalStore(this._prefs);

  final SharedPreferences _prefs;

  static const String _cartKey = 'cart_v1';
  static const String _catalogKey = 'catalog_v1';

  Cart? readCart() {
    final raw = _prefs.getString(_cartKey);
    if (raw == null) return null;
    try {
      return Cart.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> writeCart(Cart? cart) async {
    if (cart == null) {
      await _prefs.remove(_cartKey);
    } else {
      await _prefs.setString(_cartKey, jsonEncode(cart.toJson()));
    }
  }

  List<Product> readCatalog() {
    final raw = _prefs.getString(_catalogKey);
    if (raw == null) return const <Product>[];
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list
          .whereType<Map<String, dynamic>>()
          .map(Product.fromCacheJson)
          .toList();
    } catch (_) {
      return const <Product>[];
    }
  }

  Future<void> writeCatalog(List<Product> products) async {
    await _prefs.setString(
      _catalogKey,
      jsonEncode(products.map((p) => p.toCacheJson()).toList()),
    );
  }
}

final localStoreProvider = Provider<LocalStore>(
    (ref) => LocalStore(ref.watch(sharedPreferencesProvider)));
