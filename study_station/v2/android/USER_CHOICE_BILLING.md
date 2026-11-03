# India user-choice billing (Play distribution)

The existing Google prepaid products stay the entry point. There is no standalone
PayU button in the Play build. `StudyStationBilling.purchase(planId)` invokes
Google's purchase flow and lets Google render the billing choice.

Configuration from `/api/v1/payments/google/config` must contain
`user_choice: {"enabled": true, "countries": ["IN"]}` to enable this integration.
Missing, malformed or disabled configuration keeps Google billing only. Before
each purchase the bridge asks `getBillingConfigAsync` for the customer's current
Play country, without caching it. Only `IN` initializes a client with
`enableUserChoiceBilling`. Country lookup failure keeps Google billing only.

After the SDK's `UserChoiceBillingListener` callback, the bridge validates the
single product, product type and offer token against the actual launched flow.
It checks the account and page generation, then resolves the original purchase
request with:

```json
{"ok":true,"alternative":{"external_transaction_token":"SDK_TOKEN","plan_id":"monthly","product_id":"study_station_monthly","base_plan_id":"monthly-prepaid","country_code":"IN"}}
```

Every purchase retires the previous SDK client before installing a new request
completion. SDK and connection callbacks carry their client generation; old
callbacks cannot consume a new page's or account's checkout context. A late
country lookup is discarded before it can replace the current client. Checkout
requests expire after three minutes; retirement also fences later callbacks.

The frontend submits that object to
`/api/v1/payments/google/alternative/start`. The backend must persist the token
with the authenticated account, enforce enrollment and India eligibility, and
return a short-lived same-origin checkout link. This callback never grants study
access. PayU server verification and Google external-transaction reporting remain
backend responsibilities. Never log tokens, put them in URLs or transfer them
to a different user after account switching.

Before enabling in production, complete Console enrollment, merchant invoicing,
service-account API access, prepaid product setup and licensed-tester checks on a
Play-installed build. Unit tests cannot establish enrollment or verify Google's
real choice screen. No real payment is needed for source tests.

Official references (checked 23 October 2026):

- https://developer.android.com/google/play/billing/alternative/alternative-billing-with-user-choice-in-app
- https://developer.android.com/reference/com/android/billingclient/api/BillingConfig
- https://developer.android.com/reference/com/android/billingclient/api/UserChoiceDetails.Product
