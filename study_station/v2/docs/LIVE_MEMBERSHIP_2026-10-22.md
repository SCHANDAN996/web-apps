# Membership release — 22 October 2026

## Update — 23 October 2026

- Organization account: no new-personal-account 12-tester/14-day gate applies.
  Internal testing was optional verification, not a production requirement.
- Bundle 1.2.0/code 3 is Active and available to the configured internal tester.
  Production is separately being prepared; no public release claimed.
- Android Play OAuth client created with owner action-time approval:
  `1040204190388-8sso19hsku9kkkgq06v8as2ff3lpr807.apps.googleusercontent.com`.
  Package `com.studystation.app`, Play SHA1
  `75:44:DD:39:2B:91:50:DE:D6:C6:49:07:B6:BA:81:E6:1D:36:21:A1`.
- OAuth website/privacy branding completed, audience now In production (basic
  sign-in; no Drive consent enabled). Real Play-installed login remains untested.
- Production and direct-signing App Links certificates deployed; live endpoint
  HTTP200 confirmed. Existing debug association retained.
- Reviewer access instructions updated for actual paid membership/daily lease.
  Advertising ID declaration saved No after merged-manifest inspection.
- New dormant India user-choice code: Android31tests, server39related tests,
  followed by11choice tests including declined-retention behavior; browser
  Google billing and choice checkout mocks passed. This new code is local and
  not in the uploaded code3 artifact or enabled on production.
- Owner does not know GST rate and declined post-deletion reporting retention.
  Keep UCB OFF; account deletion must not retain unapproved reporting snapshots.
  Do not assume a tax rate or set merchant timestamp confirmation flags.
- No phone attached on latest ADB check. No new physical-device test claimed.

## Live website

https://studystation.ebookcart.in/membership

- Explicit signed-in trial activation: 72 hours, server time, no payment needed.
- Production PayU hosted checkout: INR9 per calendar month / INR51 per calendar year.
- One-time purchases; no automatic renewals or charges.
- User-approved refund policy: duplicate payments or access not provided after payment;
  Google Play rules and statutory rights remain applicable.
- Paid access requires verified server-to-server provider confirmation.
- Five-minute operational reconciliation timer is active; successful full refunds
  revoke only their own access grant. Chargebacks require an operator-verified case.
- RSA daily offline lease endpoint is active. The updated APK verifies its signature,
  account namespace and monotonic expiry. Reboot requires another online check.
- Normal account deletion also removes membership/payment records.
- Review account has an explicitly labelled, non-financial operator grant through
  22 October 2027. No provider payment was fabricated for that grant.

Deployment backup: `/root/ss-backups/membership-20261022-081010`.
The existing retention timer expires this protected backup under the 14-day policy.
Private credentials and signing material are outside the repository.
The ebookcart application's payment flow was not changed.

## Verified

- Windows full suite: 402 passed; two symlink-privilege failures.
- Linux targeted suite: 107 passed, including both Windows-blocked checks.
- Android unit tests before the last logout hook: 24 passed.
- Browser billing mocks: success, pending, cancellation, restoration, account change.
- Native UI hides PayU, including older WebViews before bridge injection.
- Browser Home → membership uses a full document with the required form-action CSP.
- Production smoke: exact prices/configuration, 72-hour non-restarting trial,
  RSA-verified lease no longer than 24 hours, book access, forged callback rejected.
- Disposable production QA account was deleted after its checks.
- Mobile production page: checkout and refund text visible, no horizontal overflow.

No live provider order, charge, refund or real-money test was created by the agent.
The actual customer/provider/bank round trip still requires a user-performed payment.

## Remaining before Play billing/public release

The owner subsequently selected PayU for both website and app. A separate
direct-distribution APK opens the same hosted PayU website in the phone browser;
the user must sign in with the same Study Station account. No session token is
transferred in a link. The Play variant must keep external checkout hidden until
India user-choice billing enrollment, the required Google alternative and external
transaction reporting are implemented and approved. A direct APK is not a Play AAB.

- Release APK/AAB compilation and signature verification completed. Play bundle
  1.2.0/code 3 uploaded and saved in an internal-testing draft on 22 October;
  Console accepted the bundle and reports a 20.8 MB new install. Not published.
- Enable the Android Publisher API, configure a narrowly scoped service account,
  securely install its credentials and a separate token encryption key.
- Create/activate the documented prepaid products/base plans and validate prices.
- Play-installed tester purchase, acknowledgement, restoration and refund checks.
- Update private review instructions for the new sign-in/trial/access flow.
- Finish store listing, content rating, Data Safety, Play App Signing and release.
- Register Play signing certificate for Android Google login and App Links.

Google Play billing remains disabled until these prerequisites are verified.
The Chrome extension connection recovered. Default store listing is now ready to
send for review: Hindi, English India and English US descriptions, SS icon,
1024x500 feature graphic and four real-device screenshots were saved.
Content rating is now IARC Completed (owner explicitly accepted IARC terms).
Data Safety is saved for review. The dashboard's initial setup list is complete.
India user-choice billing terms were explicitly approved by the owner and
accepted in Console. Organization and support/dispute email were confirmed;
enrollment has reached Set up invoicing, not confirmed complete. Google fees and
24-hour external-transaction reporting still apply. No public release is claimed.

Real-device checks on the connected V2553 phone passed: non-destructive debug
update, Home, membership gate, external PayU entry, signed daily proof, and bundled
chapter rendering with that app WebView's network disabled. Network was restored.
Review account was signed out and its native lease cleared afterwards. No real
learner progress was reset. Screenshots captured by ADB on 22 October show Home,
book library, reader and mock selection; no learner names or submitted results.
Fresh production-certificate Google login and Play-delivered purchases remain
untested. No live provider charge or public Play release is claimed.
