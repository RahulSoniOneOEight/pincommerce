library agency_flutter_ui;

import 'package:flutter/material.dart';
import 'package:iconoir_flutter/iconoir_flutter.dart' as iconoir;

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

enum AgencyMotionToken { instant, fast, standard, slow, page }

abstract final class AgencyMotion {
  static const _durations = {
    AgencyMotionToken.instant: Duration(milliseconds: 80),
    AgencyMotionToken.fast: Duration(milliseconds: 140),
    AgencyMotionToken.standard: Duration(milliseconds: 220),
    AgencyMotionToken.slow: Duration(milliseconds: 320),
    AgencyMotionToken.page: Duration(milliseconds: 380),
  };

  static Duration resolve(BuildContext context, AgencyMotionToken token) {
    final media = MediaQuery.maybeOf(context);
    if (media?.disableAnimations ?? false) return Duration.zero;
    return _durations[token]!;
  }
}

enum AgencyIconConcept { increment, decrement, search, warning, success, error }

class AgencyIcon extends StatelessWidget {
  const AgencyIcon(this.concept, {this.size = 20, super.key});
  final AgencyIconConcept concept;
  final double size;

  @override
  Widget build(BuildContext context) => switch (concept) {
    AgencyIconConcept.increment => iconoir.Plus(width: size, height: size),
    AgencyIconConcept.decrement => iconoir.Minus(width: size, height: size),
    AgencyIconConcept.search => iconoir.Search(width: size, height: size),
    AgencyIconConcept.warning => iconoir.WarningTriangle(width: size, height: size),
    AgencyIconConcept.success => iconoir.CheckCircle(width: size, height: size),
    AgencyIconConcept.error => iconoir.Xmark(width: size, height: size),
  };
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
                icon: const AgencyIcon(AgencyIconConcept.decrement),
              ),
              Text('${line.quantity}'),
              IconButton(
                tooltip: 'Increase ${line.name}',
                onPressed: onQuantityChanged == null ? null : () => onQuantityChanged!(line.sku, line.quantity + 1),
                icon: const AgencyIcon(AgencyIconConcept.increment),
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

class FilterBar extends StatelessWidget {
  const FilterBar({
    required this.filters,
    this.selected = const <String>{},
    this.onSelected,
    this.onClear,
    this.state = CommerceFixture.defaultState,
    super.key,
  });
  final List<String> filters;
  final Set<String> selected;
  final ValueChanged<String>? onSelected;
  final VoidCallback? onClear;
  final CommerceFixture state;

  @override
  Widget build(BuildContext context) {
    final disabled = state == CommerceFixture.disabled;
    return Semantics(
      label: 'Product filters',
      child: Wrap(
        spacing: AgencySpacing.sm,
        runSpacing: AgencySpacing.sm,
        children: [
          for (final filter in filters)
            FilterChip(
              label: Text(filter),
              selected: selected.contains(filter),
              onSelected: disabled || onSelected == null ? null : (_) => onSelected!(filter),
            ),
          TextButton(
            onPressed: disabled ? null : onClear,
            child: const Text('Clear'),
          ),
        ],
      ),
    );
  }
}

class CheckoutSummary extends StatelessWidget {
  const CheckoutSummary({
    required this.subtotal,
    required this.shipping,
    required this.total,
    this.onContinue,
    this.state = CommerceFixture.defaultState,
    super.key,
  });
  final String subtotal;
  final String shipping;
  final String total;
  final VoidCallback? onContinue;
  final CommerceFixture state;

  @override
  Widget build(BuildContext context) {
    if (state == CommerceFixture.loading) return const LinearProgressIndicator();
    final disabled = state == CommerceFixture.disabled;
    return Semantics(
      label: 'Checkout summary',
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(AgencySpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('Subtotal'), Text(subtotal)]),
              const SizedBox(height: AgencySpacing.sm),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('Shipping'), Text(shipping)]),
              const Divider(),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('Total', style: AgencyText.title), Text(total, style: AgencyText.title)]),
              const SizedBox(height: AgencySpacing.md),
              FilledButton(onPressed: disabled ? null : onContinue, child: const Text('Continue checkout')),
            ],
          ),
        ),
      ),
    );
  }
}

class NavigationMenu extends StatelessWidget {
  const NavigationMenu({
    required this.items,
    required this.current,
    this.onNavigate,
    this.state = CommerceFixture.defaultState,
    super.key,
  });
  final List<String> items;
  final String current;
  final ValueChanged<String>? onNavigate;
  final CommerceFixture state;

  @override
  Widget build(BuildContext context) {
    final disabled = state == CommerceFixture.disabled;
    return Semantics(
      label: 'Primary navigation',
      child: Wrap(
        spacing: AgencySpacing.sm,
        children: [
          for (final item in items)
            TextButton(
              onPressed: disabled || onNavigate == null ? null : () => onNavigate!(item),
              child: Text(item, style: item == current ? AgencyText.label.copyWith(fontWeight: FontWeight.w700) : AgencyText.label),
            ),
        ],
      ),
    );
  }
}

class FormSection extends StatelessWidget {
  const FormSection({
    required this.label,
    required this.value,
    this.helper,
    this.error,
    this.onChanged,
    this.state = CommerceFixture.defaultState,
    super.key,
  });
  final String label;
  final String value;
  final String? helper;
  final String? error;
  final ValueChanged<String>? onChanged;
  final CommerceFixture state;

  @override
  Widget build(BuildContext context) {
    final disabled = state == CommerceFixture.disabled;
    final effectiveError = state == CommerceFixture.validationError ? (error ?? 'Check this value') : error;
    return TextFormField(
      initialValue: value,
      enabled: !disabled,
      onChanged: onChanged,
      decoration: InputDecoration(
        labelText: label,
        helperText: helper,
        errorText: effectiveError,
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
