# Data safety working sheet

## Console entry on 22 October 2026

The Play-variant form was completed and saved for review (not public approval).
Collection: name, email, user IDs, purchase history, other in-app messages,
app interactions, other user-generated content, and device/other IDs. Email is
processed ephemerally for Google authentication; it is optional because password
accounts do not require email. Names, user IDs, app interactions and device IDs
are required; purchases, messages and uploaded/shared work are user-selected.
No advertising/marketing purpose was selected. App interactions include analytics
for service observation and personalization for learning; identity/access records
include account management and fraud prevention as applicable.

Sharing exemptions applied to instructed hosting/service processing and explicit
user-directed classroom/sharing actions under the linked Google definitions;
local-only notebooks are excluded from off-device collection. The Play variant
currently suppresses PayU and Drive. Enabling Play alternative checkout or Drive
requires rechecking this form, including phone/contact handling and recipients.
HTTPS in transit, account deletion URL and privacy/data-control URL were entered.
No independent security-review or NPCI badge was claimed.

Source review dated 2026-10-19. Declarations cover the app's controlled WebView, backend and SDKs, not just Kotlin permissions. Do not select “no data collected”: online progress, identity and deliberately shared work leave the device. Final answers require the exact artifact, deployed settings, traffic inspection and operator review.

## Data inventory and proposed mapping

| Data path | Actual source behavior | Proposed Play type / purpose | Required review |
|---|---|---|---|
| Google identity | `app/google_auth.py` validates email and identity claims transiently; persists immutable subject via `google_auth_models.py` and display name/random account username via ClassroomAccount. No Google password or long-lived Google token retained. | Personal info: name, email address, user IDs. Account management, app functionality, fraud prevention/security. Email handling is transient; subject/name persist. | Check ephemeral-processing answers precisely. Identity collection optional only if all users can use core study without signup. |
| Password account and sessions | Username, display name, password hash and expiring server session; no plain password storage. | Personal info/user IDs and authentication information as applicable to the current form; account management/security. | Verify every authentication field mapping in Console. Never disclose password hash as public user content. |
| Device-bound online study | Server models retain device identifier, submitted answers, test history, revision/progress and usage limits. | Device or other IDs; app activity/app interactions and other user-generated content as appropriate. App functionality and security. | Offline-only does not imply online study is anonymous or uncollected. Determine optionality from actual startup/request behavior; do not assume an opt-out. |
| Shared notebook/class work | ClassroomRecord stores user-selected strokes/content, groups, assignments, submissions and discussions; events and idempotency replies also contain associated data. | Other user-generated content; other in-app messages for discussions. App functionality. | Sharing/access depends on invitations, membership, link and author permissions. Drawings are not automatically photos; attachments, if added, need separate classification. |
| Private offline work | Local notebook/pages and offline progress stay in app/device storage unless explicitly exported/shared/backed up. | Local-only processing does not by itself require collection declaration. | Confirm no automatic upload by the final release. Account-scoped files may become inaccessible after account deletion. |
| Export/system share | User-selected local file/document destination or Android share target. | Assess user-initiated transfer exemption under current guidance; underlying collected content still needs collection declaration. | Do not declare every transfer absent simply because user initiated it. Inspect actual disclosure and payload. |
| Optional Drive backup | Native BackupBridge uses `drive.appdata` for user-triggered backup/restore; release flag defaults false. Local export uses document picker. Login alone requests only openid/email/profile. | When enabled, evaluate off-device backup contents and Google/service-provider/user-directed transfer rules. | Verify final build flag, real separate consent, backup contents, SDK handling and retention. No Drive promise for a disabled build. |
| Security/access logs | Server may record IP, method/path/status and abuse-prevention counters. | Device/other IDs where linkable; app interactions as applicable; fraud prevention/security. | Confirm actual server/CDN fields and rotation. Do not claim coarse location merely because IP exists if no location is derived. Remove OAuth callback query codes from every access-log layer. |
| Optional membership/daily lease (2026-10-21 addition) | Server stores opaque account namespace, 72-hour trial start/end, paid expiry and verified grant references. Optional RS256 daily proof contains namespace, issuer/audience, issue/expiry and random identifier; proof lives in private native storage. The check does not upload notebooks. | User IDs, purchase history where paid, and app interactions; account management/app functionality/fraud prevention. | Verify final feature flags and native account/time binding. It is a maximum 24-hour entitlement proof, not encrypted-content DRM. Account deletion atomically erases membership/grant rows; logout clears native proof. Core paid study requires signup when enforced, so account collection is not optional for that path. |
| Website-only PayU checkout (2026-10-21 addition) | Explicit consent sends name/email/Indian phone through Study Station to sign hosted checkout and onward to PayU; contact fields are transient and are not in the local payment ledger. Ledger stores account namespace/order/provider transaction IDs, plan/amount/currency/status/dates. Card/UPI secrets are entered on PayU. No automatic renewal. | Personal information name/email/phone; financial info purchase history, with ephemeral processing assessed for transient fields. App functionality/payment processing/security. | Separate website deployment is required; native Play UI suppresses PayU and has no external checkout promotion. Do not count an unenabled website-only path as an enabled Play payment SDK, but include every path actually reachable in the final artifact. Verify PayU recipient/service-provider and user-initiated transfer classification from current policy, not assumptions. Account deletion removes the Study Station ledger; PayU has its own retention. |
| Google Play prepaid purchases (2026-10-22 addition) | Native Billing passes a purpose-hashed opaque account identifier to Google. The server verifies the purchase token using Android Publisher SubscriptionsV2 and acknowledges only eligible verified prepaid products; Google must confirm acknowledgement. Server stores token encrypted with an external key plus token fingerprint, opaque account namespace, product/base-plan/state/expiry/verification/acknowledgement/test flags. No raw card/UPI credentials or buyer email are required by this implementation. | User IDs and financial information/purchase history as appropriate; app functionality, account management and fraud prevention/security. Token transfer for S2S verification is collection even though token is not displayed. | Google Play SDK and developer API recipient handling must be evaluated against current form guidance. Do not claim the token is anonymous, or that encryption makes it uncollected. Plans are prepaid, no automatic renewal. Localized Play product prices must be displayed. Account deletion erases local encrypted tokens and access ledger but does not perform a Google refund; recreating an account cannot automatically claim the old namespace-bound token. Verify Console setup, final Billing dependencies, actual provider traffic and test-purchase flags before declaring live. |
| AI explanation/generation | `app/ai.py` calls an external provider when configured; tutor path uses question content, while device usage budgets stay server-side. | Assess exact transmitted fields and SDK/provider terms; app functionality. | Audit all enabled AI routes and whether any user-supplied text is sent. Do not invent a user-chat collection path or assume no transfer without inspection. |

