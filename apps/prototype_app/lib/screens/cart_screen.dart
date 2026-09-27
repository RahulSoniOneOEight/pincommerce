import 'package:agency_flutter_ui/agency_flutter_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../domain/models.dart';
import '../providers/cart_providers.dart';
import '../widgets/status_views.dart';

/// The active cart with quantity controls and a checkout summary.
class CartScreen extends ConsumerWidget {
  const CartScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cartState = ref.watch(cartProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Cart')),
      body: cartState.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => ErrorView(error: error),
        data: (cart) {
          if (cart == null || cart.items.isEmpty) {
            return const EmptyView(message: 'Your cart is empty');
          }
          return ListView(
            padding: const EdgeInsets.all(AgencySpacing.md),
            children: <Widget>[
              for (final item in cart.items) _LineItemTile(item: item),
              const SizedBox(height: AgencySpacing.md),
              CheckoutSummary(
                subtotal: cart.total?.formatted ?? '—',
                shipping: 'Free',
                total: cart.total?.formatted ?? '—',
                onContinue: () => context.push('/checkout'),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _LineItemTile extends ConsumerWidget {
  const _LineItemTile({required this.item});

  final CartLineItem item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(cartProvider.notifier);
    return Card(
      child: ListTile(
        title: Text(item.title),
        subtitle: Text(item.unitPrice?.formatted ?? ''),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            IconButton(
              tooltip: 'Decrease',
              onPressed: () =>
                  notifier.updateQuantity(item.id, item.quantity - 1),
              icon: const Icon(Icons.remove),
            ),
            Text('${item.quantity}', style: AgencyText.label),
            IconButton(
              tooltip: 'Increase',
              onPressed: () =>
                  notifier.updateQuantity(item.id, item.quantity + 1),
              icon: const Icon(Icons.add),
            ),
          ],
        ),
      ),
    );
  }
}
