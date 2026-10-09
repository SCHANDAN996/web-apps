# 📚 Book Autopilot — लाइव स्थिति (lane-1)

**आख़िरी update:** 10-10-2026 12:59 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 10-10 12:43 AM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 22 Para Jumbles Adv (Graduation English) | 🔧 सुधार रहा है | 2 मिनट |
| W2 | Chapter 02 Classification (Graduation Reasoning) | ✍️ लिख रहा है | 16 मिनट |
| W3 | Chapter 07 Sitting Arrangement (Graduation Reasoning) | 🔎 review हो रहा है | 16 मिनट |
| W4 | Chapter 08 Puzzles (Graduation Reasoning) | 🔎 review हो रहा है | 10 मिनट |
| W5 | Chapter 12 Missing Term (Graduation Reasoning) | 🔧 सुधार रहा है | 15 मिनट |
| W6 | Chapter 13 Dictionary Order (Graduation Reasoning) | ✍️ लिख रहा है | 15 मिनट |
| W7 | Chapter 14 Alphabet Questions (Graduation Reasoning) | ✍️ लिख रहा है | 15 मिनट |
| W8 | Chapter 19 Cubes Dice (Graduation Reasoning) | ✍️ लिख रहा है | 15 मिनट |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th GK | 19 | 0 | 0 |
| 10th Reasoning | 22 | 0 | 0 |
| 10th Maths | 17 | 5 | 0 |
| 10th English | 17 | 0 | 3 |
| 12th Maths | 11 | 0 | 12 |
| 12th GK | 22 | 0 | 2 |
| 12th Reasoning | 8 | 0 | 17 |
| 12th English | 25 | 0 | 0 |
| Graduation Maths | 3 | 0 | 25 |
| Graduation GK | 27 | 0 | 1 |
| Graduation Reasoning | 14 | 1 | 15 |
| Graduation English | 29 | 1 | 0 |
| **कुल** | **214** | **7** | **75** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 22 Para Jumbles Adv (English) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
10-10 00:43:32 autopilot start: 8 workers, reverse=True
10-10 00:43:33 START Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_22_Para_Jumbles_Adv (FIX: todo 0, problems 1)
10-10 00:43:39 START Graduation_Level/Reasoning/Chapter_02_Classification (TODO: todo 1, problems 0)
10-10 00:43:44 START Graduation_Level/Reasoning/Chapter_07_Sitting_Arrangement (OK: todo 0, problems 0)
10-10 00:43:49 START Graduation_Level/Reasoning/Chapter_08_Puzzles (FIX: todo 0, problems 1)
10-10 00:43:54 START Graduation_Level/Reasoning/Chapter_12_Missing_Term (FIX: todo 0, problems 1)
10-10 00:43:59 START Graduation_Level/Reasoning/Chapter_13_Dictionary_Order (TODO: todo 6, problems 0)
10-10 00:44:04 START Graduation_Level/Reasoning/Chapter_14_Alphabet_Questions (TODO: todo 6, problems 0)
10-10 00:44:09 START Graduation_Level/Reasoning/Chapter_19_Cubes_Dice (TODO: todo 6, problems 1)
10-10 00:47:32   [Sitting_Arrangement] review Content_en.txt: 1 issue(s): - The claim "Numbering kills 80% of silly mistakes" uses an invented statistic (80%) → Replace with "Numbering grea
10-10 00:48:37   [Dictionary_Order] Practice_en_Set_03.txt try 1: rejected (parsed 0 questions, numbers -…-)
10-10 00:48:58   [Puzzles] repaired Short_Tricks_hi.txt (2915 chars)
10-10 00:48:58   [Puzzles] written 1, failed 0; AI calls today 10/100000
10-10 00:49:27   [Classification] Practice_hi_Set_01.txt try 1: rejected (Q22:leaked_reasoning)
10-10 00:51:40   [Puzzles] review Feynman_en.txt: 1 issue(s): - The example solution incorrectly states that Aman cannot be in seat 2 because the Chintu-Bina pair won't fit with
10-10 00:52:53   [Alphabet_Questions] FAILED Practice_en_Set_03.txt: rate_limited
10-10 00:52:53   [Alphabet_Questions] skip Practice_hi_Set_03.txt: its pair Practice_en_Set_03.txt was not written
10-10 00:52:56   [Para_Jumbles_Adv] repaired Mind_Map_hi.txt (1372 chars)
10-10 00:52:56   [Para_Jumbles_Adv] written 1, failed 0; AI calls today 16/100000
10-10 00:54:38   [Classification] Practice_hi_Set_01.txt try 2: rejected (Q22:leaked_reasoning)
10-10 00:55:03   [Sitting_Arrangement] review Content_hi.txt: 1 issue(s): - 'यहीं 80% गलतियाँ होती हैं' (invented statistic) → Remove the percentage or replace with 'यहीं अक्सर गलतियाँ होती
10-10 00:57:02   [Para_Jumbles_Adv] repaired Mind_Map_hi.txt (1383 chars)
10-10 00:57:02   [Para_Jumbles_Adv] written 1, failed 0; AI calls today 20/100000
10-10 00:57:02 NOT OK Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_22_Para_Jumbles_Adv after 13 min: todo [] problems ['Mind_Map_hi.txt: much shorter than the English section (1382']
10-10 00:57:03 START Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_22_Para_Jumbles_Adv (FIX: todo 0, problems 1)
10-10 00:57:35   [Puzzles] review Feynman_hi.txt: 1 issue(s): - ब्लर्टिंग शीट में 'गोल मेज़ और सीधी पंक्ति में क्या अलग ध्यान देना है?' बिंदु शामिल है, लेकिन अध्याय में सीधी पंक
```
