/// Static runtime configuration for the PinCommerce storefront.
///
/// Values are supplied at build time via `--dart-define` and fall back to
/// localhost defaults that match a local Medusa instance.
///
/// Example:
/// ```sh
/// flutter run \
///   --dart-define=MEDUSA_BASE_URL=https://medusa.example.com \
///   --dart-define=MEDUSA_PUBLISHABLE_KEY=pk_live_xxx
/// ```
class AppConfig {
  const AppConfig._();

  static const String medusaBaseUrl = String.fromEnvironment(
    'MEDUSA_BASE_URL',
    defaultValue: 'http://localhost:9000',
  );

  static const String medusaPublishableKey = String.fromEnvironment(
    'MEDUSA_PUBLISHABLE_KEY',
    defaultValue: 'pk_test_demo',
  );
}
