# Google Drive backup setup

Cloud project created for this app: `study-station-511803` (Study Station).
The project exists and Google Drive API is enabled (confirmed in Console).
OAuth branding is configured as Study Station / External testing with the project
owner's support and notification email (Console reports configuration created).
The Android debug OAuth client was created on 16 October 2026 after owner approval.
No learner Drive permission has been granted; physical consent/upload/restore testing remains pending.

Registered debug client:
- Package: `com.studystation.app.debug`
- Certificate SHA-1: `FD:8B:87:92:B8:4A:92:1C:99:2E:C2:A7:CD:FC:16:FD:BD:F0:CB:2E`
- Name: Study Station Android debug
- Client ID: `1040204190388-084kk93i9msui4tbfsus0jp91mnv3412.apps.googleusercontent.com` (public application identifier, not a secret)
- Clients: https://console.cloud.google.com/auth/clients?project=study-station-511803

Console Data Access is saved with **only** `drive.appdata` in non-sensitive scopes;
sensitive and restricted scopes are empty. Audience remains External / Testing.
On 17 October 2026 the owner-provided test account was added (one test user).
Physical Android authorization and a native Drive upload succeeded with disposable
local QA progress and rough work. Fresh-learner native restore remains unverified:
the USB device became offline during that step. No production learner data was reset.
Do not publish or add unrelated accounts automatically.

## Configure the project

1. Google Drive API is enabled at https://console.cloud.google.com/apis/library/drive.googleapis.com?project=study-station-511803.
2. In Google Auth Platform, configure app branding, support email and developer contact using the project owner's details. Select External audience for public learners. Keep Testing while testing; add only intended test accounts.
3. Request only `https://www.googleapis.com/auth/drive.appdata`. Do not request full Drive access. This folder is hidden from ordinary Drive file browsing; users can manage app data in Drive settings.
4. Create an Android OAuth client for the exact installed package and signing certificate SHA-1:
   - Debug: `com.studystation.app.debug`, debug certificate SHA-1 from `gradlew.bat signingReport`.
   - Release: `com.studystation.app`, actual release signing certificate. When distributed by Play App Signing use the **app signing** SHA-1 shown in Play Console.
5. Do not put a client secret, service account key or Google account password in this repository. The Android AuthorizationClient flow uses the registered package/certificate, and does not require a server client secret.
6. Only after registration is verified, build the matching app with `-Pss.googleDriveEnabled=true`. Default builds leave Drive unavailable and retain local file backup/restore.

## Validate before enabling for learners

- Use a separate test learner. Save progress plus rough work to Drive, then restore into a fresh test learner. Confirm mock answers, reading history and rough work survive.
- Cancel Google consent and the file picker: no progress changes and no stuck buttons.
- Test missing backup, network failure, expired authorization, repeated restore and invalid/oversized files.
- Verify permission is limited to app data. Tokens must never appear in JavaScript, server requests, backup JSON or logs.
- A successful unit test or APK build does not prove that Google OAuth registration works. Keep Drive disabled until a real device upload/download passes.

Local backup files contain study history and rough work. They exclude learner authentication tokens, recovery codes, question solutions, AI budgets and admin data. Existing study progress remains on the application server; this feature adds portable backups, and does not migrate the entire progress system off the server.

References:
- https://developer.android.com/identity/authorization
- https://developers.google.com/workspace/drive/api/guides/appdata
- https://developers.google.com/android/guides/client-auth
