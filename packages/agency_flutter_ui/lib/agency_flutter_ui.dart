library agency_flutter_ui;

import 'package:flutter/material.dart';

abstract final class AgencySpacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
}

abstract final class AgencyRadius {
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
}

abstract final class AgencyText {
  static const TextStyle body = TextStyle(fontSize: 16, height: 1.5);
  static const TextStyle label = TextStyle(fontSize: 14, height: 1.4);
  static const TextStyle title = TextStyle(fontSize: 24, height: 1.25, fontWeight: FontWeight.w600);
  static const TextStyle metric = TextStyle(fontSize: 30, height: 1.15, fontWeight: FontWeight.w700);
}

abstract final class AgencyTheme {
  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(seedColor: const Color(0xFF17181A));
    return ThemeData(
      colorScheme: scheme,
      scaffoldBackgroundColor: const Color(0xFFFFFFFF),
      useMaterial3: true,
    );
  }
}

enum CommerceFixture {
  defaultState, loading, empty, failure, approvalPending, paymentFailed,
  disabled, validationError, outOfStock, discounted, editing, open, resolved,
}

Widget _messageCard(String message) => Card(
  child: Padding(
    padding: const EdgeInsets.all(AgencySpacing.md),
    child: Text(message, style: AgencyText.body),
  ),
);

class ProductCard extends StatelessWidget {
  const ProductCard({
    required this.title,
    required this.priceLabel,
    this.previousPriceLabel,
    this.state = CommerceFixture.defaultState,
    this.onPressed,
    super.key,
  });

