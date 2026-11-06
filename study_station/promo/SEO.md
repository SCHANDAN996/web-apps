# Automatic Shorts metadata

Every new Short gets its own metadata before upload. No external model or API key is required:
`app/promo/metadata.py` deterministically uses the actual question, option/answer validation, subject,
level and bilingual chapter titles. The correct option and explanation never appear as a public spoiler.
This is a shared generation template, not one identical title/keyword block on every video.

## Per-video decisions

- Title: specific chapter/topic first, a whole-word question hook when it fits, English subject label
  and #Shorts; maximum90characters. Long questions remain complete in description when within budget.
- First2description lines: the chapter in Hindi/English and honest one-question practice context.
- Actual question/options follow; channel introduction and Telegram link remain shared.
- Exactly3description hashtags: Shorts, relevant subject, StudyStation. No keyword block in description.
- Tags: brand, subject, bilingual chapter, small relevant exam group; case-insensitive duplicates removed,
  conservative450character budget. Tags are supplementary; they do not guarantee search ranking.
- Exam mapping uses subject **and** level. Banking context only for graduation-level Maths/Reasoning;
  no blanket Bank/UPSC tags on GK/English. Labels mean practice context, never proof of a past exam question.
- Missing/corrupt chapter titles fall back to readable folder/subject. Invalid option/answer structure
  uses a generic subject template without exam targeting. No paid AI call can delay/block daily publishing.

Outputs: NN.mp4, NN.txt (exact uploaded title+description), NN.metadata.json (same title/description/tags,
chapter labels, generator version and fallback flag). Thumbnail failures do not discard valid tags.
Existing uploaded videos are not bulk-edited by this change. The next ordinary renderer run uses it.

## Existing schedule stays unchanged

The **main** default-branch workflow currently requests01:01IST and retries until05:31IST with --once.
It checks out canonical `claude/elegant-rubin-sgov1q`. App defaults schedule publication at06:00,14:00,
19:00IST; repository variable YOUTUBE_PUBLISH_TIMES may override them. Public uploads use private+
publishAt until their slot. GitHub start/delivery can be delayed; this is not a guaranteed01:01start.
No second cron, VPS generator or new scheduled task is added. This change does not reset posted logs.

## Shorts thumbnail plan / implementation

The existing renderer already creates a vertical9:16 JPEG from the real question's opening frame.
Keep the exact question visible, with important text away from edges; no invented clickbait or answer spoiler.
YouTube's current API guidance says Shorts thumbnails must be set **after processing succeeds**.
Uploader now queries processingDetails under a60second budget (15s HTTP timeouts), then calls
thumbnails.set. Accepted/not_set is recorded alongside the successfully uploaded video.
A missing permission, feature rollout, malformed response or processing timeout leaves the video/schedule
intact and logs a safe warning. It never reuploads the video just because its thumbnail failed.
The JPEG remains in the Actions artifact for manual use. There is no later background thumbnail retry.

Channel eligibility/rollout and actual thumbnail appearance still require YouTube Studio verification.
An accepted API request is not proof the same image is shown on every Shorts surface. The existing
question-first video opening remains useful even when a custom thumbnail is unavailable.

## Official references checked5November2026

- [Titles/descriptions matter more than tags](https://support.google.com/youtube/answer/146402?hl=en)
- [Search matching title/description/video](https://support.google.com/youtube/answer/141805?hl=en)
- [Current Shorts thumbnail help](https://support.google.com/youtube/answer/72431?hl=en)
- [Shorts thumbnail rollout](https://blog.youtube/news-and-events/youtube-studio-custom-thumbnail-updates/)
- [API thumbnail processing requirement](https://developers.google.com/youtube/data/reference/rest/v3/thumbnails/set)
- [API revision history,3November2026](https://developers.google.com/youtube/data/revision_history?hl=en)
