# Membership foundation

## Current behavior and integration

`main.py` imports membership and PayU models/routers before schema initialization.
The bilingual `/membership` page is linked from Home, settings and classroom account.
Its authenticated panel loads fresh status; an unauthenticated visitor gets a login link.
`SS.initPage` calls `SSMembershipInit` after navigation swaps. No token or entitlement
is persisted in localStorage. Payments are shown only when the separate website
PayU config is enabled, and native app bridges suppress that checkout completely.

`MEMBERSHIP_ENABLED=0` is the default: UI hidden, all existing access preserved,
activation denied. `1` exposes explicit activation. GET status is read-only.
POST start accepts ONLY JSON `{"confirm":true}`, requires the existing session,
checks same-origin, and grants exactly 72 hours by server UTC. Concurrent retries,
logout and login cannot restart it. Existing users are not charged against their
historical signup date. The screen clearly says there is no automatic charge.

Server-owned advertised plans: monthly INR9 (900 paise), yearly INR51 (5100 paise),
calendar month/year terms. No auto-renew mandate. Website checkout explicitly asks
for name/email/Indian phone and PayU sharing consent. Only exact secure.payu.in and
test.payu.in hosted form destinations are allowed; CSP permits these on the enabled
website membership page only. These contact fields are not stored by Study Station.
PayU's separate module grants only after its signed callback AND server-to-server
verification. `grant_verified_payment` is internal, never an API, and writes an
idempotent MembershipGrant ledger in the caller's serialized transaction. Calendar
terms clamp month ends (Jan31 -> Feb28/29), rather than silently becoming 30days.

## Important boundaries

With MEMBERSHIP_ENABLED=1, server middleware gates /books*, /practice*, /mock*,
/questions*, /revise and GET /api/v1/revise; POST new practice/mock, question practice/
explain, and retry-wrong. Denied APIs return 401 sign_in_required or 402
membership_required JSON. HTML redirects to /membership with only the actual safe
path in return_to. Existing attempt answer/finish/results, progress, personal
notebooks, account controls, backup/restore and public answer-free /q previews remain
accessible. The guard is off by default. It is not DRM for raw public APK assets.

Optional GET /api/v1/membership/lease requires an active trial/paid entitlement and
MEMBERSHIP_LEASE_PRIVATE_KEY_FILE referencing an external RSA2048+ PEM key. It signs
RS256 JWT claims iss=StudyStation, aud=com.studystation.app, namespace, iat, exp, jti.
The lease expires at the earlier of 24h and the entitlement end. Signing errors fail
closed with a generic 503, no key data in responses. Native code must verify signature,
audience/issuer/account namespace and anchor elapsed-time across the trusted boot;
reboot requires an online check. Native bridge code is owned by the Android agent.
membership.js renews on activation and account-scope change; logout/delete clears
the native lease. A scope-generation fence prevents late responses authorizing an
account that has already changed.

Membership rows are keyed by opaque permanent storage namespace, so account ID
reuse cannot transfer an entitlement. Account deletion removes Membership,
MembershipGrant and PayUOrder rows by namespace in its existing atomic transaction.
No personal anti-fraud
fingerprints are retained. Accordingly deleting/recreating an account CAN receive
another trial; this is an explicit unresolved abuse boundary, not solved by login
session persistence. Blocking recreation requires an approved retention/privacy
policy and keyed Google subject reservation (plus a policy for password-only users),
not plain email hashes or device fingerprinting. Do not claim recreation prevention.
No persistent Google-sub tombstone was added without that policy decision.
