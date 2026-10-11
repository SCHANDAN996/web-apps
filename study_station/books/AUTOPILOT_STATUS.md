# 📚 Book Autopilot — लाइव स्थिति (lane-1)

**आख़िरी update:** 11-10-2026 08:22 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 11-10 07:05 AM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W2 | Chapter 25 Statement Argument (Graduation Reasoning) | 🔧 सुधार रहा है | 4 मिनट |
| W3 | Chapter 13 Dictionary Order (Graduation Reasoning) | ✍️ लिख रहा है | 7 मिनट |

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
| 12th Reasoning | 21 | 0 | 4 |
| 12th English | 25 | 0 | 0 |
| Graduation Maths | 25 | 0 | 3 |
| Graduation GK | 27 | 0 | 1 |
| Graduation Reasoning | 27 | 2 | 1 |
| Graduation English | 29 | 1 | 0 |
| **कुल** | **277** | **3** | **16** |

## ✅ autopilot से हाल में पूरे हुए

- 11-10 08:17 — Graduation Reasoning · Chapter 30 Advanced Puzzles

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 22 Para Jumbles Adv (English) — 4 बार
- Chapter 12 Missing Term (Reasoning) — 4 बार
- Chapter 13 Dictionary Order (Reasoning) — 3 बार
- Chapter 25 Statement Argument (Reasoning) — 3 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
11-10 07:52:51   [Advanced_Puzzles] written 1, failed 0; AI calls today 32/100000
11-10 07:54:33   [Advanced_Puzzles] review Feynman_hi.txt: 1 issue(s): - "90% छात्र फँसते हैं" is an invented exam statistic → Replace with a non-specific phrase like "कई छात्र फँसते हैं
11-10 07:55:42   [Statement_Argument] repaired PYQ_hi.txt (2096 chars)
11-10 07:55:42   [Statement_Argument] written 1, failed 0; AI calls today 38/100000
11-10 07:56:53   [Dictionary_Order] Practice_en_Set_06.txt try 4: re-solve disagrees (Q143 key b vs re-solve c)
11-10 07:56:53   [Dictionary_Order] REJECTED Practice_en_Set_06.txt: no version passed the checks — not written
11-10 07:56:53   [Dictionary_Order] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
11-10 07:56:53   [Dictionary_Order] written 0, failed 2; AI calls today 40/100000
11-10 07:56:53 NOT OK Graduation_Level/Reasoning/Chapter_13_Dictionary_Order after 22 min: todo ['Set 06 en: todo', 'Set 06 hi: todo'] problems []
11-10 07:56:56 START Graduation_Level/Reasoning/Chapter_13_Dictionary_Order (TODO: todo 2, problems 0)
11-10 07:58:13   [Advanced_Puzzles] review Flashcards_en.txt: 1 issue(s): - Card 8: Claims outward-facing "immediate left" moves clockwise → Outward-facing "immediate left" moves anticlo
11-10 08:00:03   [Statement_Argument] repaired PYQ_hi.txt (8637 chars)
11-10 08:00:03   [Statement_Argument] written 1, failed 0; AI calls today 45/100000
11-10 08:00:04 NOT OK Graduation_Level/Reasoning/Chapter_25_Statement_Argument after 8 min: todo [] problems ['PYQ_hi.txt: much shorter than the English section (8636 vs 4']
11-10 08:00:07 START Graduation_Level/Reasoning/Chapter_25_Statement_Argument (FIX: todo 0, problems 1)
11-10 08:00:17   [Dictionary_Order] Practice_en_Set_06.txt try 1: rejected (Q126:leaked_reasoning,Q132:leaked_reasoning,Q133:leaked_reasoning,Q143:leaked_reasoning,Q144:leaked_reasoning)
11-10 08:01:32   [Advanced_Puzzles] review PYQ_en.txt: 1 issue(s): - Q3 solution states "With outward-facing, 'left' becomes clockwise" → For outward-facing, left is anti-clockwise (coun
11-10 08:03:44   [Dictionary_Order] Practice_en_Set_06.txt try 2: rejected (parsed 0 questions, numbers -…-)
11-10 08:05:25   [Statement_Argument] repaired PYQ_hi.txt (16086 chars)
11-10 08:05:25   [Statement_Argument] written 1, failed 0; AI calls today 49/100000
11-10 08:08:12   [Dictionary_Order] Practice_en_Set_06.txt try 3: rejected (Q128:leaked_reasoning,Q130:leaked_reasoning,Q131:leaked_reasoning,Q132:leaked_reasoning,Q134:leaked_reasoning)
11-10 08:08:42   [Advanced_Puzzles] review PYQ_hi.txt: 2 issue(s): - Question 1 (floor puzzle) answer (b) U is not uniquely determined from the given conditions; both U and T can occupy 
11-10 08:09:24   [Statement_Argument] repaired PYQ_hi.txt (2522 chars)
11-10 08:09:24   [Statement_Argument] written 1, failed 0; AI calls today 53/100000
11-10 08:09:24 NOT OK Graduation_Level/Reasoning/Chapter_25_Statement_Argument after 9 min: todo [] problems ['PYQ_hi.txt: much shorter than the English section (2521 vs 4']
11-10 08:09:27 START Graduation_Level/Reasoning/Chapter_25_Statement_Argument (FIX: todo 0, problems 1)
11-10 08:14:39   [Advanced_Puzzles] review Short_Tricks_hi.txt: 1 issue(s): - Trick 8 rule incorrectly states “केंद्र की ओर मुख हो तो बाएँ-दाएँ घड़ी-विपरीत सोचो”; for persons facing the 
11-10 08:15:08   [Dictionary_Order] Practice_en_Set_06.txt try 4: re-solve disagrees (Q142 key a vs re-solve c)
11-10 08:15:08   [Dictionary_Order] REJECTED Practice_en_Set_06.txt: no version passed the checks — not written
11-10 08:15:08   [Dictionary_Order] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
11-10 08:15:08   [Dictionary_Order] written 0, failed 2; AI calls today 58/100000
11-10 08:15:09 NOT OK Graduation_Level/Reasoning/Chapter_13_Dictionary_Order after 18 min: todo ['Set 06 en: todo', 'Set 06 hi: todo'] problems []
11-10 08:15:11 START Graduation_Level/Reasoning/Chapter_13_Dictionary_Order (TODO: todo 2, problems 0)
11-10 08:17:06   [Advanced_Puzzles] review: 5 section(s) corrected, 0 failed
11-10 08:17:06   [Advanced_Puzzles] written 5, failed 0; AI calls today 61/100000
11-10 08:17:24 DONE Graduation_Level/Reasoning/Chapter_30_Advanced_Puzzles in 28 min → 681e80c7
11-10 08:17:27 worker 0: nothing left
11-10 08:18:29   [Statement_Argument] repaired PYQ_hi.txt (1730 chars)
11-10 08:18:29   [Statement_Argument] written 1, failed 0; AI calls today 61/100000
11-10 08:19:36   [Dictionary_Order] Practice_en_Set_06.txt try 1: rejected (parsed 0 questions, numbers -…-)
```
