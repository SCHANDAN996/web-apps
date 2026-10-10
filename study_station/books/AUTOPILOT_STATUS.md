# 📚 Book Autopilot — लाइव स्थिति (lane-1)

**आख़िरी update:** 10-10-2026 11:41 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 10-10 09:07 PM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

⏸️ अभी कोई worker नहीं चल रहा (रुका हुआ या सब पूरा)।

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th GK | 19 | 0 | 0 |
| 10th Reasoning | 22 | 0 | 0 |
| 10th Maths | 22 | 0 | 0 |
| 10th English | 18 | 0 | 2 |
| 12th Maths | 20 | 0 | 3 |
| 12th GK | 22 | 0 | 2 |
| 12th Reasoning | 19 | 0 | 6 |
| 12th English | 25 | 0 | 0 |
| Graduation Maths | 25 | 0 | 3 |
| Graduation GK | 27 | 0 | 1 |
| Graduation Reasoning | 26 | 2 | 2 |
| Graduation English | 29 | 1 | 0 |
| **कुल** | **274** | **3** | **19** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 13 Dictionary Order (Reasoning) — 2 बार
- Chapter 12 Missing Term (Reasoning) — 2 बार
- Chapter 22 Para Jumbles Adv (English) — 2 बार
- Chapter 25 Statement Argument (Reasoning) — 2 बार
- Chapter 30 Advanced Puzzles (Reasoning) — 2 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
10-10 21:54:20   [Dictionary_Order] FAILED Practice_en_Set_06.txt: network
10-10 21:54:20   [Dictionary_Order] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
10-10 21:54:20   [Dictionary_Order] written 0, failed 2; AI calls today 2/100000
10-10 21:54:20 NOT OK Graduation_Level/Reasoning/Chapter_25_Statement_Argument after 46 min: todo [] problems ['PYQ_hi.txt: much shorter than the English section (10814 vs ']
10-10 21:54:23 NOT OK Graduation_Level/Reasoning/Chapter_13_Dictionary_Order after 23 min: todo ['Set 06 en: todo', 'Set 06 hi: todo'] problems []
10-10 21:54:23 START Graduation_Level/Reasoning/Chapter_25_Statement_Argument (FIX: todo 0, problems 1)
10-10 21:54:25 START Graduation_Level/Reasoning/Chapter_30_Advanced_Puzzles (TODO: todo 2, problems 1)
10-10 22:12:51   [Advanced_Puzzles] FAILED Practice_en_Set_06.txt: network
10-10 22:12:51   [Advanced_Puzzles] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
10-10 22:12:51   [Advanced_Puzzles] written 0, failed 2; AI calls today 3/100000
10-10 22:12:51 NOT OK Graduation_Level/Reasoning/Chapter_30_Advanced_Puzzles after 18 min: todo ['Set 06 en: todo', 'Set 06 hi: todo'] problems ['Important_Rules_hi.txt: much shorter than the English sectio']
10-10 22:12:53 START Graduation_Level/Reasoning/Chapter_30_Advanced_Puzzles (TODO: todo 2, problems 1)
10-10 22:16:17   [Missing_Term] FAILED Important_Rules_hi.txt: network
10-10 22:16:17   [Missing_Term] written 0, failed 1; AI calls today 3/100000
10-10 22:16:55   [Statement_Argument] FAILED PYQ_hi.txt: network
10-10 22:16:55   [Statement_Argument] written 0, failed 1; AI calls today 3/100000
10-10 22:17:09   [Para_Jumbles_Adv] FAILED Mind_Map_hi.txt: network
10-10 22:17:09   [Para_Jumbles_Adv] written 0, failed 1; AI calls today 3/100000
10-10 22:26:16   [Advanced_Puzzles] Practice_en_Set_06.txt try 1: rejected (Q126:leaked_reasoning,Q128:leaked_reasoning,Q129:leaked_reasoning,Q132:leaked_reasoning,Q140:leaked_reasoning)
10-10 22:39:30   [Statement_Argument] FAILED PYQ_hi.txt: network
10-10 22:39:30   [Statement_Argument] written 0, failed 1; AI calls today 5/100000
10-10 22:39:30 NOT OK Graduation_Level/Reasoning/Chapter_25_Statement_Argument after 45 min: todo [] problems ['PYQ_hi.txt: much shorter than the English section (10814 vs ']
10-10 22:39:32 worker 3: nothing left
10-10 22:40:24   [Para_Jumbles_Adv] repaired Mind_Map_hi.txt (1273 chars)
10-10 22:40:24   [Para_Jumbles_Adv] written 1, failed 0; AI calls today 5/100000
10-10 22:40:25 NOT OK Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_22_Para_Jumbles_Adv after 47 min: todo [] problems ['Mind_Map_hi.txt: much shorter than the English section (1272']
10-10 22:40:27 worker 0: nothing left
10-10 22:41:06   [Missing_Term] repaired Important_Rules_hi.txt (3332 chars)
10-10 22:41:06   [Missing_Term] written 1, failed 0; AI calls today 5/100000
10-10 22:41:06 NOT OK Graduation_Level/Reasoning/Chapter_12_Missing_Term after 48 min: todo [] problems ['Important_Rules_hi.txt: much shorter than the English sectio']
10-10 22:41:09 worker 1: nothing left
10-10 22:52:05   [Advanced_Puzzles] Practice_en_Set_06.txt try 2: re-solve disagrees (Q130 key b vs re-solve c)
10-10 23:18:39   [Advanced_Puzzles] Practice_en_Set_06.txt try 3: re-solve disagrees (Q128 key a vs re-solve b, Q139 key d vs re-solve a)
10-10 23:33:06   [Advanced_Puzzles] Practice_en_Set_06.txt try 4: rejected (parsed 0 questions, numbers -…-)
10-10 23:33:06   [Advanced_Puzzles] REJECTED Practice_en_Set_06.txt: no version passed the checks — not written
10-10 23:33:06   [Advanced_Puzzles] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
10-10 23:33:06   [Advanced_Puzzles] written 0, failed 2; AI calls today 8/100000
10-10 23:33:06 NOT OK Graduation_Level/Reasoning/Chapter_30_Advanced_Puzzles after 80 min: todo ['Set 06 en: todo', 'Set 06 hi: todo'] problems ['Important_Rules_hi.txt: much shorter than the English sectio']
10-10 23:33:09 worker 2: nothing left
10-10 23:41:07 autopilot end: done 0, failed 5
```
