import 'package:agency_flutter_ui/agency_flutter_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../data/medusa_api.dart';
import '../domain/models.dart';
import '../providers/cart_providers.dart';

/// Checkout form: captures contact + shipping address and persists them to the
/// cart. Payment is intentionally mocked here — the production payment flow is
/// wired through the governed payment connector in staging.
class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  String _email = '';
  String _firstName = '';
  String _lastName = '';
  String _address1 = '';
  String _city = '';
  String _postalCode = '';
  bool _submitting = false;

  Future<void> _placeOrder() async {
    final cart = ref.read(cartProvider).value;
    if (cart == null) {
      _show('Your cart is empty');
      return;
    }
    setState(() => _submitting = true);
    try {
      final client = ref.read(medusaClientProvider);
      await client.setEmail(cart.id, _email.trim());
      await client.setShippingAddress(
        cart.id,
        Address(
          firstName: _firstName.trim(),
          lastName: _lastName.trim(),
          address1: _address1.trim(),
          city: _city.trim(),
          postalCode: _postalCode.trim(),
          countryCode: 'IN',
        ),
      );
      if (!mounted) return;
      _show('Order placed — payment is mocked in staging');
      context.go('/');
    } catch (error) {
      if (!mounted) return;
      _show('Checkout failed: $error');
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _show(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final cart = ref.watch(cartProvider).value;
    return Scaffold(
      appBar: AppBar(title: const Text('Checkout')),
      body: ListView(
        padding: const EdgeInsets.all(AgencySpacing.md),
        children: <Widget>[
          CheckoutSummary(
            subtotal: cart?.total?.formatted ?? '—',
            shipping: 'Free',
            total: cart?.total?.formatted ?? '—',
          ),
          const SizedBox(height: AgencySpacing.md),
          FormSection(
              label: 'Email', value: _email, onChanged: (v) => _email = v),
          FormSection(
              label: 'First name',
              value: _firstName,
              onChanged: (v) => _firstName = v),
          FormSection(
              label: 'Last name',
              value: _lastName,
              onChanged: (v) => _lastName = v),
          FormSection(
              label: 'Address',
              value: _address1,
              onChanged: (v) => _address1 = v),
          FormSection(label: 'City', value: _city, onChanged: (v) => _city = v),
          FormSection(
              label: 'Postal code',
              value: _postalCode,
              onChanged: (v) => _postalCode = v),
          const SizedBox(height: AgencySpacing.lg),
          FilledButton(
            onPressed: _submitting ? null : _placeOrder,
            child: _submitting
                ? const SizedBox(
                    height: 18,
                    width: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Place order'),
          ),
        ],
      ),
    );
  }
}
