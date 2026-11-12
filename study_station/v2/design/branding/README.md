# StudyStation approved multicolor identity

The authoritative full logo is `studystation-multicolor-master.png`, the exact owner's selected
`logo-option-08-multicolor.png`: multicolor tree growing from an open book, StudyStation wordmark.
Do not substitute a contact sheet, another concept, a traced redraw, or the rejected alpha isolate.

The icon crop is derived directly from that 1254×1254 original at pixel bounds
`(150, 55, 1105, 955)` (left, top, right, bottom), above the wordmark. It retains the original white
background and exact artwork. Small icons use this emblem without illegible text; large assets use
the complete original. No colors/shapes are reconstructed. The white backing is intentional on dark UI.

Rebuild from `study_station/v2` with the project's Pillow dependency:

```sh
python scripts/export_branding.py
python -m app.shell
python -m app.shell --check
```

`exports.json` records SHA-256 for both sources and every exported asset. Web asset versions and
Android's bundled asset version derive automatically from static bytes. No manual version string,
service-worker implementation, Android package, billing or signing setting changes are required.
The exporter also gives each PWA manifest icon a URL version derived from that icon's SHA-256,
so long-lived static caches cannot reuse the previous icon URL after the manifest updates.
Installed PWA icon refresh remains browser/OS controlled and may take time after deployment.

| Surface | Active file / behavior |
|---|---|
| Website header | `app/static/brand-mark.webp` (96×96, displayed at36×36) |
| Browser favicon | `app/static/favicon.png` (64×64) |
| PWA installation | `app/static/icon-192.png`, `icon-512.png` |
| Existing SVG icon URL | `app/static/icon.svg` embeds the current emblem |
| Android launcher + native offline screen | `android/app/src/main/res/drawable-nodpi/brand_icon.png`; 80px padding plus existing18dp foreground inset keeps colored book corners inside the central33dp-radius safe circle; launcher background is white |
| Android web and offline HTML | Regenerated `android/app/src/main/assets/{shell,offline}/{hi,en}.html`; Gradle bundles current static assets at build time |
| Full promotional logo | `../promo/branding/logo.jpg` (1024×1024) |
| Social account avatar | `../promo/branding/profile-1024.png` (emblem, padded for circular crops) |
| YouTube banner | `../promo/branding/banner.jpg` (2560×1440); complete content in central1546×423 safe rectangle |
| Play listing icon | `play-store/icon-512.png` (512×512, RGBA PNG, opaque white background) |
| Play feature graphic | `play-store/feature-1024x500.png` (1024×500, RGB PNG, no alpha) |

Google's listing sizes/formats were checked11November2026 in
[Play Console preview-asset requirements](https://support.google.com/googleplay/android-developer/answer/9866151).
They are listing files; uploading them does not update an already installed Android launcher icon.

The former active `study-station-3d-master.png` is removed from the current tree and recoverable from
Git history before this branding commit. Unrelated historical concepts and the legacy app folders are
not active canonical branding and are deliberately left alone.

Website deployment, a signed Android update, Play listing updates, and social profile/banner uploads
are separate actions. Exporting or committing assets does not perform any of those remote updates.
Telegram, Instagram and YouTube profile pictures must be updated on their verified StudyStation
accounts; leave unrelated accounts untouched. See `docs/PLAY_STORE_BRANDING_HANDOFF.md`.
