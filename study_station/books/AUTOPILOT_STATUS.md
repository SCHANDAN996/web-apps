# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 07:14 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 06:58 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 16 मिनट |
| W2 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 16 मिनट |
| W3 | Chapter 06 kaal vachya (10th Hindi) | 🔎 review हो रहा है | 2 मिनट |
| W4 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 19 |
| key 4 | 15 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 6 | 0 | 11 |
| 12th Computer | 7 | 0 | 7 |
| 10th GK | 19 | 0 | 0 |
| 10th Reasoning | 22 | 0 | 0 |
| 10th Maths | 22 | 0 | 0 |
| 10th English | 20 | 0 | 0 |
| 12th Maths | 23 | 0 | 0 |
| 12th GK | 24 | 0 | 0 |
| 12th Reasoning | 25 | 0 | 0 |
| 12th English | 25 | 0 | 0 |
| Graduation Maths | 28 | 0 | 0 |
| Graduation GK | 28 | 0 | 0 |
| Graduation Reasoning | 30 | 0 | 0 |
| Graduation English | 30 | 0 | 0 |
| **कुल** | **309** | **0** | **18** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 04 visheshan kriya (Hindi) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 06:58:02 autopilot start: 4 workers, reverse=False
19-11 06:58:02 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
19-11 06:58:02 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
19-11 06:58:07 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
19-11 06:58:12 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya (OK: todo 0, problems 0)
19-11 06:58:17 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
19-11 06:59:11   [varn_vartani] review Content_hi.txt: 3 issue(s): - Section 2.1 (परीक्षा उपयोगी नियम), Section 6 (त्वरित संकेत #3), Section 7 (Q1 उत्तर संकेत): अवर्गीय व्यंजन (य, र,
19-11 06:59:53   [ling_vachan_karak] review Content_hi.txt: 6 issue(s): - Section 1, नपुंसकलिंग table: "फल, पत्तल, कमरा, ज्ञान" are incorrectly classified as neuter; they are masculine/fe
19-11 07:01:34   [visheshan_kriya] review Content_hi.txt: 3 issue(s): - The rule "विशेषण हमेशा संज्ञा/सर्वनाम के लिंग, वचन, कारक के अनुसार बदलता है" is incorrect because अरूपांतरित विशे
19-11 07:02:27   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - Section 1 (लिंग) Napuṁsakaliṅg table lists "आग", "धुआँ", "पानी" as नपुंसकलिंग → In standa
19-11 07:03:30   [ling_vachan_karak] review Key_Facts_hi.txt: 6 issue(s): - बिंदु 2 में उदाहरण **पेड़ा** गलत है (यह मानक पुल्लिंग संज्ञा नहीं है) → सही उदाहरण: **बच्चा** (या कोई अन्य आकार
19-11 07:03:57   [visheshan_kriya] REJECTED review fix Content_hi.txt: reviewer still reports - Section 1.3 table lists 'हरा' under अरूपांतरित विशेषण → 'हरा' is रूपांतरित (हरा/हरी) and 
19-11 07:05:13   [sangya_sarvanam] review Content_hi.txt: 2 issue(s): - उदाहरण 4 और त्वरित पुनरावृत्ति बिंदु 3 में "ने" का नियम गलत बताया गया है: "सकर्मक क्रिया + भूतकाल + कर्ता → ने" →
19-11 07:05:20   [ling_vachan_karak] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 4: Claims Hindi has a neuter gender for inanimate objects and lists किताब, मेज, प
19-11 07:08:55   [ling_vachan_karak] review PYQ_hi.txt: 6 issue(s): - Grammar rule for ergative "ने" incorrectly restricted to अन्य पुरुष (third person) → "ने" is used with transitive ver
19-11 07:10:38   [visheshan_kriya] review Important_Rules_hi.txt: 1 issue(s): - Rule 12 example "वह जोरदार बोला" incorrectly treats "जोरदार" as a क्रियाविशेषणीय विशेषण (adverbial adject
19-11 07:11:11   [sangya_sarvanam] review Key_Facts_hi.txt: 2 issue(s): - Point 13: The dative form “किसे (कभी-कभी)” is incorrectly listed for “क्या” → “क्या” has no dative form “किसे”;
19-11 07:11:22   [visheshan_kriya] review: 1 section(s) corrected, 1 failed
19-11 07:11:22   [visheshan_kriya] written 1, failed 1; AI calls today 30/100000
19-11 07:11:23 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya after 13 min: todo [] problems []
19-11 07:11:23 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_06_kaal_vachya (OK: todo 0, problems 0)
19-11 07:12:20   [varn_vartani] REJECTED review fix Content_hi.txt: reviewer still reports - In Section 3.1 (मात्रा-नियम table), the examples for matra 'इ' (ि) are incorrect: "फल" → 
19-11 07:12:59   [varn_vartani] review Key_Facts_hi.txt: 1 issue(s): - बिंदु 6 में "नुक्ता-युक्त व्यंजन (2): ऩ, ऱ" गलत है → हिंदी में नुक्ता-युक्त व्यंजन अनेक हैं (क़, ख़, ग़, ज़, फ़
19-11 07:13:52   [kaal_vachya] review Content_hi.txt: 4 issue(s): - Introduction claims 'प्रतिवर्ष 3–5 प्रश्न पूछे जाते हैं' without a specific year or source → remove the statistic
```
