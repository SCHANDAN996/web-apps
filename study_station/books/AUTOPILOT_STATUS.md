# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 08:42 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 08:36 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 5 मिनट |
| W2 | Chapter 06 kaal vachya (10th Hindi) | 📤 push हो रहा है | 0 मिनट |
| W3 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 5 मिनट |
| W4 | Chapter 07 word (12th Computer) | 🔎 review हो रहा है | 5 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 4 |
| key 4 | 5 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 6 | 0 | 11 |
| 12th Computer | 9 | 0 | 5 |
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
| **कुल** | **311** | **0** | **16** |

## ✅ autopilot से हाल में पूरे हुए

- 19-11 20:42 — 10th Hindi · Chapter 06 kaal vachya

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 20:36:56 autopilot start: 4 workers, reverse=False
19-11 20:36:56 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
19-11 20:36:57 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
19-11 20:36:58   [varn_vartani] review Key_Facts_hi.txt: resumed private correction draft
19-11 20:37:02 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_06_kaal_vachya (OK: todo 0, problems 0)
19-11 20:37:03   [kaal_vachya] review Content_hi.txt: resumed private correction draft
19-11 20:37:07 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_07_sandhi (TODO: todo 5, problems 0)
19-11 20:37:08   [sandhi] Hindi-only writer: direct Hindi content; English generation and translation disabled
19-11 20:37:12 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_07_word (OK: todo 0, problems 0)
19-11 20:37:13   [word] review Key_Facts_en.txt: resumed private correction draft
19-11 20:37:51   [varn_vartani] review Key_Facts_hi.txt round 1: 3 issue(s): - The traditional Hindi alphabet count is 44 (11 vowels + 33 consonants); the conjuncts (क्ष, त्र, ज्ञ, श
19-11 20:39:44   [kaal_vachya] review Content_hi.txt round 1: 3 issue(s): - In Example 6 explanation, "ने के स्थान पर द्वारा" is incorrect because the active sentence "लड़के फुटबॉल 
19-11 20:39:46   [word] review Key_Facts_en.txt round 1: 4 issue(s): - Point 9: "Shift+F3 cycles UPPER/lower/Sentence case" → "Shift+F3 cycles UPPERCASE, lowercase, Capitaliz
19-11 20:41:42   [word] review Key_Facts_en.txt round 2: 1 issue(s): - Point 20 states "blue wavy underline = grammar (Word 2016/2019)"; grammar errors are indicated by a blu
19-11 20:42:22   [kaal_vachya] review: 1 section(s) corrected, 0 failed
19-11 20:42:22   [kaal_vachya] written 1, failed 0; AI calls today 11/100000
```
