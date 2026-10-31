# Features में सुधार + Admin panel: research और plan

तारीख: 24 October 2026। स्थिति: plan; मालिक ने सुझाया क्रम मंज़ूर किया। **बन गए:** Admin चरण 1 (Dashboard 2.0), चरण 2 (ग़लत उत्तर-कुंजी queue + audit log), feature #2 (mock resume), feature #4 (Telegram क्विज़ app में), feature #5 (मेरी गलतियाँ), feature #6 (CA quiz में किताब के AIR facts)। बाकी अभी बाकी।

मालिक के निर्देश:
- UI का मौजूदा flow वैसा ही रहेगा। सिर्फ़ छोटे सुधार होंगे; Home का क्रम नहीं बदलेगा। (batch-1 redesign revert किया गया।)
- PayU, trial, कीमतें और retention policy नहीं बदलेंगी। Play billing/UCB बंद रहेगा।
- Telegram/Shorts सिर्फ़ GitHub Actions से चलेंगे।

आधार: इसी repo का code पढ़ा गया। इसमें `app/admin.py`, `app/observe.py`, models, tests और `docs/FEATURE_STATUS.md` शामिल हैं।
competitor apps (Testbook, Adda247, Oliveboard आदि) के बारे में जो लिखा है, वह आम तौर पर दिखने वाले features की
जानकारी है। उनके आँकड़े या दावे नहीं दिए गए।

---

## भाग 1 — अभी क्या है (छोटा सार)

**सीखना**
- अभ्यास (10 सवाल, topic, custom list)
- CBT mock और result
- Leitner revision
- किताबें (300 अध्याय, hi+en) और offline study pack
- current affairs (AIR)
- question bank
- favourites/share

**साथ पढ़ना**
- Workspace v2 (notebooks, drawing)
- Group study, शिक्षक की कक्षा, Shared workspace
- community reports

**खाता**
- Google login, recovery-code sync, backup/restore
- scoped reset, account deletion

**कमाई**
- website पर membership + PayU (चालू)
- Play billing (बंद)

**नौकरी**
- सरकारी notice engine (official sources), filters, alerts digest

**प्रचार**
- Telegram पर रोज़ 10 polls + ट्रिक + उत्तर, रविवार का टेस्ट
- रोज़ 3 Shorts

**अभी का admin (`/admin`)**
- एक password और signed cookie, 8 घंटे का session, login rate-limit, CSRF जाँच।
- Dashboard पर 6 गिनतियाँ: reports, flagged, unreviewed, verified, pending jobs, open jobs।
- Job source health और sweep/cleanup/digest बटन।
- सवाल review queue और job edit।
- Community reports पर फ़ैसला: dismiss, remove, suspend।

---

## भाग 2 — Features में सुधार (flow वही, अंदर से बेहतर)

हर सुधार के साथ उसकी जाँच (test) लिखी है।
- **P0** = भरोसा और सही उत्तर
- **P1** = पढ़ाई का फ़ायदा
- **P2** = बढ़त (growth)

