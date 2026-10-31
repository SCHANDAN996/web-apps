# Google signup / sign-in

This feature creates real Classroom accounts using Google's immutable subject ID.
An email match never merges an existing password account or a device's private work.
Sign-in asks only for `openid email profile`; Drive backup permission is separate.

## Google Cloud

Use the existing Study Station project. Complete Branding and Audience with the
actual operator contact, published privacy policy and terms. While in Testing,
add only operator-approved test users. Never publish a client secret in source,
the APK, browser JavaScript, screenshots or support messages.

Create an **OAuth Web application** client:

- Authorized origin: `https://studystation.ebookcart.in`
- Authorized redirect URI:
  `https://studystation.ebookcart.in/api/v1/classroom/google/callback`

The server reads these environment variables at runtime:

```
GOOGLE_WEB_CLIENT_ID=<web application client ID>
GOOGLE_CLIENT_SECRET=<web application secret; server only>
```

Restart the service after private environment changes. `GET
/api/v1/classroom/google/config` exposes the public client ID and readiness flags,
never the secret. Without configuration sign-in reports unavailable, never success.

## Android

Create separate **Android OAuth clients** for the package and SHA-1 of each
authorized signing certificate. Debug testing and Play App Signing certificates
are different. For Play releases register the **app signing** SHA-1 from Play
Console, not only the upload certificate. Use the same web client ID as the
Credential Manager server audience. Do not use the Android client ID as audience.

The WebView obtains a browser-bound nonce using POST `/api/v1/classroom/google/challenge`
and JSON `{}`. Native Credential Manager receives this nonce and the returned web
client ID, then returns an ID token to the same trusted WebView. The WebView posts
JSON `{ "id_token": "..." }` to `/api/v1/classroom/google/token`, retaining cookies.
OAuth consent must not run inside the embedded WebView. Browser clients use GET
`/api/v1/classroom/google/start`; standard browser OAuth uses state, PKCE and nonce.

## Validation and release checks

The backend checks Google's signature, exact configured audience, issuer, expiry,
verified-email claim and single-use nonce. The nonce expires after five minutes
and is stored server-side with an HttpOnly, SameSite=Lax browser cookie. Consumption
is a conditional SQL delete, shared safely by both server workers. Google tokens,
authorization codes and refresh tokens are not persisted. No Drive access token
is requested. Existing account sign-in is rejected until explicit sign-out.

Run `python -m pytest tests/test_google_auth.py` against the isolated test database.
These tests mock Google's signature verifier to exercise application controls;
they do not claim that Cloud credentials or a real Google consent round-trip work.
Before release test a real authorized user on the signed APK, cancellation,
sign-out, reopening and another account. Confirm private guest progress is unchanged.
Web callback access logging must omit query strings because OAuth codes arrive
as query parameters. Account deletion and privacy disclosures are release gates.

Official reference:
https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
https://developers.google.com/identity/openid-connect/openid-connect

Before enabling web sign-in, follow the mandatory safe-log deployment gate in
[deploy/OAUTH_LOGGING.md](../deploy/OAUTH_LOGGING.md). Merely changing nginx's
access log format does not protect nginx error logs.
