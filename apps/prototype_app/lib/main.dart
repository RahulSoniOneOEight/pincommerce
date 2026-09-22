import 'package:agency_flutter_ui/agency_flutter_ui.dart';
import 'package:flutter/material.dart';

void main() => runApp(const PrototypeApp());

const referenceScreens = <String>[
  'home','category','search','search-results','product-list','product-detail',
  'cart','checkout','address','delivery','payment','order-confirmation','orders',
  'order-detail','return-request','return-status','rfq','quote-detail','account',
  'approval-status','support','profile','inventory'
];

const referenceStates = <String>[
  'default','loading','empty','failure','out-of-stock','no-results','coupon-valid',
  'coupon-invalid','payment-failed','order-success','approval-pending','approved',
  'rejected','refunded','available','partially-used','limit-exceeded','draft','submitted','in-stock','low-stock'
];

class PrototypeApp extends StatelessWidget {
  const PrototypeApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'PinCommerce Reference Retail',
    theme: AgencyTheme.light(),
    home: const PrototypeHomePage(),
  );
}

class PrototypeHomePage extends StatefulWidget {
  const PrototypeHomePage({super.key});
  @override
  State<PrototypeHomePage> createState() => _PrototypeHomePageState();
}

class _PrototypeHomePageState extends State<PrototypeHomePage> {
  String screen = 'home';
  String state = 'default';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reference Retail · Direction A')),
      body: ListView(
        padding: const EdgeInsets.all(AgencySpacing.lg),
        children: [
          const Text('CUST-B2B-014 · Available credit ₹1,85,000', style: AgencyText.body),
          const SizedBox(height: AgencySpacing.md),
          DropdownButton<String>(
            value: screen,
            isExpanded: true,
            items: referenceScreens.map((x) => DropdownMenuItem(value: x, child: Text(x))).toList(),
            onChanged: (v) => setState(() => screen = v ?? screen),
          ),
          DropdownButton<String>(
            value: state,
            isExpanded: true,
            items: referenceStates.map((x) => DropdownMenuItem(value: x, child: Text(x))).toList(),
            onChanged: (v) => setState(() => state = v ?? state),
          ),
          const SizedBox(height: AgencySpacing.md),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AgencySpacing.md),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(screen, style: AgencyText.title),
                const SizedBox(height: AgencySpacing.sm),
                Text('State: $state', style: AgencyText.body),
                const Text('Demo orders: ORD-1001 success · ORD-1002 payment failed · ORD-1003 approval pending'),
                const Text('Returns, credit, fulfilment and exception states are selectable above.'),
              ]),
            ),
          ),
          const ProductCard(title: 'Reference Product A', priceLabel: '₹1,999'),
        ],
      ),
    );
  }
}
