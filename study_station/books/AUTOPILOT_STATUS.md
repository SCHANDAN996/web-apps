# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 03:04 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 01:32 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 08 samas (10th Hindi) | ✍️ लिख रहा है | 47 मिनट |
| W2 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 67 मिनट |
| W3 | Chapter 07 word (12th Computer) | 🔎 review हो रहा है | 49 मिनट |
| W4 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 36 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 92 |
| key 4 | 50 |

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

- Chapter 04 visheshan kriya (Hindi) — 1 बार
- Chapter 03 sangya sarvanam (Hindi) — 1 बार
- Chapter 06 kaal vachya (Hindi) — 1 बार
- Chapter 01 varn vartani (Hindi) — 1 बार
- Chapter 05 ling vachan karak (Hindi) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 02:17:53 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani after 46 min: todo [] problems []
19-11 02:17:54 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_08_samas (TODO: todo 5, problems 0)
19-11 02:17:54   [samas] Hindi-only writer: direct Hindi content; English generation and translation disabled
19-11 02:18:35   [word] review Content_en.txt: 4 issue(s): - The shortcut `Ctrl+Shift+V` is listed as "Paste Special → Keep Text Only" but this is not a default shortcut in W
19-11 02:20:22   [word] REJECTED review fix Content_en.txt: reviewer still reports - In section 5.1, the Change Case (Shift+F3) description incorrectly includes 'tOGGLE cASE'
19-11 02:21:19   [word] review Content_hi.txt: 2 issue(s): - शॉर्टकट तालिका में "फिर से करें" के लिए Ctrl+Shift+Z सूचीबद्ध है → Word में Redo का मानक शॉर्टकट केवल Ctrl+Y है; 
19-11 02:23:59   [sandhi] Practice_hi_Set_01.txt try 4: re-solve disagrees (Q15 key c vs re-solve a, Q24 key d vs re-solve a)
19-11 02:23:59   [sandhi] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
19-11 02:24:18   [samas] Practice_hi_Set_01.txt try 1: re-solve disagrees (Q5 key b vs re-solve c, Q8 key b vs re-solve a, Q9 key d vs re-solve a, Q13 key b vs re-solve a, Q19
19-11 02:26:48   [samas] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q5 key a vs re-solve c, Q6 key b vs re-solve d, Q8 key c vs re-solve b, Q9 key c vs re-solve d, Q13 
19-11 02:28:08   [ling_vachan_karak] REJECTED review fix Important_Rules_hi.txt: reviewer still reports - Rule 11: अधिकरण कारक के चिह्न केवल 'में/पर' बताए गए हैं, लेकिन उदाहरण 'रात को' मे
19-11 02:28:08   [ling_vachan_karak] review: 1 section(s) corrected, 5 failed
19-11 02:28:08   [ling_vachan_karak] written 1, failed 5; AI calls today 100/100000
19-11 02:28:08 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak after 56 min: todo [] problems []
19-11 02:28:09 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
19-11 02:29:30   [word] REJECTED review fix Content_hi.txt: reviewer still reports - शॉर्टकट तालिका में Ctrl+N की नोट "ब्राउज़र में नया टैब खोलता है" गलत है → ब्राउज़र में Ct
19-11 02:30:18   [word] review Key_Facts_en.txt: 2 issue(s): - Item 19: Wildcard example `<[A-Z]{1,}>` claimed to find capitalized words → The pattern `<[A-Z]{1,}>` finds all
19-11 02:32:12   [sangya_sarvanam] review Content_hi.txt: 1 issue(s): - The exception list for nouns with unchanged plural forms incorrectly includes 'पैर' (singular 'पैर' becomes plura
19-11 02:32:55   [sandhi] Practice_hi_Set_02.txt try 1: re-solve disagrees (Q26 key b vs re-solve a, Q27 key d vs re-solve b, Q28 key d vs re-solve c, Q29 key a vs re-solve b, 
19-11 02:34:49   [sangya_sarvanam] review Key_Facts_hi.txt: 1 issue(s): - In point 16, the suffix “आई/ई” is wrongly illustrated with “दयालु → दयालुता”; the correct suffix for “दयालुता” 
19-11 02:36:49   [word] REJECTED review fix Key_Facts_en.txt: reviewer still reports - Point 6 incorrectly states that Shift+arrow keys extend selection by word, line, and pa
19-11 02:38:00   [word] review Key_Facts_hi.txt: 1 issue(s): - Item 20: Cross-reference shortcut written as `Alt+N, RF` → correct shortcut is `Alt+N, R`
19-11 02:39:23   [sandhi] Practice_hi_Set_02.txt try 2: re-solve disagrees (Q29 key a vs re-solve b, Q30 key c vs re-solve a, Q31 key b vs re-solve c, Q36 key a vs re-solve b, 
19-11 02:39:35   [sangya_sarvanam] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - In point 6, the example "लड़कोंने खेला" for the ergative marker "ने" is incorrect becau
19-11 02:40:32   [word] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - सुपरस्क्रिप्ट शॉर्टकट `Ctrl+Shift++` गलत है → सही शॉर्टकट `Ctrl+Shift+=` (या `Ctrl+Shif
19-11 02:41:08   [word] review Feynman_en.txt: 1 issue(s): - Common mistake #5 states "Sharing .docx with macros (.docm)" but .docx files cannot contain macros; .docm is the 
19-11 02:44:22   [samas] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q5 key a vs re-solve c, Q8 key c vs re-solve a, Q9 key c vs re-solve d, Q13 key b vs re-solve a, Q19
19-11 02:47:11   [sandhi] Practice_hi_Set_02.txt try 3: re-solve disagrees (Q30 key d vs re-solve a, Q32 key a vs re-solve c, Q39 key b vs re-solve d, Q41 key d vs re-solve c, 
19-11 02:48:56   [samas] Practice_hi_Set_01.txt try 4: re-solve disagrees (Q5 key a vs re-solve c, Q6 key b vs re-solve d, Q8 key c vs re-solve a, Q9 key c vs re-solve d, Q13 
19-11 02:48:56   [samas] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
19-11 02:51:27   [samas] Practice_hi_Set_03.txt try 1: re-solve disagrees (Q73 key d vs re-solve a)
19-11 02:54:41   [samas] Practice_hi_Set_03.txt try 2: re-solve disagrees (Q65 key d vs re-solve b, Q73 key b vs re-solve d, Q74 key a vs re-solve b)
19-11 02:55:51   [sandhi] Practice_hi_Set_02.txt try 4: re-solve disagrees (Q28 key b vs re-solve d, Q31 key b vs re-solve d, Q39 key d vs re-solve b, Q41 key b vs re-solve a, 
19-11 02:55:51   [sandhi] REJECTED Practice_hi_Set_02.txt: no version passed the checks — not written
19-11 02:56:52   [sandhi] Practice_hi_Set_03.txt try 1: rejected (Q52:duplicate_options,Q54:duplicate_options,Q56:duplicate_options,Q58:duplicate_options,Q60:duplicate_options)
19-11 02:57:21   [samas] Practice_hi_Set_03.txt try 3: re-solve disagrees (Q73 key d vs re-solve b)
19-11 03:00:02   [samas] Practice_hi_Set_03.txt try 4: re-solve disagrees (Q58 key b vs re-solve d)
19-11 03:00:02   [samas] REJECTED Practice_hi_Set_03.txt: no version passed the checks — not written
19-11 03:03:08   [sangya_sarvanam] review PYQ_hi.txt: 2 issue(s): - Section 1 example explanation incorrectly labels 'माँ' as व्यक्तिवाचक संज्ञा → 'माँ' is जातिवाचक संज्ञा (common noun)
19-11 03:04:33   [sangya_sarvanam] REJECTED review fix PYQ_hi.txt: reviewer still reports - Section 2, trap "कारक चिह्न भ्रम": "'ने' कर्ता (अन्य पुरुष, भूतकाल)" is incorrect; 'ने' marks
```
