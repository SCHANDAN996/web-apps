# 📚 Book Autopilot — लाइव स्थिति (lane-1)

**आख़िरी update:** 11-10-2026 10:05 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 11-10 08:32 PM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 07 Sitting Arrangement (Graduation Reasoning) | 🧮 उत्तर दोबारा जाँच रहा है | 92 मिनट |
| W2 | Chapter 08 Puzzles (Graduation Reasoning) | 🧮 उत्तर दोबारा जाँच रहा है | 92 मिनट |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th GK | 19 | 0 | 0 |
| 10th Reasoning | 22 | 0 | 0 |
| 10th Maths | 22 | 0 | 0 |
| 10th English | 19 | 0 | 1 |
| 12th Maths | 20 | 0 | 3 |
| 12th GK | 24 | 0 | 0 |
| 12th Reasoning | 22 | 0 | 3 |
| 12th English | 25 | 0 | 0 |
| Graduation Maths | 27 | 0 | 1 |
| Graduation GK | 27 | 0 | 1 |
| Graduation Reasoning | 27 | 2 | 1 |
| Graduation English | 29 | 1 | 0 |
| **कुल** | **283** | **3** | **10** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
11-10 20:32:47 autopilot start: 3 workers, reverse=True
11-10 20:32:50 START Graduation_Level/Reasoning/Chapter_07_Sitting_Arrangement (OK: todo 0, problems 0)
11-10 20:32:54 START Graduation_Level/Reasoning/Chapter_08_Puzzles (OK: todo 0, problems 0)
11-10 20:33:01 worker 2: nothing left
11-10 20:48:33   [Sitting_Arrangement] set 01: Q21 key a vs re-solve d
11-10 20:49:50   [Puzzles] set 01: Q1 key a vs re-solve -, Q2 key d vs re-solve -, Q3 key a vs re-solve -, Q4 key b vs re-solve -, Q5 key b vs re-solve -, Q6 key d vs re-solve -
11-10 20:50:58   [Sitting_Arrangement] set 01 try 1: rejected (Q21:leaked_reasoning)
11-10 21:06:49   [Sitting_Arrangement] set 01 try 2: re-solve disagrees (Q24 key b vs re-solve a)
11-10 21:19:25   [Puzzles] set 01 try 1: re-solve disagrees (Q12: the clues give "6", which is not among the options)
11-10 21:26:05   [Sitting_Arrangement] set 01 try 3: re-solve disagrees (Q24 key b vs re-solve a)
11-10 21:43:29   [Sitting_Arrangement] set 01 try 4: re-solve disagrees (Q18 key c vs re-solve b, Q23 key b vs re-solve a)
11-10 21:43:29   [Sitting_Arrangement] FAILED set 01: no version passed the checks — files left as they were
11-10 21:47:11   [Puzzles] set 01 try 2: re-solve disagrees (Q12: the clues give "6", which is not among the options; Q22: clues contradict each other — no arrangement fits all 
11-10 22:03:01   [Puzzles] set 01 try 3: re-solve disagrees (Q21 key a vs re-solve b)
```
