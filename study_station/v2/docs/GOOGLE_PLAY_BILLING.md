# Google Play prepaid billing — implementation and activation checklist

No charges or live Google purchases were performed while implementing this module.
Google billing remains disabled unless PLAY_BILLING_ENABLED=1 and both external
credential/encryption files exist. Website PayU and Google entitlements are separate.

## Required operator/Console setup

1. Enable Google Play Android Developer API in the existing Google Cloud project.
2. Create/use a dedicated service account, then invite its email in Play Console
   Users & permissions with access to Study Station only. Official Billing API rights:
   **View financial data, orders, and cancellation survey responses** and **Manage
   orders and subscriptions**. Do not grant unrelated app release/admin permissions.
3. Save its JSON on the server outside the repository, readable only by the service
   account/root. Set PLAY_BILLING_SERVICE_ACCOUNT_FILE to its absolute path.
4. Generate a separate Fernet key (cryptography.Fernet.generate_key), store it in a
   protected file outside the repo, set PLAY_BILLING_TOKEN_KEY_FILE. Do not substitute
   the Google client secret or RSA offline-lease key. Back up the encryption key
   securely; losing it prevents existing-token reconciliation. Do not rotate it
   without re-encrypting the stored tokens first.
5. Configure and activate subscriptions for package com.studystation.app:

   | App plan | Product ID | Base plan ID | Type | Intended India price |
   |---|---|---|---|---|
   | monthly | study_station_monthly | monthly-prepaid | prepaid one calendar month | INR9 |
   | yearly | study_station_yearly | yearly-prepaid | prepaid one calendar year | INR51 |

   Console validates allowed prices/regions; these prices must not be claimed live
   before Console accepts and activates them. Native UI displays ProductDetails'
   localized price, never substitutes the website's INR label for a Google price.
   Auto-renewing base plans are deliberately rejected by this implementation.
6. Upload the Billing-enabled AAB, activate an appropriate test track, configure
   license testers, and install through Google Play under an eligible tester account.
   Set PLAY_BILLING_ALLOW_TEST=1 only for deliberately authorized test handling.
7. Test purchase success, pending, cancellation, repeat verification, restore,
   account switching, acknowledgement failure/retry, refund/revocation and offline
   lease expiration before enabling live billing. Do not charge a real card as a test.
8. Configure authenticated RTDN/Pub/Sub processing or operational reconciliation
   before production scaling. The present server rechecks stale Google purchases
   during membership/status, protected server access and offline lease requests.

## Native/server contract

GET /api/v1/payments/google/config requires the existing signed-in session and returns
enabled, package_name, auto_renew=false, products with plan_id/product_id/base_plan_id,
and a 64-hex obfuscated_account_id. Native BillingFlowParams must pass that exact ID
through setObfuscatedAccountId. It is SHA256 of a purpose prefix and opaque random
account namespace; neither email nor raw account identity is sent in that field.

POST /api/v1/payments/google/verify accepts ONLY JSON {purchase_token:string}.
It requires the same session and same-origin JSON rules. Native sends only PURCHASED
tokens, not pending purchases. Server requests Google's purchases.subscriptionsv2.get
for the fixed application package and validates account binding, exact product/base
plan, prepaid type, supported state and authoritative expiry. Client product IDs,
prices, purchase states, dates and "paid" booleans cannot grant anything.

Verified tokens are encrypted at rest with the external Fernet key; their SHA256
fingerprint is a unique key bound to one account namespace. A second account cannot
reassign the token. For a purchase not yet acknowledged, the backend acknowledges,
then fetches Google's state again; it grants access only after Google confirms ACKED.
Failures remain retryable without adding time. A repeat token refreshes the same
record using Google's exact expiry; it never stacks fictitious extra calendar months.

Response: {verified,entitled,state,acknowledged,valid_until,plan_id,auto_renew:false}.
No raw token or provider response is returned/logged. Google service errors are
generic 503 responses. A pending/paused/on-hold/expired/unsupported state never
grants; active or canceled prepaid subscriptions retain access only until Google's
future expiry. Prepaid grace-period data is rejected as non-entitled.

## Entitlement isolation and lifecycle

membership.paid_access_until combines independent website paid_until with fresh,
acknowledged PlayPurchase expiry. Google refund/expiry cannot erase an unrelated
PayU year; PayU revocation recomputes only its own non-revoked grant ledger.
No Google purchase is copied into flat website paid_until. Status/server guards/
signed-lease issuance refresh Google records older than 15 minutes. Stale cache
without successful verification does not authorize new access.

A previously issued offline lease can remain usable until its signed expiry,
at most 24h after issue and never beyond its entitlement end. Daily offline checking
does not promise immediate offline revocation after refunds. Existing public APK
assets are not encrypted DRM.

Deleting the account removes its encrypted purchase tokens and local entitlement
rows; this does not itself perform a Google Play refund. A recreated account has a
different namespace and cannot silently claim the old token. The account deletion
disclosure/support flow must explain paid-access consequences before removal.

## Official references reviewed 22 October 2026

- [Play Developer API setup and service-account permissions](https://developers.google.com/android-publisher/getting_started)
- [SubscriptionsV2 authoritative purchase fields](https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2)
- [Backend security and account obfuscation](https://developer.android.com/google/play/billing/security)
- [Subscription lifecycle and entitlement changes](https://developer.android.com/google/play/billing/lifecycle/subscriptions)
- [Billing integration and acknowledgement](https://developer.android.com/google/play/billing/integrate)
