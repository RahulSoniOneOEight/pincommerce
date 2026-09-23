import 'package:agency_flutter_ui/agency_flutter_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Widget host(Widget child) => MaterialApp(theme: AgencyTheme.light(), home: Scaffold(body: child));

void main() {
  testWidgets('governed actions invoke equivalent callbacks', (tester) async {
    String? filter;
    await tester.pumpWidget(host(FilterBar(filters: const ['In stock'], onSelected: (v) => filter=v)));
    await tester.tap(find.text('In stock')); await tester.pump();
    expect(filter,'In stock');

    int? quantity;
    await tester.pumpWidget(host(B2BQuickOrder(lines: const [QuickOrderLine(sku:'SKU-1',name:'Reference Product',quantity:1)], onQuantityChanged: (_,q)=>quantity=q)));
    await tester.tap(find.byTooltip('Increase Reference Product')); await tester.pump();
    expect(quantity,2);

    String? navigation;
    await tester.pumpWidget(host(NavigationMenu(items: const ['Home','Catalog'],current:'Home',onNavigate:(v)=>navigation=v)));
    await tester.tap(find.text('Catalog')); await tester.pump();
    expect(navigation,'Catalog');

    String? value;
    await tester.pumpWidget(host(FormSection(label:'Name',value:'a',onChanged:(v)=>value=v)));
    await tester.enterText(find.byType(TextFormField),'buyer'); await tester.pump();
    expect(value,'buyer');
  });
}
