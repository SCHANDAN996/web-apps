# 📚 Book Autopilot — लाइव स्थिति (three-chapters)

**आख़िरी update:** 17-11-2026 02:29 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 17-11 01:57 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | ✍️ लिख रहा है | 31 मिनट |
| W2 | Chapter 02 shabd bhed (10th Hindi) | 🔎 review हो रहा है | 8 मिनट |
| W3 | Chapter 03 sangya sarvanam (10th Hindi) | ✍️ लिख रहा है | 31 मिनट |

**बाकी साथ चल रहे runs:** [RATE_POLICY](autopilot/RATE_POLICY.md) · [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 1 | 0 | 16 |
| 12th Computer | 4 | 0 | 10 |
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
| **कुल** | **301** | **0** | **26** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
17-11 13:57:47 autopilot start: 3 workers, reverse=False
17-11 13:57:47 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (TODO: todo 4, problems 0)
17-11 13:57:48   [varn_vartani] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 13:57:53 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_02_shabd_bhed (TODO: todo 3, problems 0)
17-11 13:57:53   [shabd_bhed] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 13:57:58 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (TODO: todo 4, problems 0)
17-11 13:57:58   [sangya_sarvanam] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 13:58:36   [varn_vartani] Practice_hi_Set_01.txt try 1: rejected (Q15:duplicate_options,Q23:duplicate_options)
17-11 14:00:48   [shabd_bhed] Practice_hi_Set_02.txt try 1: re-solve disagrees (Q43 key b vs re-solve a)
17-11 14:01:04   [sangya_sarvanam] Practice_hi_Set_01.txt try 1: rejected (Q5:duplicate_options)
17-11 14:03:14   [varn_vartani] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q17 key b vs re-solve c, Q18 key c vs re-solve ?, Q24 key a vs re-solve b)
17-11 14:04:42   [shabd_bhed] Practice_hi_Set_02.txt try 2: re-solve disagrees (Q43 key d vs re-solve b)
17-11 14:11:08   [shabd_bhed] wrote Practice_hi_Set_02.txt (write, 25 MCQs)
17-11 14:11:59   [shabd_bhed] Practice_hi_Set_03.txt try 1: rejected (parsed 21 questions, numbers 51…72)
17-11 14:12:17   [varn_vartani] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q24 key a vs re-solve c)
17-11 14:13:42   [shabd_bhed] Practice_hi_Set_03.txt try 2: re-solve disagrees (Q57 key b vs re-solve a, Q66 key c vs re-solve a)
17-11 14:14:22   [sangya_sarvanam] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q5 key c vs re-solve b)
17-11 14:17:50   [shabd_bhed] wrote Practice_hi_Set_03.txt (write, 25 MCQs)
17-11 14:17:58   [varn_vartani] Practice_hi_Set_01.txt try 4: re-solve disagrees (Q1 key d vs re-solve b)
17-11 14:17:58   [varn_vartani] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
17-11 14:20:09   [shabd_bhed] wrote Practice_hi_Set_04.txt (write, 25 MCQs)
17-11 14:20:09   [shabd_bhed] written 3, failed 0; AI calls today 30/100000
17-11 14:21:04   [shabd_bhed] review Content_hi.txt: 5 issue(s): - सर्वनाम खंड में "वह" को "वह लड़का" में संज्ञा बताया गया है → "वह" यहाँ सार्वनामिक विशेषण (विशेषण) है, संज्ञा नहीं
17-11 14:23:20   [sangya_sarvanam] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q13 key c vs re-solve ?, Q14 key c vs re-solve a, Q25 key a vs re-solve ?)
17-11 14:24:16   [varn_vartani] Practice_hi_Set_02.txt try 1: rejected (parsed 13 questions, numbers 26…40)
17-11 14:25:56   [shabd_bhed] review Key_Facts_hi.txt: 1 issue(s): - Point 18: 'आम्र' given as the feminine form of 'आम' is incorrect; Hindi does not use 'आम्र' as a feminine noun 
17-11 14:26:28   [varn_vartani] Practice_hi_Set_02.txt try 2: rejected (Q27:duplicate_options,Q28:duplicate_options,Q29:duplicate_options,Q30:duplicate_options,Q32:duplicate_options)
17-11 14:27:15   [shabd_bhed] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 18 incorrectly states that some words are considered neuter (नपुंसकलिंग) in Hindi
17-11 14:27:38   [shabd_bhed] review Feynman_hi.txt: 1 issue(s): - परिचय में दिया गया मेमोनिक (सर्वनाम विशेषण क्रिया अव्यय सम्बन्ध सूचक विस्मयादिबोधक संज्ञा) ८ भेदों से मेल नहीं खा
17-11 14:28:14   [sangya_sarvanam] Practice_hi_Set_01.txt try 4: re-solve disagrees (Q16 key c vs re-solve a, Q25 key c vs re-solve ?)
17-11 14:28:14   [sangya_sarvanam] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
```
