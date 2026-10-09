# 📚 Book Autopilot — लाइव स्थिति (lane-1)

**आख़िरी update:** 10-10-2026 03:46 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 10-10 12:43 AM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 20 Mirror Water Images (Graduation Reasoning) | ✍️ लिख रहा है | 5 मिनट |
| W2 | Chapter 21 Paper Folding Cutting (Graduation Reasoning) | ✍️ लिख रहा है | 132 मिनट |
| W3 | Chapter 07 Sitting Arrangement (Graduation Reasoning) | 🔧 सुधार रहा है | 5 मिनट |
| W4 | Chapter 22 Figure Series (Graduation Reasoning) | ✍️ लिख रहा है | 129 मिनट |
| W5 | Chapter 23 Syllogism (Graduation Reasoning) | ✍️ लिख रहा है | 119 मिनट |
| W6 | Chapter 13 Dictionary Order (Graduation Reasoning) | ✍️ लिख रहा है | 84 मिनट |
| W7 | Chapter 14 Alphabet Questions (Graduation Reasoning) | ✍️ लिख रहा है | 79 मिनट |
| W8 | Chapter 19 Cubes Dice (Graduation Reasoning) | ✍️ लिख रहा है | 71 मिनट |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th GK | 19 | 0 | 0 |
| 10th Reasoning | 22 | 0 | 0 |
| 10th Maths | 20 | 2 | 0 |
| 10th English | 17 | 0 | 3 |
| 12th Maths | 16 | 0 | 7 |
| 12th GK | 22 | 0 | 2 |
| 12th Reasoning | 10 | 0 | 15 |
| 12th English | 25 | 0 | 0 |
| Graduation Maths | 12 | 0 | 16 |
| Graduation GK | 27 | 0 | 1 |
| Graduation Reasoning | 13 | 2 | 15 |
| Graduation English | 29 | 1 | 0 |
| **कुल** | **232** | **5** | **59** |

## ✅ autopilot से हाल में पूरे हुए