  final String title;
  final String priceLabel;
  final String? previousPriceLabel;
  final CommerceFixture state;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    if (state == CommerceFixture.loading) {
      return const Card(child: Padding(
        padding: EdgeInsets.all(AgencySpacing.md),
        child: LinearProgressIndicator(),
      ));
    }
    if (state == CommerceFixture.failure) return _messageCard('Product unavailable');
    final unavailable = state == CommerceFixture.outOfStock;
    return Semantics(
      button: onPressed != null && !unavailable,
      label: '$title, $priceLabel',
      child: Card(
        child: InkWell(
          borderRadius: BorderRadius.circular(AgencyRadius.md),
          onTap: unavailable ? null : onPressed,
          child: Padding(
            padding: const EdgeInsets.all(AgencySpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: AgencyText.body),
                const SizedBox(height: AgencySpacing.sm),
                Row(children: [
                  Text(priceLabel, style: AgencyText.title),
                  if (state == CommerceFixture.discounted && previousPriceLabel != null) ...[
                    const SizedBox(width: AgencySpacing.sm),
                    Text(previousPriceLabel!, style: AgencyText.label.copyWith(decoration: TextDecoration.lineThrough)),
                  ],
                ]),
                if (unavailable) ...[
                  const SizedBox(height: AgencySpacing.sm),
                  const Text('Out of stock', style: AgencyText.label),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class CategoryRail extends StatelessWidget {
  const CategoryRail({
    required this.categories,
    this.state = CommerceFixture.defaultState,
    this.onSelected,
    super.key,
  });
  final List<String> categories;
  final CommerceFixture state;
  final ValueChanged<String>? onSelected;

  @override
  Widget build(BuildContext context) {
    if (state == CommerceFixture.loading) return const LinearProgressIndicator();
    if (state == CommerceFixture.failure) return _messageCard('Categories unavailable');
    if (state == CommerceFixture.empty || categories.isEmpty) return _messageCard('No categories');
    return Semantics(
      label: 'Product categories',
      child: SizedBox(
        height: 52,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: categories.length,
          separatorBuilder: (_, __) => const SizedBox(width: AgencySpacing.sm),
          itemBuilder: (context, index) {
            final category = categories[index];
            return ActionChip(label: Text(category), onPressed: onSelected == null ? null : () => onSelected!(category));
          },
        ),
      ),
    );
  }
}

class QuickOrderLine {
  const QuickOrderLine({required this.sku, required this.name, required this.quantity});
  final String sku;
  final String name;
  final int quantity;
}

class B2BQuickOrder extends StatelessWidget {
  const B2BQuickOrder({
    required this.lines,
    this.state = CommerceFixture.defaultState,
    this.onQuantityChanged,
    super.key,
  });
  final List<QuickOrderLine> lines;
  final CommerceFixture state;
  final void Function(String sku, int quantity)? onQuantityChanged;

  @override
  Widget build(BuildContext context) {
    if (state == CommerceFixture.loading) return const LinearProgressIndicator();
    if (state == CommerceFixture.failure) return _messageCard('Quick order unavailable');
    if (state == CommerceFixture.empty || lines.isEmpty) return _messageCard('No order lines');
    return Semantics(
      label: 'B2B quick order',
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columns: const [
            DataColumn(label: Text('SKU')),
            DataColumn(label: Text('Product')),
            DataColumn(label: Text('Qty')),
          ],
          rows: lines.map((line) => DataRow(cells: [
            DataCell(Text(line.sku)),
            DataCell(Text(line.name)),
            DataCell(Row(children: [
              IconButton(
                tooltip: 'Decrease ${line.name}',
                onPressed: onQuantityChanged == null ? null : () => onQuantityChanged!(line.sku, line.quantity > 0 ? line.quantity - 1 : 0),
                icon: const Icon(Icons.remove),
              ),
              Text('${line.quantity}'),
              IconButton(
                tooltip: 'Increase ${line.name}',
                onPressed: onQuantityChanged == null ? null : () => onQuantityChanged!(line.sku, line.quantity + 1),
                icon: const Icon(Icons.add),
              ),
            ])),
          ])).toList(),
        ),
      ),
    );
  }
}

class DashboardKpi extends StatelessWidget {
  const DashboardKpi({
    required this.label,
    required this.value,
    this.trendLabel,
    this.state = CommerceFixture.defaultState,
    super.key,
  });
  final String label;
  final String value;
  final String? trendLabel;
  final CommerceFixture state;

  @override
  Widget build(BuildContext context) {
    if (state == CommerceFixture.loading) {
      return const Card(child: Padding(
        padding: EdgeInsets.all(AgencySpacing.md),
        child: LinearProgressIndicator(),
      ));
    }
    if (state == CommerceFixture.failure) return _messageCard('Metric unavailable');
    return Semantics(
      label: '$label $value',
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(AgencySpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: AgencyText.label),
              const SizedBox(height: AgencySpacing.sm),
              Text(value, style: AgencyText.metric),
              if (trendLabel != null) ...[
                const SizedBox(height: AgencySpacing.xs),
                Text(trendLabel!, style: AgencyText.label),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class ExceptionItem {
  const ExceptionItem({required this.id, required this.summary, required this.status});
  final String id;
  final String summary;
  final String status;
}

class ExceptionTable extends StatelessWidget {
  const ExceptionTable({
    required this.items,
    this.state = CommerceFixture.defaultState,
    this.onOpen,
    super.key,
  });
  final List<ExceptionItem> items;
  final CommerceFixture state;
  final ValueChanged<String>? onOpen;

  @override
  Widget build(BuildContext context) {
    if (state == CommerceFixture.loading) return const LinearProgressIndicator();
    if (state == CommerceFixture.failure) return _messageCard('Exceptions unavailable');
    if (state == CommerceFixture.empty || items.isEmpty) return _messageCard('No exceptions');
    return Semantics(
      label: 'Operational exceptions',
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columns: const [
            DataColumn(label: Text('ID')),
            DataColumn(label: Text('Exception')),
            DataColumn(label: Text('Status')),
            DataColumn(label: Text('Action')),
          ],
          rows: items.map((item) => DataRow(cells: [
            DataCell(Text(item.id)),
            DataCell(Text(item.summary)),
            DataCell(Text(item.status)),
            DataCell(TextButton(onPressed: onOpen == null ? null : () => onOpen!(item.id), child: const Text('Open'))),
          ])).toList(),
        ),
      ),
    );
  }
}

class Surface extends StatelessWidget {
  const Surface({required this.child, super.key});
  final Widget child;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(AgencySpacing.lg),
    child: child,
  );
}
