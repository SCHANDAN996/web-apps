# Study Station → YouTube Shorts

The existing 05:01 IST workflow renders three quiz videos. Setting `YOUTUBE_AUTO_UPLOAD=true`
adds upload to the selected channel with the generated title and description. Telegram and MP4/caption
artifacts remain available. No additional server cron or ChatGPT scheduled task is needed.

## One-time channel connection

1. In [Google Cloud Console](https://console.cloud.google.com/), create/select your project and enable
   **YouTube Data API v3**. Configure Google Auth Platform consent for your own account and create a
   **Desktop app** OAuth client. Download its client JSON outside this repository.
2. On your own laptop, from `study_station/v2`, run:

   ```sh
   python -m pip install google-auth-oauthlib
   python scripts/youtube_authorize.py /outside/repo/client_secret.json /outside/repo/youtube-secrets.json
   ```

   A browser opens for Google consent with `all.chandansingh@gmail.com` preselected as a login hint.
   Use that account and select its Study Station channel (including the correct Brand account if applicable).
   The requested scopes are `youtube.upload` and `youtube.readonly` (to verify the channel).
   Credentials are saved with owner-only permissions outside Git. Do not paste them into chat.
3. In repository **Settings → Secrets and variables → Actions**, add these **secrets** from that local file:
   `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`.
4. Add these repository **variables**:

   | Variable | Value |
   | --- | --- |
   | `YOUTUBE_CHANNEL_ID` | Exact channel ID starting with `UC` (YouTube Studio → Settings → Channel → Advanced settings) |
   | `YOUTUBE_MADE_FOR_KIDS` | `false` for general government-exam preparation; choose `true` if the actual audience is children |
   | `YOUTUBE_PRIVACY_STATUS` | `private` for the first check; then `public` for automatic public posting |
   | `YOUTUBE_AUTO_UPLOAD` | `true` to enable upload; `false` to keep generating without upload |

5. Run **Actions → Promo Shorts → Run workflow**, selecting the branch with this change, count `1`.
   Verify the channel and video in YouTube Studio. Set privacy to `public` for later uploads after checking.
   Existing private uploads are not republished by changing this variable.

Google OAuth consent apps in External/Testing status can issue refresh tokens that expire after seven
days for these scopes. Configure the appropriate production consent status for unattended operation;
Google may require verification. Reconnect if access is revoked or token refresh fails.

## Activate the daily schedule

GitHub runs scheduled workflows only when the workflow exists on the repository's **default branch**.
The canonical app/book branch is `claude/elegant-rubin-sgov1q`, while the default branch is `main`.
Merge the implementation into the canonical branch and copy this updated `.github/workflows/promo-shorts.yml`
to `main` as well. The scheduled workflow checks out the canonical branch for code/books and saves logs there.
Manual dispatch checks out its selected branch so a test cannot silently execute old canonical code.
Keep only this existing workflow as the daily scheduler. GitHub schedules can be delayed; 05:01 IST is the
requested time, not an exact delivery guarantee.

## Failure handling

`youtube_uploads.json` is a separate workflow-owned journal containing channel/question IDs and upload
results, never credentials. Before sending a video, Actions commits and pushes its pending checkpoint.
After success, it immediately checkpoints the returned video ID. If the runner dies or loses its response,
a pending record blocks further uploads. Check YouTube Studio and reconcile that record before resuming;
never simply delete pending records and rerun. A failed journal push also stops uploads.
Generated files are archived even when a later upload fails. The API integration does not blindly retry
an ambiguous video insertion. Successful uploads do not repeat that question for the same channel.

## References

- [YouTube videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
- [Google desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Refresh token expiration](https://developers.google.com/identity/protocols/oauth2#expiration)
- [GitHub scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