| # | प्राथमिकता | सुधार | क्यों | जाँच |
|---|---|---|---|---|
| 1 | P0 | **संदिग्ध उत्तर-कुंजी अपने-आप पकड़ना:** `observe` अभी ऐसे सवाल गिनता है जिनमें 20+ उत्तरों में 15% से कम सही हैं। इन्हें admin queue में दिखाना, और मालिक की पुष्टि पर hide करना। | एक ग़लत उत्तर भरोसा तोड़ता है, और Telegram पर वायरल होकर और नुक़सान करता है। | test: नकली आँकड़ों से सवाल queue में आए; बिना पुष्टि hide न हो। |
| 2 | P0 | **सवाल resume:** 12/50 पर छोड़ा तो वापस 12 ही खुले। palette और number एक ही जगह से आएँ। (handoff में P0) | सबसे ज़्यादा समय यहीं जाता है। | e2e: बीच में छोड़कर लौटें, वही सवाल और उत्तर बचे रहें। |
| 3 | P0 | **Mock card पर साफ़ जानकारी:** सवाल, समय, negative marking। bank अधूरा हो तो "Full mock" न लिखें। | ग़लत लेबल से भरोसा घटता है। | test: अधूरे exam पर "Full" न दिखे। |
| 4 | P1 | **"आज के Telegram सवाल" app में:** जो 10 सवाल चैनल पर गए, वही app में एक quiz के रूप में (`posted.json` से)। | Telegram से आए लोग app में भी वही पाएँ, और site live होने पर लिंक सीधे वहाँ जाए। | test: आज के posted ids → quiz; सवाल दोहराए न जाएँ। |
| 5 | P1 | **गलतियों का दोहराव:** "मेरी गलतियाँ" सेट, यानी पिछले 7 दिन के गलत सवाल। revision में एक बटन। Leitner पहले से है, बस आसान रास्ता चाहिए। | कमज़ोरी पर सीधा अभ्यास। | test: सिर्फ़ उसी learner के गलत सवाल आएँ। |
| 6 | P1 | **Current affairs का हफ़्ते/महीने का quiz** `tools/current_affairs/facts.tsv` से (AIR लिंक के साथ)। | परीक्षा में CA के पक्के नंबर मिलते हैं। facts पहले से जाँचे हुए हैं। | test: हर सवाल के साथ AIR link। |
| 7 | P1 | **Jobs:** खोज साफ़ बताए कि कितने results में खोज रही है। अपनी योग्यता/राज्य के हिसाब से alert। (handoff में P1) | नौकरी वाला हिस्सा लोगों को रोज़ वापस लाता है। | test: filter reset; "100 में से" वाला text। |
| 8 | P1 | **Offline pack:** हर किताब का size और "डाउनलोड हुआ ✓" दिखे। | सस्ते फ़ोन, कम data। | e2e: offline में अध्याय खुले। |
| 9 | P2 | **Result share card:** mock के बाद score की एक तस्वीर जिसमें चैनल/app का लिंक हो। सिर्फ़ असली score, कोई बनावटी rank नहीं। | मुफ़्त प्रचार। | test: image में सिर्फ़ उसी attempt के अंक। |
| 10 | P2 | **रोज़ की याद (web push / app notification):** "आज के 10 सवाल बाकी हैं", सिर्फ़ जिसने अनुमति दी हो। | streak बचती है। | test: opt-in के बिना कुछ न भेजा जाए। |
| 11 | P2 | **Signature sound (Shorts):** 4-5 notes की अपनी धुन और हल्की घड़ी की टिक-टिक। ffmpeg ख़ुद बनाता है, कोई copyright नहीं। | reels की पहचान बनती है। | test: धुन scenes के समय पर। |

**जो नहीं करेंगे:**
- नकली "All-India rank" या बिना स्रोत के "PYQ" दावे।
- AI से बनी तस्वीरों या AI आवाज़ से पढ़ाना। मालिक बाद में चाहें तो disclosure के साथ।
- नया framework।

---

## भाग 3 — Admin panel का plan

मौजूदा `/admin` को ही बढ़ाना है, नया system नहीं बनाना।
- login, cookie और CSRF वही रहेंगे।
- हर नया हिस्सा **पहले read-only** बनेगा।
- बदलाव करने वाले बटन बाद में आएँगे, हर बटन के साथ audit log।
- फ़ोन पर चलने लायक layout होगा।

### A. Dashboard 2.0: एक नज़र में सब
- **Learners:** आज और 7 दिन में active, आज के उत्तर, 7 दिन के mock (`observe.collect()` से)। सिर्फ़ गिनती, किसी का नाम या email नहीं।
- **Alerts:** `observe` वाली सूची (🔴/🟠)। website health, sweep 12h से नहीं चला, CA 36h से नहीं आया, backup 2 दिन पुराना, AI सीमा।
- **Deploy:** server पर कौन-सा revision चल रहा है (`/var/lib/studystation/source-release.json`) और GitHub से मेल खाता है या नहीं।
- **Promo:** चैनल लिंक, आज कौन-से slot गए (posted.json की server पर पढ़ी प्रति), आख़िरी Shorts run का लिंक।

