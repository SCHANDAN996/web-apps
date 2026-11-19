# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 08:46 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 06:58 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 50 मिनट |
| W2 | Chapter 07 word (12th Computer) | 🔎 review हो रहा है | 72 मिनट |
| W3 | Chapter 08 samas (10th Hindi) | ✍️ लिख रहा है | 66 मिनट |
| W4 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 81 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 71 |
| key 4 | 101 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 6 | 0 | 11 |
| 12th Computer | 7 | 0 | 7 |
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
| **कुल** | **309** | **0** | **18** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 04 visheshan kriya (Hindi) — 2 बार
- Chapter 05 ling vachan karak (Hindi) — 1 बार
- Chapter 03 sangya sarvanam (Hindi) — 1 बार
- Chapter 06 kaal vachya (Hindi) — 1 बार
- Chapter 01 varn vartani (Hindi) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 07:55:47 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya after 14 min: todo [] problems []
19-11 07:55:48 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
19-11 07:56:55   [sandhi] Practice_hi_Set_02.txt try 2: rejected (Q37:duplicate_options,Q48:duplicate_options)
19-11 08:02:33   [samas] Practice_hi_Set_03.txt try 3: re-solve disagrees (Q64 key c vs re-solve ?, Q71 key b vs re-solve a)
19-11 08:05:37   [sandhi] Practice_hi_Set_02.txt try 3: re-solve disagrees (Q31 key c vs re-solve a, Q49 key a vs re-solve c)
19-11 08:08:05   [samas] Practice_hi_Set_03.txt try 4: re-solve disagrees (Q64 key c vs re-solve a)
19-11 08:08:05   [samas] REJECTED Practice_hi_Set_03.txt: no version passed the checks — not written
19-11 08:11:09   [samas] Practice_hi_Set_04.txt try 1: re-solve disagrees (Q89 key c vs re-solve b, Q93 key d vs re-solve c, Q97 key a vs re-solve c, Q100 key d vs re-solve b)
19-11 08:12:04   [sandhi] Practice_hi_Set_02.txt try 4: re-solve disagrees (Q29 key d vs re-solve ?, Q30 key c vs re-solve ?, Q36 key d vs re-solve ?, Q40 key b vs re-solve ?)
19-11 08:12:04   [sandhi] REJECTED Practice_hi_Set_02.txt: no version passed the checks — not written
19-11 08:12:38   [sandhi] Practice_hi_Set_03.txt try 1: rejected (Q52:duplicate_options,Q54:duplicate_options,Q56:duplicate_options,Q58:duplicate_options,Q60:duplicate_options)
19-11 08:13:13   [sandhi] Practice_hi_Set_03.txt try 2: rejected (Q52:duplicate_options,Q54:duplicate_options,Q56:duplicate_options,Q58:duplicate_options,Q60:duplicate_options)
19-11 08:14:22   [sandhi] Practice_hi_Set_03.txt try 3: rejected (corrupted characters)
19-11 08:14:56   [samas] Practice_hi_Set_04.txt try 2: re-solve disagrees (Q99 key a vs re-solve b)
19-11 08:15:37   [ling_vachan_karak] review Content_hi.txt: 6 issue(s): - In the बहुवचन बनाने के नियम table, the row for 'आ (स्त्रीलिंग)' incorrectly lists 'लड़की → लड़कियाँ' and 'नदी → न
19-11 08:17:13   [samas] Practice_hi_Set_04.txt try 3: re-solve disagrees (Q99 key a vs re-solve b)
19-11 08:17:21   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - In the plural formation table (Section 2), the row for "आ (स्त्रीलिंग)" lists "बहू → बहुए
19-11 08:18:53   [sandhi] Practice_hi_Set_03.txt try 4: rejected (Q54:duplicate_options,Q62:duplicate_options,Q64:duplicate_options,Q66:duplicate_options,Q68:duplicate_options)
19-11 08:18:53   [sandhi] REJECTED Practice_hi_Set_03.txt: no version passed the checks — not written
19-11 08:19:44   [sandhi] Practice_hi_Set_05.txt try 1: rejected (Q118:duplicate_options)
19-11 08:20:51   [samas] wrote Practice_hi_Set_04.txt (write, 25 MCQs)
19-11 08:21:00   [sandhi] Practice_hi_Set_05.txt try 2: rejected (Q118:duplicate_options)
19-11 08:22:10   [word] REJECTED review fix Key_Facts_en.txt: reviewer still reports - In point 19, the wildcard example `<[A-Z]{1,}>` uses regex syntax, not Word wildcard sy
19-11 08:24:40   [word] review Flashcards_hi.txt: 2 issue(s): - Card 10: "Ctrl + Click (शब्द)" → Ctrl+Click selects a sentence; to select a word use double‑click.
19-11 08:25:42   [ling_vachan_karak] review Key_Facts_hi.txt: 5 issue(s): - Point 4: The claim that inanimate objects are usually neuter and the examples (किताब, मेज, पानी, आकाश) are wron
19-11 08:27:13   [ling_vachan_karak] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 4 incorrectly claims Hindi has a neuter gender (नपुंसकलिंग) for inanimate nouns a
19-11 08:28:39   [word] review PYQ_en.txt: 2 issue(s): - In Example 1 solution, the claim "Ctrl + Shift + F opens the Font dialog with focus on the Font list (legacy behavior
19-11 08:29:13   [sandhi] Practice_hi_Set_05.txt try 3: re-solve disagrees (Q102 key a vs re-solve b, Q105 key c vs re-solve d, Q106 key c vs re-solve d, Q109 key d vs re-solve
19-11 08:30:19   [samas] Practice_hi_Set_05.txt try 1: re-solve disagrees (Q113 key a vs re-solve d, Q115 key a vs re-solve d, Q119 key c vs re-solve d)
19-11 08:33:57   [samas] Practice_hi_Set_05.txt try 2: re-solve disagrees (Q113 key c vs re-solve d)
19-11 08:35:54   [samas] Practice_hi_Set_05.txt try 3: re-solve disagrees (Q113 key a vs re-solve d, Q120 key a vs re-solve b)
19-11 08:37:44   [samas] Practice_hi_Set_05.txt try 4: re-solve disagrees (Q113 key a vs re-solve d)
19-11 08:37:44   [samas] REJECTED Practice_hi_Set_05.txt: no version passed the checks — not written
19-11 08:38:45   [samas] Practice_hi_Set_06.txt try 1: rejected (Q131:duplicate_options)
19-11 08:40:46   [sandhi] Practice_hi_Set_05.txt try 4: re-solve disagrees (Q104 key a vs re-solve d, Q105 key c vs re-solve b, Q109 key d vs re-solve ?, Q113 key a vs re-solve
19-11 08:40:46   [sandhi] REJECTED Practice_hi_Set_05.txt: no version passed the checks — not written
19-11 08:41:21   [sandhi] Practice_hi_Set_06.txt try 1: rejected (Q128:duplicate_options,Q134:duplicate_options)
19-11 08:42:07   [samas] Practice_hi_Set_06.txt try 2: re-solve disagrees (Q127 key c vs re-solve a, Q137 key a vs re-solve c, Q140 key c vs re-solve b)
19-11 08:42:07   [word] REJECTED review fix PYQ_en.txt: reviewer still reports - Example 1 solution incorrectly claims "Ctrl + Shift + F changes the font size in some context
19-11 08:45:54   [samas] Practice_hi_Set_06.txt try 3: re-solve disagrees (Q132 key a vs re-solve b, Q137 key b vs re-solve a, Q139 key d vs re-solve a, Q150 key c vs re-solve
```
