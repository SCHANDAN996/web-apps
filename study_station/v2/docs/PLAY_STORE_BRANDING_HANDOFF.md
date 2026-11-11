# Play Store branding — दूसरे chat में देने वाला prompt

नीचे का prompt उस chat में दें जो मौजूदा StudyStation Play Store release संभाल रहा है:

```text
मेरे मौजूदा StudyStation Android/Play Store काम में चुना हुआ नया multicolor tree+book logo लगाओ।
नया app या दूसरा package मत बनाना। Existing package com.studystation.app, उसी verified signing
identity और मौजूदा Play Console listing को जारी रखना। Console में वर्तमान versionCode जाँचकर
उसी release workflow के अनुसार अगला version चुनना; इस branding patch ने version/billing/signing
settings नहीं बदली हैं। Secrets/keystore passwords chat, logs या Git में मत लिखना।

Repo https://github.com/SCHANDAN996/web-apps
Canonical branch claude/elegant-rubin-sgov1q
App scope study_station/v2
PC checkout C:\Users\Admin\Desktop\my project\MASS APP\study-station-latest
Branding worktree C:\Users\Admin\Desktop\my project\MASS APP\studystation-branding

पहले git status/remotes और study_station/v2/AGENTS.md, CLAUDE.md, docs/SOURCE_SYNC.md पढ़ो।
PC checkout में मेरा और दूसरे chat का अधूरा काम है: उसे overwrite/reset/clean मत करना। Latest
canonical और verified branding commit देखो; जरूरत पर अलग worktree में ordinary merge/cherry-pick
करो। पूरे पुराने app/source को branding worktree से replace मत करना।

यह exact approved original है:
study_station/v2/design/branding/studystation-multicolor-master.png
इसी का wordmark-विहीन exact pixel crop है:
study_station/v2/design/branding/studystation-emblem-crop.png
दूसरा concept/contact sheet/rejected alpha isolate मत इस्तेमाल करना। README.md और exports.json
में crop, references और SHA-256 हैं। नया design/recolor करने की जरूरत नहीं है।

Play listing files:
study_station/v2/design/branding/play-store/icon-512.png
study_station/v2/design/branding/play-store/feature-1024x500.png

Android launcher और native offline image:
study_station/v2/android/app/src/main/res/drawable-nodpi/brand_icon.png
Existing adaptive foreground XML इसी file को reference करता है; launcher_background white है।
Web/PWA favicon और icons भी app/static में बदले हैं। APK build से पहले अपने अंतिम merged source
पर python -m app.shell और --check चलाकर shell/offline HTML तथा bundled asset hash फिर बनाओ।

Final merged source पर आवश्यक Python/Android tests और release checks चलाओ। Existing signed
release pipeline से AAB बनाओ; actual artifact में नया launcher icon और web/offline logo जाँचो।
Installed app का launcher icon केवल server deploy या Play listing icon बदलने से नहीं बदलेगा;
उसके लिए signed Android app update आवश्यक है। Build/sign/upload credentials मैं सुरक्षित terminal
या official login में स्वयं दूँगा जहाँ जरूरत हो। नया signing key या applicationId मत बनाना।

Existing listing में icon और feature graphic लगाओ। Screenshots पुराने logo दिखाते हों तो वर्तमान
actual app से नए screenshots बनाओ; कोई fake UI/result/selection/guarantee मत जोड़ना। Existing
description, billing, privacy, data safety, content rating या recruitment status को branding के बहाने
मत बदलना। Console की वर्तमान requirements पढ़ो; truthful existing app facts ही उपयोग करो।

Routine preparation/verification पूरा करो। Release/submission के लिए इस chat की पहले से दी हुई
authorization लागू करो; यदि final publish का अधिकार अभी नहीं मिला है तो concrete verified AAB,
listing changes और target track/version दिखाकर केवल final decision मुझसे लो। केवल build pass या
assets upload को released मत कहना। अंत में exact source SHA, AAB SHA-256, package/version,
listing-save/review/published status और manual blocker प्रमाण सहित बताओ।
```

Asset formats checked 11 November 2026:
[Google Play preview-asset requirements](https://support.google.com/googleplay/android-developer/answer/9866151).