Source manifest declares INTERNET only. No ad identifier/advertising SDK was found in the reviewed implementation; final merged manifest/dependency scan must verify this. Do not claim an independent security audit or end-to-end encryption: server-readable classroom content is not E2EE.

## Form answers to resolve

1. **Collection:** Yes for the enabled online features above. WebView collection counts. Map all actual SDK behavior, including transient transfers.
2. **Sharing:** Determine recipient roles and current exemptions, including hosting/service providers, deliberate sharing and Google sign-in/backup. Do not automatically answer either “all shared” or “none shared”. Record the rationale per data type.
3. **Encryption in transit:** Proposed Yes only after verifying release cleartext is disabled and every app/server/provider path uses appropriate encrypted transport. This is not an at-rest or E2EE claim.
4. **Deletion:** In-app links and public `/delete-account` route are implemented, with sign-in and exact-username confirmation. Verify deployment. Core account and associated shared records are deleted; own classes include descendants such as student submissions. Local files, anonymous device learning data and Drive copies have separate controls/lifecycles. Do not claim account deletion erases every device record.
5. **Retention:** Decide and publish specific security-log and protected-backup retention. Repository backup script has a 14-day cleanup command, but real scheduled operation and deployment snapshots are unverified. Deletion must not silently resurrect deleted accounts from restored backups.
6. **Children:** Owner must select genuine target ages and complete relevant policy review. School-level content does not itself establish a particular intended age declaration.
7. **Ads:** Proposed No based on reviewed source, contingent on final SDK/runtime audit and monetization configuration.

## Deletion acceptance checklist

- Public deletion instructions open without login; signing in returns to deletion page.
- Preview makes own classes and other students' dependent work visible in the irreversible warning.
- No destructive request before explicit confirmation and exact username.
- Disposable account's Google identity, sessions, owned records/descendants and authored references are removed; unrelated independent records survive.
- Export warning explains local account-scoped notebook access loss. Device progress and Drive backup removal are explained separately.
- Support can handle access problems at all.chandansingh@gmail.com, with an identity-verification process decided by the operator. Never delete on the basis of an unverified email alone.

Reference: [Google Play Data safety guidance](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en), [account deletion guidance](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en). Recheck the live form before submission.
