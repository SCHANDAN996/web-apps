# 📱 Study Station — Android app

## वर्तमान APK: 1.1.0, पढ़ाई मोबाइल पर

किताबें और सवाल अब APK के public content pack में हैं। पढ़ना, अभ्यास, मॉक और
progress स्थानीय रूप से चलते हैं; Jobs और current affairs के लिए server खुलता है।
Build, content export, backup और सीमाएँ: [OFFLINE_STUDY.md](OFFLINE_STUDY.md)।
नए UI में पढ़ना जारी रखने का मुख्य card, 2×2 shortcuts, searchable book library
और कक्षा filters हैं। नीचे का विवरण पुराने online wrapper की compatibility के लिए है।

App का **ढाँचा APK में** है और **content server पर**। कोई public website या अपना domain ख़रीदना ज़रूरी नहीं।

| कहाँ | क्या |
|---|---|
| **APK के अंदर** | app का frame — top bar, tab bar, icons (`app/src/main/assets/shell/{hi,en}.html`), design की files — `../app/static` (CSS, JS), screens बदलने का code, offline स्क्रीन, app icon |
| **Server पर** | हर screen का content — सवाल, किताबें, नौकरियाँ, करंट अफेयर्स — और हर learner की प्रगति (device cookie) |

**कैसे चलता है:** कोई screen खुलते ही APK अपना frame तुरंत दिखाता है (network का इंतज़ार नहीं), फिर `app.js` उस
screen का content server से लाकर सिर्फ़ बीच का हिस्सा (`<main>`) बदलता है। Tab बदलने पर पूरा page दोबारा load नहीं
होता। Internet न हो तो frame के अंदर "ऑफ़लाइन" संदेश और "दोबारा कोशिश करें" बटन आता है।

**Frame की files generate होती हैं** — `templates/base.html`, `templates/shell.html`, `static/` की कोई file या frame के
शब्द बदलें तो `study_station/v2` से चलाएँ (वरना `tests/test_shell.py` fail होगा):

```
python -m app.shell
```

**पुराना APK, नया server:** APK अपना frame और CSS/JS तभी इस्तेमाल करता है जब server वही version (`?v=…`) दे रहा हो।
Server नया हो तो page अपने-आप पूरा server से आता है (cookie `ss_shell_off`) — पुराना APK कभी टूटा हुआ design नहीं
दिखाता, बस थोड़ा धीमा खुलता है जब तक नया APK न बने। दूसरी sites (official notice, PDF) फ़ोन के browser में खुलती हैं।

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

## अपने Drive या फ़ाइल में backup

Settings का local backup Android के document picker से JSON फ़ाइल बनाता/खोलता है। Storage permission नहीं चाहिए।
Google Drive backup शुरू में बंद रहता है; Cloud Console में Drive API, OAuth consent और Android client
(इस build का package तथा signing certificate SHA-1) तैयार होने पर `local.properties` में
`ss.googleDriveEnabled=true` रखकर नया APK बनाएँ। Debug package `com.studystation.app.debug` और release
package `com.studystation.app` के signing certificates अलग हो सकते हैं; हर वितरण के लिए सही OAuth client बनाएँ।

Drive consent सिर्फ़ Settings में user के backup/restore दबाने पर native Google authorization से खुलता है।
केवल `drive.appdata` scope माँगा जाता है; app के private Drive folder में एक `study-station-backup-v1.json`
फ़ाइल रहती है। Token Android में रहता है, web page या Study Station server को नहीं भेजा जाता।
Backup सीमा 4 MiB है। Restore की पुष्टि और progress validation web app में होती है।

Bridge केवल app origin के main document को दिया जाता है; iframe और दूसरे origins से अनुरोध अस्वीकार होते हैं।
Screen/document बदलने के बाद पुराना native result छोड़ दिया जाता है। Android System WebView में
`WEB_MESSAGE_LISTENER` support न होने पर native backup उपलब्ध नहीं होगा; WebView update करें।

## नियम

- `Links.kt` तय करता है कि कौन-सा link app में खुले — बदलें तो `LinksTest.kt` भी।
- `app/static` की files LF line-endings में रहती हैं (`../.gitattributes`), वरना Windows पर बना version server से अलग निकलेगा।
