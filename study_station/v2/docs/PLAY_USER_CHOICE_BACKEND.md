# India user-choice backend foundation (not enabled)

The Google Play app must obtain an SDK UserChoiceBillingListener token after an
explicit purchase gesture. A web platform flag never enables a Play checkout.

`POST /api/v1/payments/google/alternative/start` accepts only
`external_transaction_token`, `plan_id`, `product_id`, `base_plan_id`, `country_code`.
It returns a 15-minute opaque `choice_id` and same-origin `checkout_url`.
The URL is not authentication. The signed-in account namespace must match at
checkout. `GET /api/v1/payments/google/alternative/checkout?choice_id=...` returns
only enabled status, choice ID, plan, valid states and expiry for its owner.
`POST /api/v1/payments/payu/orders` accepts optional `play_choice_id`
and `billing_state` (Google's India administrative-area enumeration). Existing
website and direct APK orders do not use these fields. Checkout consumes a choice
once in the same writer transaction that inserts the PayU order.

Enable only after all external setup and end-to-end testing:

- Existing Google Billing and website PayU credentials must be ready.
- `SS_PLAY_UCB_ENABLED=1` and `SS_PLAY_UCB_ENROLLED_IN=1` are explicit gates.
- `SS_PLAY_UCB_TAX_BPS` must be merchant/accountant approved; it has no default.
  Prices are tax-inclusive and remain server-owned ₹9/₹51. Zero is permitted only
  when the merchant explicitly confirms no applicable tax.
- Validate PayU's verified `addedon` completion semantics/time zone with the
  merchant before enabling. There is no default zone or assumed completion time:
  `SS_PLAY_UCB_CAPTURE_TIME_CONFIRMED=1`,
  `SS_PLAY_UCB_CAPTURE_TIME_SEMANTICS_CONFIRMED=1`,
  `SS_PLAY_UCB_CAPTURE_TIME_FIELD=addedon`, and a confirmed
  `SS_PLAY_UCB_PROVIDER_UTC_OFFSET` such as `+05:30` are required. A documented
  initiation timestamp alone does not justify confirming completion semantics.
- Install a five-minute privileged job running `python -m app.play_choice --apply`.
  Alert on `report_unavailable` and `deadline_alert` (20 hours after capture).
  The job reports only existing S2S-verified captured orders. It never charges or
  requests a refund. Google IDs contain only opaque hashes; SDK tokens use the
  existing external Fernet key and are never printed.
- Refund time comes from verified SUCCESS rows' `success_at`, never inquiry time
  or `RefundCreationDate`. Missing, malformed or implausible completion times
  fail closed and alert. Validate partial-refund rounding against provider and
  Google test records before production.
- Account deletion erases account linkage and unused choices, while retaining
  only opaque provider IDs/bindings, encrypted SDK token, keyed account-binding
  digest, amounts, tax state and report state for outstanding obligations. This
  requires a separately approved financial-retention policy, reflected publicly,
  before setting `SS_PLAY_UCB_RETENTION_APPROVED=1` and an explicit
  `SS_PLAY_UCB_RETENTION_DAYS`. No exception to the prior 14-day policy has been
  approved yet. Detached snapshots are purged at their explicit deadline; a
  report still outstanding then raises `retention_deadline_alert`.

Reports use a deterministic externalTransactionId, GET before CREATE, prepaid
subscription payloads, India tax address and exact INR micro amounts. A lost
CREATE response retries the same ID. Refund retries GET Google's current balance
before POST, then verify the resulting balance; original entitlement revocation
remains PayU reconciliation's responsibility.

Primary references:

Operator decision 23 October 2026: GST rate is unknown, and post-deletion payment
reporting retention was declined. Do not enable UCB. Without retention approval,
account deletion removes the entire choice/report record; no detached snapshot
is retained. The approved website checkout remains a separate existing flow.

- https://developer.android.com/google/play/billing/alternative/alternative-billing-with-user-choice-in-app
- https://developers.google.com/android-publisher/api-ref/rest/v3/externaltransactions
- https://developers.google.com/android-publisher/api-ref/rest/v3/externaltransactions/createexternaltransaction
- https://developers.google.com/android-publisher/api-ref/rest/v3/externaltransactions/refundexternaltransaction
- https://docs.payu.in/reference/verify_payment_api
- https://docs.payu.in/reference/get_all_refunds_from_transaction_ids_api
