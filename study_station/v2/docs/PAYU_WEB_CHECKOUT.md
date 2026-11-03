# Study Station website payments

This is **one-time** access, not an automatically renewing subscription:
monthly INR 9.00 (900 paise), yearly INR 51.00 (5100 paise). The server owns
the plan allowlist and price. A calendar month/year is granted by membership's
internal service only after payment verification. Three-day trials belong to
the membership service and do not require payment/contact details.

## Integration

Import `app.payu_payments.router` in main before schema initialization and
include the router. Its model is additive. Account deletion must remove
`PayUOrder` rows matching the deleted account's storage namespace, in the same
transaction as membership and account removal. Do not delete somebody else's
ledger or update ebookcart's orders/endpoints.

Disabled by default. Protected server environment needs:

* `SS_PAYU_WEB_ENABLED=1`
* `SS_PAYMENT_CHANNEL=website`
* `SS_PAYU_WEB_ORIGIN`: exact HTTPS website origin, no trailing path
* `SS_PAYU_ENV=test` or `production`
* `SS_PAYU_MERCHANT_KEY`, `SS_PAYU_MERCHANT_SALT`: server-only secret values

Native Play screens must not display payment links, hosted forms or external
payment steering unless the app meets the applicable approved alternative-
billing program requirements. This release uses Google Play Billing in native
screens and PayU only in the browser website experience. A dedicated website
hostname can simplify operations but is not required: browser payment routes
may share the app's existing HTTPS origin. Native APK UI must strictly suppress
PayU UI/links. User agents, query parameters and JavaScript bridge detection are
not authorization boundaries; every API still requires account/Origin checks,
server-owned prices and authoritative provider verification. There is no client
`platform=web` override of those checks.

Existing ebookcart credentials are present in production. The account owner has
confirmed merchant approval for Study Station; code inspection alone does not
independently prove provider-dashboard approval.
No provider settings, live orders or charges were created by these tests.

## Browser API

`GET /api/v1/payments/payu/config` gives availability and public plan prices.
Signed-in website users submit JSON to `POST /api/v1/payments/payu/orders`,
with exact Origin header, `plan_id` (`monthly`/`yearly`), `name`, `email`,
Indian `phone` and explicit `contact_consent:true`. Explain before submission
that these contact details go to PayU to process payment. This service does
not persist them; it never collects card/account credentials. Submit returned
`fields` as a form to the returned allowlisted PayU `action_url`.

`GET /api/v1/payments/payu/orders/{id}` returns only the owning account's
non-sensitive order status. Never treat the form submission or browser return
as success until the ledger reports `paid`. Do not ask users to repay a pending
order. Signed callback delivery should be retried if verification is temporarily
unavailable; arrange provider-side webhook retries and reconciliation before
live operation. There is no unauthenticated client grant/reconcile endpoint.

PayU redirects/forms use `POST /payments/payu/return`; provider notification
uses `POST /payments/payu/webhook`. These isolated form endpoints are the
documented exception to JSON-only API POSTs. Both validate reverse SHA-512
with constant-time comparison, bind amount/order nonce, then independently call
PayU's verify_payment API over verified TLS. A grant requires captured success,
matching transaction ID, exact amount, product, account, plan and nonce. Domestic
hosted checkout is INR; a supplied non-INR currency is rejected. HTTP redirects
from the provider API are not followed. No raw provider payload is stored/logged.

Finalization locks the ledger and grants membership in one database transaction.
Replay cannot extend access twice; unique provider IDs prevent another order
claiming the same PayU transaction. Deleted/recreated accounts cannot inherit
payments because both account ID and random namespace must match.

## Refunds and operations

No automatic renewals, recurring mandates, refund calls or charges are issued
by this module. Publish a clear refund/contact policy before enabling checkout.
Refund/chargeback reconciliation uses the server-only operational flow below;
a client callback cannot initiate refunds or revocations. Do not silently
regrant paid orders on later replay. Suppress request-body/query logging at ingress, protect
the server environment and never copy merchant salt into APKs or public assets.

## Primary provider specifications

* https://docs.payu.in/docs/hashing-request-and-response
* https://docs.payu.in/reference/verify_payment_api
* https://docs.payu.in/docs/faqs-for-web-checkout-integration

Tests use dummy credentials and mocked verification only; no live API call.

## Scheduled reconciliation and operator cases

Install `deploy/studystation-payu-reconcile.service` and its timer after database
migration. The oneshot service runs as the restricted `studystation` user,
reads the protected environment and can write only `/var/lib/studystation`.
It runs every five minutes, bounds each batch to 50 locally known orders and
stores per-order check time/outcome with no raw provider details. Systemd
prevents overlap for the same service unit; operators must not start parallel
manual batches. CLI: `python -m app.payu_reconcile --apply --limit 50`.

Pending orders require authoritative `verify_payment` captured transaction
matching all original order bindings. The server-only inquiry can recover a
missing callback because it directly authenticates to PayU, never a browser
claim. It checks refund history before granting, so a provider inquiry/shape
error never creates new access. Paid orders are checked every six hours.
An unknown/not-found transaction remains pending; older pending inquiries
back off rather than silently losing a late captured payment.

Refund history uses documented `getAllRefundsFromTxnIds`, merchant transaction
ID as `var1`, SHA-512 general-command request hash and verified TLS. The parser
requires `Refund Details[PayuID]` rows with matching `PayuID`; it counts unique
`RequestID` entries whose `Status` is `SUCCESS`. Pending/failed refunds do not
revoke access. Successful amounts totaling the complete original price revoke
only that payment's grant, atomically with its ledger state. Partial refunds
retain access and set `partial_refund_review` for an operator decision. Provider
errors retain current paid access, set a sanitized operational warning and retry.

There is **no claim of automatic chargeback detection**: the refund endpoint
does not document a complete chargeback feed. A privileged server operator
must verify the final chargeback/full-refund against the merchant dashboard
or an authenticated provider case first. Then run:

```
python -m app.payu_reconcile --apply --revoke-order SS_<transaction> \
  --reason chargeback --evidence-reference CASE_123456 \
  --confirm-dashboard-verified
```

The case reference is saved in the local ledger. Never use a customer email,
password, provider key or full case contents as the reference. This command
only revokes the local entitlement; it never moves money, initiates a refund
or changes merchant settings. Refunds themselves are processed through the
existing protected merchant operations. The operator owns verification of the
case; an arbitrary supplied case ID alone is not independent provider proof.

Revoked grants cannot be reactivated by replaying payment callbacks. Other
remaining paid grants, including Play purchases, are recomputed separately by
the membership service. Unknown provider response structures raise an error
instead of guessing status fields or revoking unrelated grants.

Provider schema source:
https://docs.payu.in/reference/get_all_refunds_from_transaction_ids_api
