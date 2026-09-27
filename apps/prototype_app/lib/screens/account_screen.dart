import 'package:agency_flutter_ui/agency_flutter_ui.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/b2b_providers.dart';

/// B2B account overview: credit facility + entry point into the quote flow.
class AccountScreen extends ConsumerWidget {
  const AccountScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final account = ref.watch(b2bAccountProvider);
    final quoteCount = ref.watch(quotesProvider).length;

    return Scaffold(
      appBar: AppBar(title: const Text('B2B Account')),
      body: ListView(
        padding: const EdgeInsets.all(AgencySpacing.md),
        children: <Widget>[
          Text(account.companyName, style: AgencyText.title),
          const SizedBox(height: AgencySpacing.md),
          DashboardKpi(
            label: 'Credit limit',
            value: account.creditLimit.formatted,
          ),
          const SizedBox(height: AgencySpacing.sm),
          DashboardKpi(
            label: 'Available credit',
            value: account.availableCredit.formatted,
          ),
          const SizedBox(height: AgencySpacing.lg),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.request_quote_outlined),
            title: Text('Quotes', style: AgencyText.body),
            subtitle: Text('$quoteCount request(s) for quote'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/quotes'),
          ),
          const SizedBox(height: AgencySpacing.lg),
          FilledButton.icon(
            onPressed: () => context.push('/quotes'),
            icon: const Icon(Icons.add),
            label: const Text('Request a quote'),
          ),
        ],
      ),
    );
  }
}
