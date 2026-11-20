# 📚 Book Autopilot — लाइव स्थिति (twelve-chapters)

**आख़िरी update:** 20-11-2026 04:43 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 20-11 04:41 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 1 मिनट |
| W2 | Chapter 09 upsarg pratyay (10th Hindi) | 🔎 review हो रहा है | 1 मिनट |
| W3 | Chapter 12 anekarthi samshrut (10th Hindi) | 🔎 review हो रहा है | 1 मिनट |
| W4 | Chapter 12 e banking (12th Computer) | 🔎 review हो रहा है | 1 मिनट |
| W5 | Chapter 13 ek shabd (10th Hindi) | ✍️ लिख रहा है | 1 मिनट |
| W6 | Chapter 14 muhavare lokokti (10th Hindi) | 🔎 review हो रहा है | 0 मिनट |
| W7 | Chapter 15 vakya shuddhi (10th Hindi) | ✍️ लिख रहा है | 0 मिनट |
| W8 | Chapter 16 rikt sthan vakya kram (10th Hindi) | ✍️ लिख रहा है | 0 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 1 |
| key 4 | 2 |
| key 5 | 1 |
| key 6 | 1 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 13 | 0 | 4 |
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
| **कुल** | **323** | **0** | **4** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
20-11 16:41:56 autopilot start: 12 workers, reverse=False
20-11 16:41:56 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
20-11 16:41:56 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_07_sandhi (TODO: todo 5, problems 0)
20-11 16:41:57   [sandhi] Hindi-only writer: direct Hindi content; English generation and translation disabled
20-11 16:42:01 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_09_upsarg_pratyay (OK: todo 0, problems 0)
20-11 16:42:01   [upsarg_pratyay] review Flashcards_hi.txt: resumed private correction draft
20-11 16:42:06 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_12_anekarthi_samshrut (OK: todo 0, problems 0)
20-11 16:42:07   [anekarthi_samshrut] review Content_hi.txt: resumed private correction draft
20-11 16:42:11 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_12_e_banking (OK: todo 0, problems 0)
20-11 16:42:12   [e_banking] review Content_en.txt: resumed private correction draft
20-11 16:42:16 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_13_ek_shabd (TODO: todo 3, problems 0)
20-11 16:42:17   [ek_shabd] Hindi-only writer: direct Hindi content; English generation and translation disabled
20-11 16:42:21 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_14_muhavare_lokokti (OK: todo 0, problems 0)
20-11 16:42:22   [muhavare_lokokti] review Key_Facts_hi.txt: resumed private correction draft
20-11 16:42:27 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_15_vakya_shuddhi (TODO: todo 6, problems 0)
20-11 16:42:27   [vakya_shuddhi] Hindi-only writer: direct Hindi content; English generation and translation disabled
20-11 16:42:31 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_16_rikt_sthan_vakya_kram (TODO: todo 6, problems 0)
20-11 16:42:32   [rikt_sthan_vakya_kram] Hindi-only writer: direct Hindi content; English generation and translation disabled
20-11 16:42:50 worker 8: nothing left
20-11 16:43:04 worker 9: nothing left
20-11 16:43:18   [ek_shabd] Practice_hi_Set_01.txt try 1: rejected (parsed 24 questions, numbers 1…25)
20-11 16:43:18 worker 10: nothing left
20-11 16:43:33 worker 11: nothing left
20-11 16:43:36   [sandhi] Practice_hi_Set_01.txt try 1: rejected (parsed 24 questions, numbers 1…25)
```
