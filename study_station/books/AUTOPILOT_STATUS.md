# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 03:27 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 03:11 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |
| W2 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |
| W3 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |
| W4 | Chapter 06 kaal vachya (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 19 |
| key 4 | 13 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
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

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 15:11:08 autopilot start: 4 workers, reverse=False
19-11 15:11:08 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
19-11 15:11:08 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
19-11 15:11:13 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
19-11 15:11:18 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
19-11 15:11:23 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_06_kaal_vachya (OK: todo 0, problems 0)
19-11 15:13:32   [sangya_sarvanam] review Key_Facts_hi.txt round 1: 3 issue(s): - Point 6: Example "लड़कोंने खेले" for ergative "ने" uses intransitive verb "खेलना"; "ने" is only for tra
19-11 15:14:00   [varn_vartani] review Key_Facts_hi.txt round 1: 3 issue(s): - The description of नुक्ता-युक्त व्यंजन as two letters (ऩ, ऱ) used for Marathi/Sanskrit sounds is incorr
19-11 15:15:16   [varn_vartani] review Key_Facts_hi.txt round 2: 4 issue(s): - Point 1 says there are only 2 नुक्ता‑युक्त व्यंजन and totals 41 consonants (33 + 4 + 2 + 2); in fact th
19-11 15:15:44   [ling_vachan_karak] review Content_hi.txt round 1: 8 issue(s): - Section 2 (वचन), Table "बहुवचन बनाने के नियम": Row for "आ (स्त्रीलिंग)" states rule "आ → एँ" but examples
19-11 15:17:35   [varn_vartani] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 1: The consonant total is given as 41 with the breakdown “33 मूल व्यंजन + 4 संयुक
19-11 15:18:14   [ling_vachan_karak] review Content_hi.txt round 2: 3 issue(s): - In "लिंग के प्रकार" table, नपुंसकलिंग examples "कमरा", "पत्तल", "ज्ञान" are incorrect: "कमरा" and "ज्ञान"
19-11 15:18:44   [varn_vartani] review Feynman_hi.txt round 1: 2 issue(s): - The chandrabindu rule table (Section 3) and Question 4 (Section 5) incorrectly give "गँगा" as correct and
19-11 15:20:33   [varn_vartani] review Feynman_hi.txt round 2: 3 issue(s): - व्यंजन गणना: "33 व्यंजन" लिखा है लेकिन सूची में 36 व्यंजन (क्ष, त्र, ज्ञ सहित) दिए हैं → या तो गिनती 36 क
19-11 15:21:30   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - In the लिंग-परिवर्तन rules table, rule 2 "आ → इन" lists "सेठ → सेठानी" as an example, but
19-11 15:22:26   [varn_vartani] REJECTED review fix Feynman_hi.txt: reviewer still reports - Chandrabindu rule table lists "गँवार" as correct, but 'ग' is not in the specified group (
19-11 15:22:27   [ling_vachan_karak] review Key_Facts_hi.txt round 1: 7 issue(s): - Point 2 example “पेड़ा” is not a standard masculine noun → use “पेड़”
19-11 15:24:00   [varn_vartani] review Flashcards_hi.txt round 1: 1 issue(s): - Card 14: 'हिंदी' listed as anusvara example is wrong; standard Hindi spelling is 'हिन्दी' (with न) → R
19-11 15:24:05   [kaal_vachya] review Content_hi.txt round 1: 2 issue(s): - Invented exam statistic: "SSC GD, MTS, RRB Group D जैसी परीक्षाओं में इनसे प्रतिवर्ष 3–5 प्रश्न पूछे जाते
19-11 15:26:42   [kaal_vachya] review Content_hi.txt round 2: 3 issue(s): - In section 1.2 table, the structure for भूतकाल सामान्य is given as "मूल क्रिया + ा/ए/ई + था/थे/थी" but th
```
