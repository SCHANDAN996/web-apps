# 📚 Book Autopilot — लाइव स्थिति (twelve-chapters)

**आख़िरी update:** 21-11-2026 08:02 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 21-11 07:44 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 17 मिनट |
| W2 | Chapter 15 vakya shuddhi (10th Hindi) | 🔎 review हो रहा है | 7 मिनट |
| W3 | Chapter 16 rikt sthan vakya kram (10th Hindi) | ✍️ लिख रहा है | 17 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 6 |
| key 4 | 3 |
| key 5 | 6 |
| key 6 | 8 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 15 | 0 | 2 |
| 12th Computer | 14 | 0 | 0 |
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
| **कुल** | **325** | **0** | **2** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
21-11 07:44:33 autopilot start: 12 workers, reverse=False
21-11 07:44:33 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
21-11 07:44:34 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_07_sandhi (TODO: todo 5, problems 0)
21-11 07:44:35   [sandhi] Hindi-only writer: direct Hindi content; English generation and translation disabled
21-11 07:44:39 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_15_vakya_shuddhi (TODO: todo 1, problems 0)
21-11 07:44:39   [vakya_shuddhi] Hindi-only writer: direct Hindi content; English generation and translation disabled
21-11 07:44:44 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_16_rikt_sthan_vakya_kram (TODO: todo 4, problems 0)
21-11 07:44:44   [rikt_sthan_vakya_kram] Hindi-only writer: direct Hindi content; English generation and translation disabled
21-11 07:45:05 worker 3: nothing left
21-11 07:45:21 worker 4: nothing left
21-11 07:45:38 worker 5: nothing left
21-11 07:45:54 worker 6: nothing left
21-11 07:45:57   [sandhi] Practice_hi_Set_01.txt try 1: rejected (Q6:duplicate_options,Q8:duplicate_options,Q10:duplicate_options,Q12:duplicate_options,Q14:duplicate_options)
21-11 07:46:11 worker 7: nothing left
21-11 07:46:27 worker 8: nothing left
21-11 07:46:44 worker 9: nothing left
21-11 07:47:00 worker 10: nothing left
21-11 07:47:17 worker 11: nothing left
21-11 07:47:50   [vakya_shuddhi] Practice_hi_Set_06.txt try 1: re-solve disagrees (Q139 key a vs re-solve c)
21-11 07:50:25   [vakya_shuddhi] Practice_hi_Set_06.txt try 2: re-solve disagrees (Q133 key a vs re-solve ?, Q146 key c vs re-solve ?, Q150 key d vs re-solve ?)
21-11 07:51:38   [rikt_sthan_vakya_kram] Practice_hi_Set_03.txt try 1: re-solve disagrees (Q54 key c vs re-solve a, Q61 key b vs re-solve c, Q62 key c vs re-solve a, Q64 key d vs re-solve b, 
21-11 07:55:03   [vakya_shuddhi] wrote Practice_hi_Set_06.txt (write, 25 MCQs)
21-11 07:55:03   [vakya_shuddhi] written 1, failed 0; AI calls today 14/100000
21-11 07:56:06   [vakya_shuddhi] review Content_hi.txt round 1: 7 issue(s): - केस मार्कर तालिका में साधारण भूतकाल में "ने" न लगने का नियम गलत है; अन्योन्यक्रियात्मक क्रियाओं (जैसे खाय
21-11 07:59:01   [vakya_shuddhi] review Content_hi.txt round 2: 5 issue(s): - In the Case Markers table, the entry for कर्म incorrectly labels "मैं पुस्तक पढ़ता हूँ" as a mistake; "को
21-11 08:01:31   [vakya_shuddhi] REJECTED review fix Content_hi.txt: reviewer still reports - In the Pronoun-Antecedent Agreement table, the example "सीता अपने भाई को बुलाई" is incorr
21-11 08:02:02   [vakya_shuddhi] review Key_Facts_hi.txt round 1: 2 issue(s): - Point 4 example “मैंने उस किताब को पढ़ा” uses the masculine past verb “पढ़ा” for the feminine object “क
21-11 08:02:35   [sandhi] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q2 key d vs re-solve a, Q4 key a vs re-solve b, Q6 key d vs re-solve b, Q7 key c vs re-solve b, Q8 k
```
