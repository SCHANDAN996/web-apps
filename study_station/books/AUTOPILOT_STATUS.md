# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 07:45 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 03:11 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 09 upsarg pratyay (10th Hindi) | ✍️ लिख रहा है | 97 मिनट |
| W2 | Chapter 09 powerpoint (12th Computer) | ✍️ लिख रहा है | 89 मिनट |
| W3 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 55 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 195 |
| key 4 | 182 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 6 | 0 | 11 |
| 12th Computer | 8 | 0 | 6 |
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
| **कुल** | **310** | **0** | **17** |

## ✅ autopilot से हाल में पूरे हुए

- 19-11 18:05 — 10th Hindi · Chapter 03 sangya sarvanam
- 19-11 17:54 — 10th Hindi · Chapter 05 ling vachan karak

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 07 word (Computer) — 2 बार
- Chapter 06 kaal vachya (Hindi) — 2 बार
- Chapter 01 varn vartani (Hindi) — 2 बार
- Chapter 08 samas (Hindi) — 2 बार
- Chapter 07 sandhi (Hindi) — 1 बार
- Chapter 08 excel (Computer) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 18:57:11   [excel] REJECTED review fix Content_hi.txt: reviewer still reports - "पुराने संस्करणों (2013 तक) में तीन शीट्स बनती थीं" गलत है — एक्सेल 2013 में भी डिफ़ॉल्ट 
19-11 18:57:36   [varn_vartani] review Key_Facts_hi.txt round 1: 1 issue(s): - Point 17 example 'अण्डा' is a misspelling (the word is 'अंडा' without anusvara) → Replace with a correc
19-11 18:58:14   [excel] review Key_Facts_hi.txt round 1: 1 issue(s): - The shortcut for toggling formula view is given as `Ctrl + ~` (tilde) → The correct shortcut is `Ctrl +
19-11 18:59:54   [excel] review Key_Facts_hi.txt round 2: 1 issue(s): - Operator precedence order listed incorrectly: comparison before concatenation → Correct order: exponent
19-11 19:00:37   [varn_vartani] review Key_Facts_hi.txt round 2: 5 issue(s): - The consonant total 41 contradicts the breakdown (33 basic + 4 conjunct + 2 double + 5 nuqta = 44) → Ch
19-11 19:02:14   [powerpoint] wrote PYQ_en.txt (6275 chars)
19-11 19:03:29   [powerpoint] wrote PYQ_hi.txt (8152 chars)
19-11 19:04:06   [powerpoint] wrote Important_Rules_en.txt (6804 chars)
19-11 19:05:45   [powerpoint] wrote Important_Rules_hi.txt (9617 chars)
19-11 19:08:53   [powerpoint] Practice_en_Set_01.txt try 1: re-solve disagrees (Q4 key b vs re-solve ?, Q20 key b vs re-solve ?)
19-11 19:08:54   [upsarg_pratyay] Practice_hi_Set_03.txt try 1: re-solve disagrees (Q52 key a vs re-solve d, Q64 key c vs re-solve b, Q68 key c vs re-solve a, Q75 key d vs re-solve ?)
19-11 19:11:39   [powerpoint] wrote Practice_en_Set_01.txt (write, 25 MCQs)
19-11 19:11:42   [varn_vartani] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Item 1 says the traditional count of 44 letters comprises 11 vowels, 33 consonants, 4 c
19-11 19:11:42   [varn_vartani] review Feynman_hi.txt: resumed private correction draft
19-11 19:12:51   [powerpoint] wrote Practice_hi_Set_01.txt (translate from Practice_en_Set_01.txt, 25 MCQs)
19-11 19:16:26   [excel] review PYQ_hi.txt round 1: 1 issue(s): - उदाहरण 1 में उत्तर और व्याख्या गलत है: सेल B2 में सूत्र `=$A$1+A2` को C3 में कॉपी करने पर सापेक्ष संदर्भ A2 ए
19-11 19:19:26   [excel] review PYQ_hi.txt round 2: 1 issue(s): - Keyboard Shortcuts (स्वरूपण): `Ctrl+Shift+@` labeled as वैज्ञानिक (scientific) and `Ctrl+Shift+:` as समय (tim
19-11 19:20:55   [varn_vartani] review Feynman_hi.txt round 1: 2 issue(s): - In the chandrabindu rule table, the example "सँकरा" is incorrect because the following consonant 'क' is n
19-11 19:21:17   [excel] REJECTED review fix PYQ_hi.txt: reviewer still reports - "सरणी सूत्र विरासत" जाल में स्पष्टीकरण गलत है: `=SUM(A1:A10*B1:B10)` नए एक्सेल में **स्पिल नह
19-11 19:21:51   [excel] review Important_Rules_en.txt round 1: 1 issue(s): - Rule 13 states Mac shortcut for F4 (absolute reference) is Cmd+T → The correct Mac shortcut for t
19-11 19:22:48   [varn_vartani] review Feynman_hi.txt round 2: 2 issue(s): - In the 'भ्रमित शब्द-युग्म' table, the row for 'आश्चर्य' shows identical spellings for both correct and in
19-11 19:24:22   [powerpoint] wrote Practice_en_Set_02.txt (write, 25 MCQs)
19-11 19:25:13   [excel] review Important_Rules_en.txt round 2: 2 issue(s): - Rule 9: The statement “Rules are evaluated in the order listed; the first true rule wins unless “
19-11 19:27:18   [excel] REJECTED review fix Important_Rules_en.txt: reviewer still reports - Rule 13: Mac shortcut for toggling absolute/relative references is incorrectly gi
19-11 19:27:27   [upsarg_pratyay] wrote Practice_hi_Set_03.txt (write, 25 MCQs)
19-11 19:28:00   [excel] review Important_Rules_hi.txt round 1: 2 issue(s): - नियम 2 में संरचित संदर्भ (Structured References) के बारे में कहा गया है कि "टेबल नाम और स्तंभ नाम
19-11 19:28:38   [upsarg_pratyay] Practice_hi_Set_04.txt try 1: rejected (Q95:duplicate_options)
19-11 19:29:49   [powerpoint] wrote Practice_hi_Set_02.txt (translate from Practice_en_Set_02.txt, 25 MCQs)
19-11 19:33:07   [powerpoint] wrote Practice_en_Set_03.txt (write, 25 MCQs)
19-11 19:35:38   [powerpoint] wrote Practice_hi_Set_03.txt (translate from Practice_en_Set_03.txt, 25 MCQs)
19-11 19:37:51   [powerpoint] wrote Practice_en_Set_04.txt (write, 25 MCQs)
19-11 19:37:51   [upsarg_pratyay] Practice_hi_Set_04.txt try 2: re-solve disagrees (Q76 key a vs re-solve b, Q79 key d vs re-solve a, Q81 key b vs re-solve d, Q85 key b vs re-solve d, 
19-11 19:38:49   [powerpoint] wrote Practice_hi_Set_04.txt (translate from Practice_en_Set_04.txt, 25 MCQs)
19-11 19:38:53   [excel] review: 2 section(s) corrected, 3 failed
19-11 19:38:53   [excel] written 2, failed 3; AI calls today 371/100000
19-11 19:38:53 NOT OK 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_08_excel after 93 min: todo [] problems []
19-11 19:38:53 worker 3: nothing left
19-11 19:41:36   [powerpoint] Practice_en_Set_05.txt try 1: re-solve disagrees (Q105 key c vs re-solve a, Q107 key c vs re-solve a, Q124 key a vs re-solve d)
19-11 19:45:16   [powerpoint] wrote Practice_en_Set_05.txt (write, 25 MCQs)
19-11 19:45:34   [upsarg_pratyay] Practice_hi_Set_04.txt try 3: re-solve disagrees (Q79 key d vs re-solve c)
```
