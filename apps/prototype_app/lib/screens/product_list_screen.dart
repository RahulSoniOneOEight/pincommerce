import 'package:agency_flutter_ui/agency_flutter_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../domain/models.dart';
import '../providers/cart_providers.dart';
import '../providers/catalog_providers.dart';
import '../widgets/status_views.dart';

/// Browse entry point: lists the catalog with a cart affordance in the app bar.
class ProductListScreen extends ConsumerWidget {
  const ProductListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final products = ref.watch(productsProvider);
    final itemCount = ref.watch(cartProvider).value?.itemCount ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('PinCommerce'),
        actions: <Widget>[
          IconButton(
            tooltip: 'B2B account',
            onPressed: () => context.push('/account'),
            icon: const Icon(Icons.business_outlined),
          ),
          IconButton(
            tooltip: 'Cart',
            onPressed: () => context.push('/cart'),
            icon: Badge(
              isLabelVisible: itemCount > 0,
              label: Text('$itemCount'),
              child: const Icon(Icons.shopping_cart_outlined),
            ),
          ),
        ],
      ),
      body: products.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => ErrorView(
            error: error, onRetry: () => ref.invalidate(productsProvider)),
        data: (items) => _Catalog(items: items),
      ),
    );
  }
}

class _Catalog extends StatelessWidget {
  const _Catalog({required this.items});

  final List<Product> items;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(AgencySpacing.md),
      children: <Widget>[
        const CategoryRail(categories: <String>['All', 'New', 'Deals', 'B2B']),
        const SizedBox(height: AgencySpacing.md),
        if (items.isEmpty)
          const EmptyView(
              message: 'No products yet — seed your Medusa catalog.')
        else
          for (final product in items) ...<Widget>[
            ProductCard(
              title: product.title,
              priceLabel: product.price?.formatted ?? 'Price on request',
              onPressed: () => context.push('/product/${product.id}'),
            ),
            const SizedBox(height: AgencySpacing.sm),
          ],
      ],
    );
  }
}
