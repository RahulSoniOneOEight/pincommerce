import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prototype_app/main.dart';

void main() {
  testWidgets('prototype renders expanded reference retail experience', (tester) async {
    await tester.pumpWidget(const PrototypeApp());

    expect(find.text('Reference Retail · Direction A'), findsOneWidget);
    expect(find.text('Reference Product A'), findsOneWidget);
    expect(find.textContaining('Available credit'), findsOneWidget);
    expect(find.byType(DropdownButton<String>), findsNWidgets(2));
  });
}
