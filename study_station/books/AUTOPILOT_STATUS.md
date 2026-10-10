# 📚 Book Autopilot — लाइव स्थिति (lane-1)

**आख़िरी update:** 11-10-2026 12:49 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 11-10 12:03 AM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W5 | Chapter 30 Advanced Puzzles (Graduation Reasoning) | 🔧 सुधार रहा है | 6 मिनट |

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
| Graduation Reasoning | 26 | 3 | 1 |
| Graduation English | 29 | 1 | 0 |
| **कुल** | **274** | **4** | **18** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 22 Para Jumbles Adv (English) — 2 बार
- Chapter 25 Statement Argument (Reasoning) — 2 बार
- Chapter 13 Dictionary Order (Reasoning) — 2 बार
- Chapter 12 Missing Term (Reasoning) — 2 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
11-10 00:16:02   [Statement_Argument] written 1, failed 0; AI calls today 12/100000
11-10 00:17:59   [Dictionary_Order] FAILED Practice_en_Set_06.txt: too_long
11-10 00:17:59   [Dictionary_Order] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
11-10 00:17:59   [Dictionary_Order] written 0, failed 2; AI calls today 12/100000
11-10 00:17:59 NOT OK Graduation_Level/Reasoning/Chapter_13_Dictionary_Order after 15 min: todo ['Set 06 en: todo', 'Set 06 hi: todo'] problems []
11-10 00:18:01 START Graduation_Level/Reasoning/Chapter_13_Dictionary_Order (TODO: todo 2, problems 0)
11-10 00:18:30   [Statement_Argument] repaired PYQ_hi.txt (7713 chars)
11-10 00:18:30   [Statement_Argument] written 1, failed 0; AI calls today 13/100000
11-10 00:18:30 NOT OK Graduation_Level/Reasoning/Chapter_25_Statement_Argument after 5 min: todo [] problems ['PYQ_hi.txt: much shorter than the English section (7712 vs 4']
11-10 00:18:32 worker 3: nothing left
11-10 00:19:29   [Advanced_Puzzles] Practice_en_Set_06.txt try 1: re-solve disagrees (Q144 key b vs re-solve a)
11-10 00:20:03   [Missing_Term] FAILED Important_Rules_hi.txt: too_long
11-10 00:20:03   [Missing_Term] written 0, failed 1; AI calls today 13/100000
11-10 00:20:03 NOT OK Graduation_Level/Reasoning/Chapter_12_Missing_Term after 17 min: todo [] problems ['Important_Rules_hi.txt: much shorter than the English sectio']
11-10 00:20:04 START Graduation_Level/Reasoning/Chapter_12_Missing_Term (FIX: todo 0, problems 1)
11-10 00:21:10   [Missing_Term] repaired Important_Rules_hi.txt (3971 chars)
11-10 00:21:10   [Missing_Term] written 1, failed 0; AI calls today 14/100000
11-10 00:22:22   [Missing_Term] repaired Important_Rules_hi.txt (3420 chars)
11-10 00:22:22   [Missing_Term] written 1, failed 0; AI calls today 16/100000
11-10 00:22:22 NOT OK Graduation_Level/Reasoning/Chapter_12_Missing_Term after 2 min: todo [] problems ['Important_Rules_hi.txt: much shorter than the English sectio']
11-10 00:22:24 worker 1: nothing left
11-10 00:24:40   [Para_Jumbles_Adv] FAILED Mind_Map_hi.txt: too_long
11-10 00:24:40   [Para_Jumbles_Adv] written 0, failed 1; AI calls today 15/100000
11-10 00:24:40 NOT OK Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_22_Para_Jumbles_Adv after 16 min: todo [] problems ['Mind_Map_hi.txt: much shorter than the English section (1150']
11-10 00:24:43 worker 0: nothing left
11-10 00:25:02   [Dictionary_Order] Practice_en_Set_06.txt try 1: rejected (Q126:leaked_reasoning,Q127:leaked_reasoning,Q133:leaked_reasoning,Q137:leaked_reasoning,Q139:leaked_reasoning)
11-10 00:26:05   [Advanced_Puzzles] wrote Practice_en_Set_06.txt (write, 25 MCQs)
11-10 00:26:35   [Advanced_Puzzles] Practice_hi_Set_06.txt try 1: rejected (parsed 0 questions, numbers -…-)
11-10 00:29:33   [Advanced_Puzzles] wrote Practice_hi_Set_06.txt (translate from Practice_en_Set_06.txt, 25 MCQs)
11-10 00:29:33   [Advanced_Puzzles] written 2, failed 0; AI calls today 19/100000
11-10 00:31:51   [Dictionary_Order] Practice_en_Set_06.txt try 2: re-solve disagrees (Q126 key d vs re-solve c, Q130 key c vs re-solve b, Q148 key d vs re-solve b)
11-10 00:33:51   [Dictionary_Order] Practice_en_Set_06.txt try 3: rejected (Q127:leaked_reasoning)
11-10 00:39:50   [Dictionary_Order] Practice_en_Set_06.txt try 4: re-solve disagrees (Q143 key d vs re-solve b)
11-10 00:39:50   [Dictionary_Order] REJECTED Practice_en_Set_06.txt: no version passed the checks — not written
11-10 00:39:50   [Dictionary_Order] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
11-10 00:39:50   [Dictionary_Order] written 0, failed 2; AI calls today 23/100000
11-10 00:39:50 NOT OK Graduation_Level/Reasoning/Chapter_13_Dictionary_Order after 22 min: todo ['Set 06 en: todo', 'Set 06 hi: todo'] problems []
11-10 00:39:52 worker 2: nothing left
11-10 00:43:44   [Advanced_Puzzles] FAILED Important_Rules_hi.txt: too_long
11-10 00:43:44   [Advanced_Puzzles] written 0, failed 1; AI calls today 22/100000
```