### B. सामग्री
- **सवाल:** मौजूदा queues के साथ नई **"संदिग्ध उत्तर-कुंजी"** queue (सुधार #1)। एक साथ कई सवाल verify/hide (bulk), हर बदलाव audit log में।
- **किताबें:** हर book और अध्याय की bookcheck स्थिति (OK/TODO/FIX), `chapter.json` का status (draft/reviewed)।
  - **read-only रहेगा।** किताबें GitHub पर बदलती हैं, server पर बदलीं तो source अलग हो जाएगा।
- **Current affairs:** आज के items, एक बटन से hide (`python -m app.current_affairs hide` वाला काम) और कारण लिखना।

### C. नौकरियाँ (मौजूदा)
- job edit और source health वैसे ही रहेंगे।
- जोड़ना: "official link नहीं मिला" वाले pending jobs की सूची और उनकी उम्र।

### D. सदस्यता और भुगतान: सिर्फ़ देखना
- active membership की गिनती, अगले 7 दिन में ख़त्म होने वाली, आज के PayU orders (status: success/pending/failed) और reconcile का नतीजा।
- order id से खोज।
- learner की पहचान छिपी रहेगी (आख़िरी 4 अक्षर)। email/phone नहीं दिखेंगे।
- **कोई बटन नहीं** जो कीमत, trial या membership बदले। manual grant सिर्फ़ मालिक के अलग निर्देश पर, audit के साथ।

### E. Community (मौजूदा)
- reports queue वैसी ही। जोड़ना: suspended accounts की सूची और "suspension हटाएँ" (कारण के साथ, audit)।

### F. Ops और सुरक्षा
- backup की आख़िरी तारीख/size, retention job की स्थिति, disk की जगह, logs (मौजूदा "runs")।
- **Audit log:** नई table `AdminAction`। हर admin बदलाव में कौन, कब, क्या, कारण दर्ज होगा। सूची admin में दिखेगी।
- **2-step login (TOTP):** password के साथ Google Authenticator का 6 अंकों वाला code। मालिक चाहे तो।
- सभी sessions से एक साथ logout (password बदलने से यह पहले से होता है)।
- **AI usage:** आज के calls और सीमा।

### चरण (हर चरण अलग, छोटे commits, tests के साथ)

| चरण | काम | प्रकृति |
|---|---|---|
| 1 | Dashboard 2.0: learners, alerts, deploy revision, promo स्थिति | read-only |
| 2 | संदिग्ध उत्तर-कुंजी queue + audit log table + bulk verify/hide | बदलाव (audit के साथ) |
| 3 | किताबों की स्थिति + CA hide बटन | read-only + एक बदलाव |
| 4 | सदस्यता/भुगतान का दृश्य | read-only |
| 5 | Community suspensions + 2-step login | सुरक्षा |

हर चरण में:
- pytest (admin के बिना login के 303/403, CSRF, data छिपाना)
- फ़ोन-size screenshot
- `docs/FEATURE_STATUS.md` अपडेट

server पर deploy अलग step है, और Play APK पर इसका कोई असर नहीं।

---

## भाग 4 — मालिक से फ़ैसले चाहिए
1. Admin में पहले क्या: **चरण 1 (Dashboard 2.0)** या **चरण 2 (ग़लत उत्तर पकड़ना)**? सुझाव: 1 फिर 2।
2. Admin अकेले आप चलाएँगे, या किसी moderator/शिक्षक को भी पहुँच देनी है? (तब अलग login और सीमित अधिकार चाहिए।)
3. 2-step login (TOTP) चाहिए?
4. Features में से पहले कौन-से तीन? सुझाव: #1 ग़लत उत्तर, #2 resume, #4 Telegram वाले सवाल app में।
