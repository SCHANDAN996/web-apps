# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 04:28 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 03:11 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 76 मिनट |
| W2 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 39 मिनट |
| W3 | Chapter 08 samas (10th Hindi) | ✍️ लिख रहा है | 9 मिनट |
| W4 | Chapter 06 kaal vachya (10th Hindi) | 🔎 review हो रहा है | 76 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 63 |
| key 4 | 65 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
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

- Chapter 03 sangya sarvanam (Hindi) — 1 बार
- Chapter 05 ling vachan karak (Hindi) — 1 बार
- Chapter 07 word (Computer) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 15:48:31   [sangya_sarvanam] review: 2 section(s) corrected, 1 failed
19-11 15:48:31   [sangya_sarvanam] written 2, failed 1; AI calls today 69/100000
19-11 15:48:32 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam after 37 min: todo [] problems []
19-11 15:48:32 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_07_sandhi (TODO: todo 5, problems 0)
19-11 15:48:32   [sandhi] Hindi-only writer: direct Hindi content; English generation and translation disabled
19-11 15:49:23   [ling_vachan_karak] review PYQ_hi.txt round 2: 4 issue(s): - Section 5 trap list includes "स्त्रीलिंग कर्ता के साथ बिना ने के" as a condition for wrong use of 'ने'; this 
19-11 15:49:51   [varn_vartani] review PYQ_hi.txt round 1: 1 issue(s): - 1.7 शब्द-शुद्धि: Explanation cites wrong rule (श vs ष) for distinguishing "प्रशासन" from "प्रशाशन"; the real 
19-11 15:52:00   [ling_vachan_karak] REJECTED review fix PYQ_hi.txt: reviewer still reports - Section 2, trap "संयुक्त संज्ञा में केवल मुख्य शब्द का वचन बदलना": example "कमरे का दरवाज़ा" 
19-11 15:52:34   [ling_vachan_karak] review: 1 section(s) corrected, 3 failed
19-11 15:52:34   [ling_vachan_karak] written 1, failed 3; AI calls today 76/100000
19-11 15:52:34 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak after 41 min: todo [] problems []
19-11 15:52:34 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_07_word (OK: todo 0, problems 0)
19-11 15:53:21   [sandhi] Practice_hi_Set_01.txt try 1: rejected (Q2:duplicate_options,Q5:duplicate_options,Q7:duplicate_options,Q8:duplicate_options,Q9:duplicate_options)
19-11 15:53:37   [word] review Content_en.txt round 1: 2 issue(s): - In section 16 (Keyboard Shortcuts), `Ctrl+Shift+V` is listed as "Paste Special → Keep Text Only" → The de
19-11 15:55:25   [word] review Content_en.txt round 2: 3 issue(s): - Section 5.1: Change Case (`Shift+F3`) description includes "tOGGLE cASE" as a toggled option → `Shift+F3`
19-11 15:57:58   [word] review Content_hi.txt round 1: 2 issue(s): - शॉर्टकट तालिका में Ctrl+N के नोट में "ब्राउज़र में नया टैब खोलता है" लिखा है → ब्राउज़र में Ctrl+N नया वि
19-11 16:00:51   [word] review Content_hi.txt round 2: 1 issue(s): - Quick Revision point 3: Focus mode shortcut listed as Alt+V,F → The View tab is accessed with Alt+W, not 
19-11 16:02:36   [word] REJECTED review fix Content_hi.txt: reviewer still reports - परिचय में रिबन टैब की सूची अधूरी है (Draw और Design गायब) → रिबन टैब में File, Home, Inse
19-11 16:03:24   [word] review Key_Facts_en.txt round 1: 1 issue(s): - Wildcard example `<[A-Z]{1,}>` claimed to find capitalized words → It actually matches words composed e
19-11 16:03:57   [sandhi] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q4 key c vs re-solve d, Q6 key c vs re-solve b, Q7 key b vs re-solve c, Q9 key b vs re-solve c, Q11 
19-11 16:04:15   [word] review Key_Facts_en.txt round 2: 1 issue(s): - Item 20: “green (older versions) = context” is incorrect; in older Word versions a green wavy underline
19-11 16:05:12   [word] REJECTED review fix Key_Facts_en.txt: reviewer still reports - Ribbon tabs list omits the Design tab → The Ribbon tabs are Home, Insert, Design, Layou
19-11 16:07:18   [word] review Flashcards_hi.txt round 1: 1 issue(s): - Card 4 claims “ब्राउज़र में भी Ctrl + P प्रिंट करता है, लेकिन Word का अपना प्रिंट इंजन उपयोग होता है” 
19-11 16:08:59   [kaal_vachya] review PYQ_hi.txt round 2: 1 issue(s): - In Section 2.1, PYQ-style उदाहरण 3 (द्विकर्मक क्रिया) the answer is given as (b) विद्या शिष्य को दी गई, but t
19-11 16:10:08   [word] review PYQ_en.txt round 1: 1 issue(s): - Example 1 solution claims “Ctrl + Shift + F opens the Font dialog with focus on the Font list (legacy behavio
19-11 16:11:31   [word] review PYQ_en.txt round 2: 2 issue(s): - In Core Sub-topics → Illustrations, the list includes 'Text Box, WordArt, Drop Cap' which are not in the Illu
19-11 16:11:52   [varn_vartani] review Important_Rules_hi.txt round 1: 6 issue(s): - Section 5 (rule 5) states long vowels take only anusvara (ं) but then cites "हाँसी" (with chandra
19-11 16:13:24   [word] REJECTED review fix PYQ_en.txt: reviewer still reports - Example 1 solution incorrectly states "Ctrl + Shift + F opens the Font dialog with focus on t
19-11 16:13:55   [word] review PYQ_hi.txt round 1: 1 issue(s): - उदाहरण 1 की व्याख्या में गलत दावा: "Ctrl+Shift+> Word और PowerPoint में फॉन्ट साइज़ बढ़ाता है, लेकिन Excel मे
19-11 16:15:42   [word] review PYQ_hi.txt round 2: 1 issue(s): - Example 1 explanation claims "Ctrl+Shift+> Word, PowerPoint और Excel तीनों में फॉन्ट साइज़ बढ़ाता है" → Ctrl+
19-11 16:17:19   [word] REJECTED review fix PYQ_hi.txt: reviewer still reports - स्कोप भ्रम ट्रैप में Ctrl+F के बारे में गलत कथन: "परीक्षा पूछे 'सभी Office ऐप्स में' तो गलत" 
19-11 16:18:05   [word] review: 2 section(s) corrected, 4 failed
19-11 16:18:05   [word] written 2, failed 4; AI calls today 119/100000
19-11 16:18:05 NOT OK 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_07_word after 26 min: todo [] problems []
19-11 16:18:06 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_08_samas (TODO: todo 3, problems 0)
19-11 16:18:06   [samas] Hindi-only writer: direct Hindi content; English generation and translation disabled
19-11 16:19:58   [sandhi] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q4 key c vs re-solve d, Q5 key d vs re-solve c, Q6 key a vs re-solve b, Q9 key d vs re-solve c, Q11 
19-11 16:20:57   [samas] Practice_hi_Set_01.txt try 1: re-solve disagrees (Q7 key b vs re-solve d, Q19 key a vs re-solve ?)
19-11 16:22:49   [samas] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q7 key d vs re-solve b)
19-11 16:25:21   [samas] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q7 key d vs re-solve b)
```
