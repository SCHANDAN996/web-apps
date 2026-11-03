# Android release preparation

Production package: `com.studystation.app`; debug package: `com.studystation.app.debug`.
Target SDK 36; minimum SDK 26. Default next version is 1.2.0 (code 3).

## Private signing configuration

Keep the upload keystore and the properties file outside this repository. Do not put passwords in commands, logs, source, or the Play listing.

Set these non-secret paths/values in ignored `android/local.properties`:

```
ss.releaseUrl=https://studystation.ebookcart.in
ss.googleWebClientId=YOUR_WEB_CLIENT_ID.apps.googleusercontent.com
ss.signingProperties=C:/private/study-station-upload.properties
ss.versionCode=3
ss.versionName=1.2.0
```

The external properties file contains `storeFile` (absolute path), `storePassword`, `keyAlias`, and `keyPassword`. Back up the private upload key securely. Release builds fail if signing is missing or the root URL is not HTTPS. A debug key must never be used as the production upload key.

From the v2 directory, after generating the public pack and app shell:

```
android/gradlew.bat -p android testDebugUnitTest
android/gradlew.bat -p android bundleRelease
```

The signed bundle is `android/app/build/outputs/bundle/release/app-release.aab`. Verify its certificate and increasing version before uploading to an internal testing track. Do not uninstall the debug package when installing production: their private local study data are separate. Export and explicitly restore user data if a user wants migration.

## Google account setup

The native chooser uses Android Credential Manager, not a Google login page inside WebView. Its ID token is verified by the app server; no Drive permission is requested by signup.

Use the same **Web application client ID** for backend `GOOGLE_WEB_CLIENT_ID` and native `ss.googleWebClientId`. Configure Android OAuth clients separately for each installed signing identity:

- Debug package + debug certificate SHA-1, for development only.
- Production package + upload certificate SHA-1, for locally installed upload-signed testing if needed.
- Production package + **Play App Signing certificate SHA-1**, for Play-delivered APKs. This certificate differs from the upload certificate.

After enabling Play App Signing, put the Play signing certificate SHA-256 in the production domain's `assetlinks.json`; retain only deliberately supported package/certificate combinations. Test signup and question App Links from an actual Play internal-test installation. A successful debug install does not prove production authentication or domain verification.

Current API contract: `StudyStationAuth.configured()`; `signIn(serverNonce)` returns `{ok:true,idToken}` or `{ok:false,error}`; `signOut()` clears the provider's credential state. Tokens stay in memory only. A valid fresh nonce from `/api/v1/classroom/google/challenge` must be prepared before the user taps Google signup. Backend session/account checks remain authoritative.

Official guidance:
- https://developer.android.com/identity/sign-in/credential-manager-siwg-implementation
- https://developer.android.com/studio/publish/app-signing
- https://developer.android.com/studio/publish/upload-bundle

Store listing, privacy/data safety/account deletion, content rights, app access instructions, rating, and Play testing/verification requirements must be completed against the actual implementation before production submission. No Play upload or publication is performed by these build settings.
# Play prepaid billing

## Separate website APK

`assembleDirectRelease` creates the signed APK for direct website distribution. It uses the same
package and external upload signing configuration as the existing direct APK, so an update can
preserve local progress when its signing certificate matches. `DIRECT_PAYU_ALLOWED` is true only
in this variant; `StudyStationMembership.allowPayu()` exposes that immutable presentation setting
to the trusted origin. The normal `release` and `debug` variants return false.
`assembleDirectDebug` is a separate QA variant with the existing debug package and debug signing
certificate, preserving that installed app's data when updated. It also enables the direct channel;
it is not a distribution release. AAB creation is blocked for both direct variants.

The direct variant does not install the Play Billing bridge and removes the Play billing manifest
permission. All membership decisions still come from server-verified payment and signed leases;
the presentation flag grants no access. The app retains its usual `StudyStationApp` user agent.
The direct app's explicit payment button calls `StudyStationMembership.openPayuWebsite()`.
Both JavaScript and native code require a current trusted main-frame user gesture, then open only
the fixed HTTPS `/membership` URL in the phone browser. No session or account credentials are
transferred; the user signs into the same account in that browser. On returning to the app,
`ss-payu-return` asks the UI to refresh server status and its signed lease. The native app does not
embed the PayU checkout or grant access merely because the external browser was opened.

Direct AAB creation is blocked at task-graph validation, including packaging/signing bundle tasks.
Do not upload this direct APK to Google Play. Build the normal `bundleRelease` for the Play channel;
Google Play payment eligibility and activation must be handled separately before enabling checkout.

Distribution filenames must identify the channel clearly, for example
`Study-Station-Direct-PayU-1.2.0.apk`. Google sign-in on that APK additionally requires the matching
Android signing-certificate OAuth registration; successful compilation does not verify that setup.

The native app uses Google Play Billing Library 9.1.0. The only selectable subscriptions are
`study_station_monthly` / `monthly-prepaid` and `study_station_yearly` / `yearly-prepaid`.
The bridge rejects recurring pricing phases, introductory offers, and a different base plan.
The screen displays the localized price returned by Play rather than a hard-coded amount.

The server must enable `/api/v1/payments/google/config` and supply the signed-in account's
opaque billing identifier. A purchase must be verified and acknowledged by the backend before
the app renews its signed offline membership lease. Pending and cancelled payments do not grant
access. The Restore button queries existing Play purchases and sends purchased tokens through
the same verification path; the client does not acknowledge or consume subscriptions itself.

Configure and activate both prepaid plans and the backend Google Play Developer API credentials
before enabling checkout. Use licensed testers and Play test tracks for acceptance; building an
APK or passing mocked tests does not prove that checkout or real settlement is operational.
No checkout is launched automatically during startup or product discovery.

Official integration reference: https://developer.android.com/google/play/billing/integrate
Release reference: https://developer.android.com/google/play/billing/release-notes

