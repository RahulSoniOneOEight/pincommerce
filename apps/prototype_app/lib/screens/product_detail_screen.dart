import 'package:agency_flutter_ui/agency_flutter_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/models.dart';
import '../providers/cart_providers.dart';
import '../providers/catalog_providers.dart';
import '../widgets/status_views.dart';

/// Product detail with an add-to-cart action against the default variant.
class ProductDetailScreen extends ConsumerWidget {
  const ProductDetailScreen({super.key, required this.productId});

  final String productId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final product = ref.watch(productProvider(productId));
    return Scaffold(
      appBar: AppBar(),
      body: product.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => ErrorView(
          error: error,
          onRetry: () => ref.invalidate(productProvider(productId)),
        ),
        data: (p) => _ProductDetail(product: p),
      ),
    );
  }
}

class _ProductDetail extends ConsumerWidget {
  const _ProductDetail({required this.product});

  final Product product;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final canAdd = product.variantId != null;
    return ListView(
      padding: const EdgeInsets.all(AgencySpacing.md),
      children: <Widget>[
        Text(product.title, style: AgencyText.title),
        if (product.description != null) ...<Widget>[
          const SizedBox(height: AgencySpacing.sm),
          Text(product.description!, style: AgencyText.body),
        ],
        const SizedBox(height: AgencySpacing.md),
        Text(product.price?.formatted ?? 'Price on request',
            style: AgencyText.metric),
        const SizedBox(height: AgencySpacing.lg),
        FilledButton.icon(
          onPressed: canAdd
              ? () async {
                  final messenger = ScaffoldMessenger.of(context);
                  await ref
                      .read(cartProvider.notifier)
                      .addItem(variantId: product.variantId!, quantity: 1);
                  if (context.mounted) {
                    messenger.showSnackBar(
                      const SnackBar(content: Text('Added to cart')),
                    );
                  }
                }
              : null,
          icon: const Icon(Icons.add_shopping_cart),
          label: const Text('Add to cart'),
        ),
      ],
    );
  }
}
