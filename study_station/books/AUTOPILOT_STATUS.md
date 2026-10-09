# 📚 Book Autopilot — लाइव स्थिति (lane-1)

**आख़िरी update:** 09-10-2026 09:43 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 09-10 08:26 AM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 22 Para Jumbles Adv (Graduation English) | ✍️ लिख रहा है | 43 मिनट |
| W2 | Chapter 05 Direction Sense (Graduation Reasoning) | ✍️ लिख रहा है | 9 मिनट |
| W3 | Chapter 07 Sitting Arrangement (Graduation Reasoning) | ✍️ लिख रहा है | 20 मिनट |
| W4 | Chapter 06 Order Ranking (Graduation Reasoning) | ✍️ लिख रहा है | 25 मिनट |
| W5 | Chapter 04 Blood Relations (Graduation Reasoning) | ✍️ लिख रहा है | 76 मिनट |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th GK | 19 | 0 | 0 |
| 10th Reasoning | 22 | 0 | 0 |
| 10th Maths | 9 | 13 | 0 |
| 10th English | 0 | 0 | 20 |
| 12th Maths | 0 | 0 | 23 |
| 12th GK | 13 | 0 | 11 |
| 12th Reasoning | 0 | 0 | 25 |
| 12th English | 21 | 0 | 4 |
| Graduation Maths | 0 | 0 | 28 |
| Graduation GK | 12 | 0 | 16 |
| Graduation Reasoning | 1 | 0 | 29 |
| Graduation English | 29 | 0 | 1 |
| **कुल** | **126** | **13** | **157** |

## ✅ autopilot से हाल में पूरे हुए

