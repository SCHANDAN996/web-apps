# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 11:52 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 11:36 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 16 मिनट |
| W2 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 16 मिनट |
| W3 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |
| W4 | Chapter 06 kaal vachya (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 12 |
| key 4 | 14 |

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

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 11:36:09 autopilot start: 4 workers, reverse=False
19-11 11:36:09 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
19-11 11:36:09 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
19-11 11:36:14 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
19-11 11:36:20 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
19-11 11:36:25 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_06_kaal_vachya (OK: todo 0, problems 0)
19-11 11:38:19   [kaal_vachya] review Content_hi.txt: 2 issue(s): - "प्रतिवर्ष 3–5 प्रश्न पूछे जाते हैं" is an invented exam statistic without a specific year or source → remove or 
19-11 11:39:23   [varn_vartani] review Content_hi.txt: 1 issue(s): - The 'ड़/ढ़' rule cites a non-existent word 'बड़ना' as the base for 'बढ़ना'; 'बड़ना' does not exist in Hindi. → De
19-11 11:41:16   [kaal_vachya] REJECTED review fix Content_hi.txt: reviewer still reports - In section 1.2 भूतकाल table, the structure for सामान्य भूतकाल is given as “मूल क्रिया + ा
19-11 11:41:57   [kaal_vachya] review Key_Facts_hi.txt: 3 issue(s): - Point 18: The “wrong” and “correct” examples both show “पढ़ा जाएगा”; the wrong example should illustrate a tens
19-11 11:43:22   [varn_vartani] review Key_Facts_hi.txt: 2 issue(s): - Point 1 incorrectly includes ऩ and ऱ as the two nukta‑yukt consonants in the 41‑consonant count; standard Hindi
19-11 11:44:18   [kaal_vachya] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 10 example uses an intransitive verb for passive: "सीता गाती है" → "गाया जाता है 
19-11 11:45:27   [varn_vartani] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 9: Example "संड" for ण is wrong — "संड" uses न, not ण → Use a correct example lik
19-11 11:47:14   [sangya_sarvanam] review Key_Facts_hi.txt: 2 issue(s): - In point 6, the example "लड़कोंने खेला" shows a verb agreement error: plural subject "लड़कोंने" requires plural
19-11 11:47:58   [kaal_vachya] review PYQ_hi.txt: 2 issue(s): - Section 2.1, rule 2: “क्रिया → जा/ई/ए + मूल क्रिया का भूतकालिक कृदंत” is wrong → correct passive formation: “मूल क्रि
19-11 11:48:38   [varn_vartani] review Feynman_hi.txt: 4 issue(s): - The consonant list in section 1 includes 36 items (क to ज्ञ) but is labeled “व्यंजन (33)” → The list should conta
19-11 11:52:24   [ling_vachan_karak] review Content_hi.txt: 5 issue(s): - वचन तालिका में "आ (स्त्रीलिंग)" पंक्ति के उदाहरण "लड़की → लड़कियाँ", "नदी → नदियाँ" ई-कारांत हैं, आ-कारांत नहीं; 
```
