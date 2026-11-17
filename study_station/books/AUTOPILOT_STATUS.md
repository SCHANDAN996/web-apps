# 📚 Book Autopilot — लाइव स्थिति (six-chapters)

**आख़िरी update:** 17-11-2026 04:01 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 17-11 03:45 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | ✍️ लिख रहा है | 16 मिनट |
| W2 | Chapter 02 shabd bhed (10th Hindi) | 🔎 review हो रहा है | 16 मिनट |
| W3 | Chapter 03 sangya sarvanam (10th Hindi) | ✍️ लिख रहा है | 16 मिनट |
| W4 | Chapter 04 visheshan kriya (10th Hindi) | ✍️ लिख रहा है | 16 मिनट |
| W5 | Chapter 04 software os (12th Computer) | 🔎 review हो रहा है | 7 मिनट |
| W6 | Chapter 05 ling vachan karak (10th Hindi) | ✍️ लिख रहा है | 15 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 29 |
| key 4 | 16 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 1 | 0 | 16 |
| 12th Computer | 5 | 0 | 9 |
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
| **कुल** | **302** | **0** | **25** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
17-11 15:45:02 autopilot start: 6 workers, reverse=False
17-11 15:45:02 API policy: account start interval=10s; key start interval=15s; in-flight per key=2
17-11 15:45:02 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (TODO: todo 4, problems 0)
17-11 15:45:03   [varn_vartani] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 15:45:08 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_02_shabd_bhed (OK: todo 0, problems 0)
17-11 15:45:13 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (TODO: todo 2, problems 0)
17-11 15:45:13   [sangya_sarvanam] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 15:45:18 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya (TODO: todo 4, problems 0)
17-11 15:45:18   [visheshan_kriya] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 15:45:23 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_04_software_os (TODO: todo 2, problems 0)
17-11 15:45:28 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (TODO: todo 6, problems 0)
17-11 15:45:28   [ling_vachan_karak] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 15:46:13   [varn_vartani] Practice_hi_Set_01.txt try 1: rejected (parsed 24 questions, numbers 1…25)
17-11 15:46:43   [ling_vachan_karak] Practice_hi_Set_01.txt try 1: rejected (Q18:duplicate_options,Q25:duplicate_options)
17-11 15:47:08   [varn_vartani] Practice_hi_Set_01.txt try 2: rejected (Q13:duplicate_options)
17-11 15:47:41   [varn_vartani] Practice_hi_Set_01.txt try 3: rejected (Q13:duplicate_options)
17-11 15:47:56   [shabd_bhed] 2026-11-17 10:17:56,339 WARNING NVIDIA rate_limited — retrying in 20s
17-11 15:48:38   [sangya_sarvanam] Practice_hi_Set_01.txt try 1: re-solve disagrees (Q5 key a vs re-solve b, Q14 key b vs re-solve a, Q20 key c vs re-solve a)
17-11 15:49:00   [varn_vartani] Practice_hi_Set_01.txt try 4: rejected (Q13:duplicate_options)
17-11 15:49:00   [varn_vartani] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
17-11 15:49:01   [visheshan_kriya] Practice_hi_Set_01.txt try 1: re-solve disagrees (Q13 key a vs re-solve c, Q23 key b vs re-solve d)
17-11 15:49:37   [shabd_bhed] review Key_Facts_hi.txt: 1 issue(s): - Point 18 incorrectly states that some words are considered नपुंसकलिंग (neuter) in Hindi; Hindi grammar recogniz
17-11 15:50:16   [varn_vartani] Practice_hi_Set_02.txt try 1: rejected (Q26:duplicate_options,Q38:duplicate_options)
17-11 15:51:35   [software_os] wrote Practice_en_Set_01.txt (write, 25 MCQs)
17-11 15:51:42   [visheshan_kriya] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q13 key a vs re-solve c, Q23 key d vs re-solve b)
17-11 15:52:19   [sangya_sarvanam] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q5 key c vs re-solve b, Q20 key c vs re-solve a)
17-11 15:52:19   [software_os] Practice_hi_Set_01.txt try 1: rejected (parsed 25 questions, numbers 51…75)
17-11 15:53:21   [software_os] wrote Practice_hi_Set_01.txt (translate from Practice_en_Set_01.txt, 25 MCQs)
17-11 15:53:22   [software_os] written 2, failed 0; AI calls today 27/100000
17-11 15:53:22   [visheshan_kriya] 2026-11-17 10:23:22,173 WARNING NVIDIA rate_limited — retrying in 20s
17-11 15:53:49   [ling_vachan_karak] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q4 key d vs re-solve a, Q12 key c vs re-solve d, Q19 key c vs re-solve a, Q25 key b vs re-solve d)
17-11 15:55:21   [sangya_sarvanam] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q5 key c vs re-solve b)
17-11 15:55:22   [software_os] review Content_en.txt: 1 issue(s): - Distributed OS examples (Google Borg, Kubernetes) are incorrect; they are cluster manager and container orchestra
17-11 15:55:36   [software_os] 2026-11-17 10:25:36,322 WARNING NVIDIA rate_limited — retrying in 20s
17-11 15:57:22   [sangya_sarvanam] Practice_hi_Set_01.txt try 4: re-solve disagrees (Q5 key c vs re-solve b)
17-11 15:57:22   [sangya_sarvanam] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
17-11 15:58:20   [sangya_sarvanam] Practice_hi_Set_05.txt try 1: rejected (Q111:duplicate_options,Q114:duplicate_options,Q125:duplicate_options)
17-11 15:58:36   [shabd_bhed] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 5 incorrectly lists “सार्वनामिक विशेषण” as a sub‑type of सर्वनाम; it is a sub‑typ
17-11 15:58:53   [visheshan_kriya] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q13 key a vs re-solve c, Q23 key d vs re-solve b)
```
