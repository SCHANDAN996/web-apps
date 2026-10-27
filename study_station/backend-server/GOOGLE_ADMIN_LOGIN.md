# Study Station Google Admin Login

Branch: `feature/study-station-google-admin-login`.

## Setup

1. In Google Cloud Console create a project, configure Google Auth Platform consent screen and an **OAuth 2.0 Web application** client. Add your deployed HTTPS callback address, e.g. `https://YOUR_DOMAIN/auth/callback`, to **Authorized redirect URIs**. If app is in Testing, add `all.chandansingh@gmail.com` as a test user.
2. Set the following **server-side** environment variables (never commit credentials):
   - `FLASK_SECRET_KEY`: strong random value (at least 32 random bytes).
   - `ADMIN_EMAIL=all.chandansingh@gmail.com`
   - `GOOGLE_CLIENT_ID`: Google OAuth client ID
   - `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
   - `GOOGLE_REDIRECT_URI=https://YOUR_DOMAIN/auth/callback`
   - `SESSION_COOKIE_SECURE=true` (HTTPS only; set false only for local HTTP testing).
3. Install dependencies using `pip install -r requirements.txt`, deploy backend, then visit `/auth/login`.
4. Access to routes starting with `/admin` requires successful Google login with the verified matching admin email. Use `/auth/logout` to sign out.

**Important:** The Google OAuth client credentials and deployment URL must be provided and deployed before sign-in will work. This change does not yet configure YouTube/Instagram channel authorization or publishing. Review other routes for sensitive actions before deploying publicly. Use HTTPS, secure server-side environment configuration and consider CSRF protection for admin POST forms.