- 09-10 09:05 — Graduation English · Chapter 30 Revision Tracker

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 03 Coding Decoding (Reasoning) — 2 बार
- Chapter 22 Para Jumbles Adv (English) — 1 बार
- Chapter 02 Classification (Reasoning) — 2 बार
- Chapter 05 Direction Sense (Reasoning) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
09-10 09:17:14 NOT OK Graduation_Level/Reasoning/Chapter_03_Coding_Decoding after 37 min: todo ['Set 06 en: todo', 'Set 06 hi: todo'] problems ['Content_hi.txt: Hindi file is mostly not in Hindi', 'Content_hi.txt: much shorter than the English section (347 v']
09-10 09:17:16 START Graduation_Level/Reasoning/Chapter_06_Order_Ranking (TODO: todo 7, problems 2)
09-10 09:19:42   [Order_Ranking] wrote Practice_hi_Set_03.txt (translate from Practice_en_Set_03.txt, 25 MCQs)
09-10 09:19:49   [Direction_Sense] wrote Practice_en_Set_02.txt (write, 25 MCQs)
09-10 09:21:19   [Order_Ranking] Practice_en_Set_04.txt try 1: rejected (Q82:leaked_reasoning,Q89:leaked_reasoning,Q99:leaked_reasoning)
09-10 09:22:04   [Direction_Sense] wrote Practice_hi_Set_02.txt (translate from Practice_en_Set_02.txt, 25 MCQs)
09-10 09:22:45   [Blood_Relations] wrote Practice_en_Set_03.txt (write, 25 MCQs)
09-10 09:23:07   [Classification] FAILED Practice_en_Set_06.txt: too_long
09-10 09:23:07   [Classification] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
09-10 09:23:07   [Classification] written 0, failed 3; AI calls today 74/100000
09-10 09:23:07 NOT OK Graduation_Level/Reasoning/Chapter_02_Classification after 22 min: todo ['Set 01 hi: todo', 'Set 06 en: todo', 'Set 06 hi: todo'] problems []
09-10 09:23:08 START Graduation_Level/Reasoning/Chapter_07_Sitting_Arrangement (TODO: todo 25, problems 0)
09-10 09:23:26   [Direction_Sense] Practice_en_Set_05.txt try 1: rejected (Q121:leaked_reasoning)
09-10 09:23:48   [Direction_Sense] Practice_en_Set_05.txt try 2: rejected (parsed 1 questions, numbers 101…101)
09-10 09:24:23   [Sitting_Arrangement] wrote Content_en.txt (8066 chars)
09-10 09:25:11   [Para_Jumbles_Adv] Practice_en_Set_05.txt try 2: re-solve disagrees (Q115 key d vs re-solve b, Q122 key d vs re-solve c)
09-10 09:25:11   [Blood_Relations] wrote Practice_hi_Set_03.txt (translate from Practice_en_Set_03.txt, 25 MCQs)
09-10 09:26:12   [Sitting_Arrangement] wrote Content_hi.txt (6379 chars)
09-10 09:27:39   [Direction_Sense] Practice_en_Set_05.txt try 3: rejected (Q115:leaked_reasoning,Q125:leaked_reasoning)
09-10 09:27:42   [Sitting_Arrangement] Feynman_en.txt try 1: rejected (chat debris "Here's the")
09-10 09:27:52   [Blood_Relations] Practice_en_Set_05.txt try 1: rejected (Q122:leaked_reasoning)
09-10 09:28:11   [Sitting_Arrangement] Feynman_en.txt try 2: rejected (chat debris "Here's the")
09-10 09:28:11   [Sitting_Arrangement] REJECTED Feynman_en.txt: chat debris "Here's the" — not written
09-10 09:29:44   [Blood_Relations] Practice_en_Set_05.txt try 2: rejected (Q115:leaked_reasoning)
09-10 09:30:21   [Direction_Sense] Practice_en_Set_05.txt try 4: re-solve disagrees (Q103 key a vs re-solve d, Q105 key d vs re-solve b, Q114 key a vs re-solve b, Q116 key b vs re-solve
09-10 09:30:21   [Direction_Sense] REJECTED Practice_en_Set_05.txt: no version passed the checks — not written
09-10 09:30:21   [Direction_Sense] skip Practice_hi_Set_05.txt: its pair Practice_en_Set_05.txt was not written
09-10 09:32:55   [Order_Ranking] Practice_en_Set_04.txt try 2: re-solve disagrees (Q82 key a vs re-solve ?, Q86 key b vs re-solve ?)
09-10 09:33:12   [Para_Jumbles_Adv] Practice_en_Set_05.txt try 3: re-solve disagrees (Q103 key c vs re-solve b)
09-10 09:33:16   [Direction_Sense] wrote Practice_hi_Set_06.txt (translate from Practice_en_Set_06.txt, 25 MCQs)
09-10 09:33:16   [Direction_Sense] written 3, failed 2; AI calls today 93/100000
09-10 09:33:16 NOT OK Graduation_Level/Reasoning/Chapter_05_Direction_Sense after 28 min: todo ['Set 05 en: todo', 'Set 05 hi: todo'] problems ['Important_Rules_hi.txt: Hindi file is mostly not in Hindi', 'PYQ_en.txt: English file contains a lot of Hindi']
09-10 09:33:17 START Graduation_Level/Reasoning/Chapter_05_Direction_Sense (TODO: todo 2, problems 2)
09-10 09:35:05   [Direction_Sense] Practice_en_Set_05.txt try 1: rejected (Q114:leaked_reasoning)
09-10 09:35:53   [Order_Ranking] Practice_en_Set_04.txt try 3: re-solve disagrees (Q82 key b vs re-solve c)
09-10 09:39:57   [Blood_Relations] Practice_en_Set_05.txt try 3: re-solve disagrees (Q121 key a vs re-solve -, Q122 key a vs re-solve -, Q123 key d vs re-solve -, Q124 key d vs re-solve
09-10 09:41:00   [Direction_Sense] Practice_en_Set_05.txt try 2: re-solve disagrees (Q114 key d vs re-solve ?)
09-10 09:43:12   [Order_Ranking] Practice_en_Set_04.txt try 4: re-solve disagrees (Q82 key c vs re-solve b)
09-10 09:43:12   [Order_Ranking] REJECTED Practice_en_Set_04.txt: no version passed the checks — not written
09-10 09:43:12   [Order_Ranking] skip Practice_hi_Set_04.txt: its pair Practice_en_Set_04.txt was not written
```
