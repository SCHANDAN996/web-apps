# Prepared release — 19 October 2026

Package: `com.studystation.app`; version `1.2.0`, version code `3`, target SDK 36.

Local output directory: `study_station/v2/release-artifacts/` (ignored by Git).

- `Study-Station-1.2.0.aab`: signed upload bundle, 20.44 MiB.
- `Study-Station-1.2.0.apk`: signed release APK, 20.09 MiB.
- `Study-Station-1.2.0-debug.apk`: existing debug package update, 31.11 MiB.
- `checksums.json`: exact output sizes and SHA-256 hashes.

Upload key and signing properties are outside the repository in the operator's
protected private directory. Keep a secure independent backup before publishing.
This is the upload certificate, not a Google Play App Signing certificate.

## Verified

- Android unit tests, debug APK, release APK and signed release bundle build passed.
- Bundle JAR signature verification passed. Android signing certificates are
  self-signed; Play acceptance and device delivery are still separate checks.
- Google Web OAuth client created in `study-station-511803` and configured on the
  production server; only public client ID is compiled into the app.
- Real browser Google sign-in succeeded using the operator-approved account.
  Scopes are `openid email profile`; this does not grant Drive access.
- Production `/privacy` and `/delete-account` return HTTP 200. Account deletion
  was tested only against isolated test accounts, never the operator's live account.
- Immutable local account namespaces and retained numeric ID allocation prevent
  deleted account IDs exposing private notebooks to newly created accounts.
- Google, deletion, notebook isolation and color-panel browser tests passed.
- Full Python run initially passed 278 tests; four generated-shell failures were
  resolved and the six shell tests passed afterward. Final namespace tests passed.
  Two Windows symlink privilege failures remain environment-blocked.
- Production nginx/rsyslog validation and synthetic redaction probes passed;
  nginx and Uvicorn retain useful request metadata without callback queries.

## Remaining gates

1. Play Console app creation declarations require the operator's confirmation.
   Prepared form: Study Station, `com.studystation.app`, Hindi, App, Free.
2. Register the actual Play App Signing certificate's SHA-1 with the Android
   OAuth client and its SHA-256 for verified App Links. Do not substitute upload
   certificate fingerprints for Play's signing certificate.
3. Native Google sign-in and final color-panel acceptance on an actual phone;
   phone is currently unavailable. Browser OAuth success does not prove native flow.
4. Complete the policy, content rights, audience, moderation and retention gates
   listed in README.md and data-safety.md before submission.
5. Upload to a testing track, inspect Play checks, and verify delivered builds.
   No public publishing has been performed.