- 10-10 01:37 — Graduation Reasoning · Chapter 08 Puzzles

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 22 Para Jumbles Adv (English) — 2 बार
- Chapter 02 Classification (Reasoning) — 2 बार
- Chapter 12 Missing Term (Reasoning) — 2 बार
- Chapter 13 Dictionary Order (Reasoning) — 1 बार
- Chapter 14 Alphabet Questions (Reasoning) — 1 बार
- Chapter 19 Cubes Dice (Reasoning) — 1 बार
- Chapter 07 Sitting Arrangement (Reasoning) — 1 बार
- Chapter 20 Mirror Water Images (Reasoning) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
10-10 02:59:09   [Sitting_Arrangement] review: 5 section(s) corrected, 2 failed
10-10 02:59:09   [Sitting_Arrangement] written 5, failed 2; AI calls today 96/100000
10-10 02:59:09 NOT OK Graduation_Level/Reasoning/Chapter_07_Sitting_Arrangement after 135 min: todo [] problems ['Content_hi.txt: much shorter than the English section (2295 ', 'Feynman_hi.txt: much shorter than the English section (367 v']
10-10 02:59:10   [Syllogism] Feynman_hi.txt try 1: rejected (too short)
10-10 02:59:10 START Graduation_Level/Reasoning/Chapter_07_Sitting_Arrangement (FIX: todo 0, problems 2)
10-10 03:01:07   [Dictionary_Order] Practice_en_Set_03.txt try 4: rejected (Q53:leaked_reasoning,Q54:leaked_reasoning,Q60:leaked_reasoning,Q61:leaked_reasoning,Q65:leaked_reasoning)
10-10 03:01:07   [Dictionary_Order] REJECTED Practice_en_Set_03.txt: no version passed the checks — not written
10-10 03:01:07   [Dictionary_Order] skip Practice_hi_Set_03.txt: its pair Practice_en_Set_03.txt was not written
10-10 03:01:07   [Mirror_Water_Images] Practice_en_Set_06.txt try 2: re-solve disagrees (Q130 key c vs re-solve a, Q145 key d vs re-solve b)
10-10 03:03:05   [Syllogism] wrote Feynman_hi.txt (4025 chars)
10-10 03:04:13   [Alphabet_Questions] Practice_en_Set_04.txt try 1: rejected (Q76:leaked_reasoning,Q77:leaked_reasoning,Q82:leaked_reasoning,Q92:leaked_reasoning,Q93:leaked_reasoning)
10-10 03:06:09   [Paper_Folding_Cutting] FAILED Practice_en_Set_03.txt: too_long
10-10 03:06:09   [Paper_Folding_Cutting] skip Practice_hi_Set_03.txt: its pair Practice_en_Set_03.txt was not written
10-10 03:08:59   [Figure_Series] FAILED Mind_Map.txt: too_long
10-10 03:12:53   [Dictionary_Order] Practice_en_Set_04.txt try 1: rejected (Q81:leaked_reasoning,Q82:leaked_reasoning,Q91:leaked_reasoning,Q94:leaked_reasoning,Q95:leaked_reasoning)
10-10 03:20:55   [Mirror_Water_Images] Practice_en_Set_06.txt try 3: re-solve disagrees (Q137 key b vs re-solve c)
10-10 03:23:53   [Sitting_Arrangement] repaired Content_hi.txt (6635 chars)
10-10 03:24:27   [Figure_Series] wrote Flashcards_en.txt (6785 chars)
10-10 03:24:33   [Syllogism] wrote Mind_Map.txt (2079 chars)
10-10 03:26:10   [Cubes_Dice] Practice_en_Set_01.txt try 3: re-solve disagrees (Q8 key d vs re-solve c, Q10 key d vs re-solve b, Q17 key d vs re-solve c, Q22 key a vs re-solve c)
10-10 03:27:58   [Paper_Folding_Cutting] wrote Practice_en_Set_04.txt (write, 25 MCQs)
10-10 03:28:02   [Figure_Series] wrote Flashcards_hi.txt (4300 chars)
10-10 03:28:14   [Syllogism] wrote Flashcards_en.txt (9966 chars)
10-10 03:28:24   [Dictionary_Order] Practice_en_Set_04.txt try 2: re-solve disagrees (Q76 key a vs re-solve d, Q79 key b vs re-solve c, Q80 key c vs re-solve b, Q91 key c vs re-solve a, 
10-10 03:29:51   [Figure_Series] PYQ_en.txt try 1: rejected (output still looks like a prompt)
10-10 03:32:39   [Paper_Folding_Cutting] wrote Practice_hi_Set_04.txt (translate from Practice_en_Set_04.txt, 25 MCQs)
10-10 03:33:56   [Figure_Series] wrote PYQ_en.txt (8967 chars)
10-10 03:36:16   [Cubes_Dice] wrote Practice_en_Set_01.txt (write, 25 MCQs)
10-10 03:39:55   [Dictionary_Order] Practice_en_Set_04.txt try 3: re-solve disagrees (Q81 key a vs re-solve b)
10-10 03:40:11   [Figure_Series] wrote PYQ_hi.txt (8222 chars)
10-10 03:40:45   [Cubes_Dice] wrote Practice_hi_Set_01.txt (translate from Practice_en_Set_01.txt, 25 MCQs)
10-10 03:41:04   [Mirror_Water_Images] FAILED Practice_en_Set_06.txt: too_long
10-10 03:41:04   [Mirror_Water_Images] skip Practice_hi_Set_06.txt: its pair Practice_en_Set_06.txt was not written
10-10 03:41:04   [Mirror_Water_Images] written 0, failed 6; AI calls today 125/100000
10-10 03:41:04 NOT OK Graduation_Level/Reasoning/Chapter_20_Mirror_Water_Images after 154 min: todo ['Set 04 en: todo', 'Set 04 hi: todo', 'Set 05 en: todo', 'Set 05 hi: todo'] problems []
10-10 03:41:05   [Sitting_Arrangement] FAILED Feynman_hi.txt: too_long
10-10 03:41:06   [Sitting_Arrangement] written 1, failed 1; AI calls today 124/100000
10-10 03:41:06 START Graduation_Level/Reasoning/Chapter_20_Mirror_Water_Images (TODO: todo 6, problems 0)
10-10 03:46:29   [Cubes_Dice] Practice_en_Set_02.txt try 1: rejected (Q43:leaked_reasoning)
10-10 03:46:45   [Syllogism] wrote Flashcards_hi.txt (4283 chars)
```
