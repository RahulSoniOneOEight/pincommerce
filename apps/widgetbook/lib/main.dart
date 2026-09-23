import 'package:agency_flutter_ui/agency_flutter_ui.dart';
import 'package:flutter/material.dart';
import 'package:widgetbook/widgetbook.dart';

void main() => runApp(const AgencyWidgetbook());

Widget shell(Widget child) => Padding(
  padding: const EdgeInsets.all(AgencySpacing.lg),
  child: SizedBox(width: 720, child: child),
);

class AgencyWidgetbook extends StatelessWidget {
  const AgencyWidgetbook({super.key});

  @override
  Widget build(BuildContext context) {
    return Widgetbook.material(
      directories: [
        WidgetbookComponent(name: 'ProductCard', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const ProductCard(title: 'Reference Product', priceLabel: '₹1,999'))),
          WidgetbookUseCase(name: 'Discounted', builder: (_) => shell(const ProductCard(title: 'Reference Product', priceLabel: '₹1,499', previousPriceLabel: '₹1,999', state: CommerceFixture.discounted))),
          WidgetbookUseCase(name: 'Out of stock', builder: (_) => shell(const ProductCard(title: 'Reference Product', priceLabel: '₹1,999', state: CommerceFixture.outOfStock))),
          WidgetbookUseCase(name: 'Loading', builder: (_) => shell(const ProductCard(title: 'Reference Product', priceLabel: '₹1,999', state: CommerceFixture.loading))),
        ]),
        WidgetbookComponent(name: 'CategoryRail', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const CategoryRail(categories: ['New', 'Beauty', 'Wellness', 'Home']))),
          WidgetbookUseCase(name: 'Empty', builder: (_) => shell(const CategoryRail(categories: [], state: CommerceFixture.empty))),
        ]),
        WidgetbookComponent(name: 'B2BQuickOrder', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const B2BQuickOrder(lines: [
            QuickOrderLine(sku: 'SKU-001', name: 'Reference Product', quantity: 12),
            QuickOrderLine(sku: 'SKU-002', name: 'Second Product', quantity: 6),
          ]))),
          WidgetbookUseCase(name: 'Loading', builder: (_) => shell(const B2BQuickOrder(lines: [], state: CommerceFixture.loading))),
        ]),
        WidgetbookComponent(name: 'DashboardKpi', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const DashboardKpi(label: 'Net sales', value: '₹12.4L', trendLabel: '+8.2% vs prior period'))),
          WidgetbookUseCase(name: 'Failure', builder: (_) => shell(const DashboardKpi(label: 'Net sales', value: '—', state: CommerceFixture.failure))),
        ]),
        WidgetbookComponent(name: 'ExceptionTable', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const ExceptionTable(items: [
            ExceptionItem(id: 'EX-101', summary: 'Settlement mismatch', status: 'Open'),
            ExceptionItem(id: 'EX-102', summary: 'Inventory variance', status: 'Review'),
          ]))),
          WidgetbookUseCase(name: 'Empty', builder: (_) => shell(const ExceptionTable(items: [], state: CommerceFixture.empty))),
        ]),
        WidgetbookComponent(name: 'FilterBar', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const FilterBar(filters: ['In stock', 'Fast delivery', 'Under ₹2,000'], selected: {'In stock'}))),
          WidgetbookUseCase(name: 'Disabled', builder: (_) => shell(const FilterBar(filters: ['In stock', 'Fast delivery'], state: CommerceFixture.disabled))),
        ]),
        WidgetbookComponent(name: 'CheckoutSummary', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const CheckoutSummary(subtotal: '₹2,499', shipping: '₹99', total: '₹2,598'))),
          WidgetbookUseCase(name: 'Loading', builder: (_) => shell(const CheckoutSummary(subtotal: '₹2,499', shipping: '₹99', total: '₹2,598', state: CommerceFixture.loading))),
        ]),
        WidgetbookComponent(name: 'NavigationMenu', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const NavigationMenu(items: ['Home', 'Catalog', 'Orders', 'Account'], current: 'Catalog'))),
          WidgetbookUseCase(name: 'Disabled', builder: (_) => shell(const NavigationMenu(items: ['Home', 'Catalog'], current: 'Home', state: CommerceFixture.disabled))),
        ]),
        WidgetbookComponent(name: 'FormSection', useCases: [
          WidgetbookUseCase(name: 'Default', builder: (_) => shell(const FormSection(label: 'Email', value: 'buyer@example.com', helper: 'Order updates are sent here'))),
          WidgetbookUseCase(name: 'Validation error', builder: (_) => shell(const FormSection(label: 'Email', value: 'bad', error: 'Enter a valid email', state: CommerceFixture.validationError))),
        ]),
      ],
    );
  }
}
