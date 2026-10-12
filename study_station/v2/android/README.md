# 📱 Study Station — Android app (shell)

यह app v2 server के ऊपर एक पतला खोल (WebView) है। कोई public website या अपना domain ख़रीदना ज़रूरी नहीं।

| कहाँ | क्या |
|---|---|
| **APK के अंदर** | design की files — `../app/static` (CSS, JS, icon), offline स्क्रीन, app icon |
| **Server पर** | सवाल, किताबें, नौकरियाँ, करंट अफेयर्स, और हर learner की प्रगति (device cookie) |

APK अपनी CSS/JS तभी इस्तेमाल करता है जब server वही version (`?v=…`) माँगे; server नया हो तो files अपने-आप
network से आती हैं — पुराना APK कभी टूटा हुआ design नहीं दिखाता। दूसरी sites (official notice, PDF) फ़ोन के
browser में खुलती हैं।

## बनाना (Windows PC)

ज़रूरत: JDK 17, Android SDK (`ANDROID_HOME`)। सब commands `study_station/v2/android` से।

```
gradlew.bat testDebugUnitTest assembleDebug
```

APK: `app/build/outputs/apk/debug/app-debug.apk`

Server का पता `local.properties` में (यह file commit नहीं होती):

```
ss.debugUrl=http://192.168.1.10:8000      # जाँच: PC पर चलता v2 (फ़ोन और PC एक ही Wi‑Fi पर)
ss.releaseUrl=https://<आपका-नाम>.duckdns.org   # असली server — सिर्फ़ HTTPS
```

- **Debug** APK सादा `http` चला सकता है (सिर्फ़ जाँच के लिए); default `http://10.0.2.2:8000` = emulator से यही PC।
- **Release** (`gradlew.bat assembleRelease`) सिर्फ़ `https://` पते पर बनता है। Play Store / लोगों को देने से पहले इसे
  अपनी keystore से sign करना होता है — keystore और उसका password आप ख़ुद बनाएँ और सँभालें, repo में कभी नहीं।

## PC पर जाँच

```
cd study_station/v2
set COOKIE_SECURE=0
uvicorn app.main:app --host 0.0.0.0 --port 8000
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

## नियम

- `Links.kt` तय करता है कि कौन-सा link app में खुले — बदलें तो `LinksTest.kt` भी।
- `app/static` की files LF line-endings में रहती हैं (`../.gitattributes`), वरना Windows पर बना version server से अलग निकलेगा।
