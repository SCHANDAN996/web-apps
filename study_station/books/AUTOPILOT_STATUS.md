# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 10:33 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 06:58 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 22 मिनट |
| W2 | Chapter 09 upsarg pratyay (10th Hindi) | ✍️ लिख रहा है | 63 मिनट |
| W3 | Chapter 08 samas (10th Hindi) | ✍️ लिख रहा है | 63 मिनट |
| W4 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 20 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 141 |
| key 4 | 191 |

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

- 19-11 09:33 — 10th Hindi · Chapter 04 visheshan kriya

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 05 ling vachan karak (Hindi) — 3 बार
- Chapter 03 sangya sarvanam (Hindi) — 2 बार
- Chapter 06 kaal vachya (Hindi) — 2 बार
- Chapter 01 varn vartani (Hindi) — 2 बार
- Chapter 08 samas (Hindi) — 1 बार
- Chapter 07 word (Computer) — 2 बार
- Chapter 07 sandhi (Hindi) — 1 बार
- Chapter 08 excel (Computer) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 09:55:29   [upsarg_pratyay] Practice_hi_Set_01.txt try 4: re-solve disagrees (Q9 key d vs re-solve ?, Q10 key c vs re-solve a, Q17 key d vs re-solve ?)
19-11 09:55:29   [upsarg_pratyay] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
19-11 09:56:30   [upsarg_pratyay] Practice_hi_Set_02.txt try 1: rejected (Q47:duplicate_options)
19-11 09:59:03   [samas] Practice_hi_Set_01.txt try 4: re-solve disagrees (Q14 key a vs re-solve b)
19-11 09:59:03   [samas] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
19-11 10:02:25   [upsarg_pratyay] Practice_hi_Set_02.txt try 2: re-solve disagrees (Q28 key c vs re-solve ?, Q32 key d vs re-solve ?, Q36 key d vs re-solve c, Q49 key b vs re-solve c)
19-11 10:02:45   [ling_vachan_karak] review PYQ_hi.txt: 5 issue(s): - The claim "SSC GD में इस अध्याय से 3–5 प्रश्न आते हैं" is an invented exam statistic without a year → Remove the clai
19-11 10:05:08   [samas] Practice_hi_Set_03.txt try 1: re-solve disagrees (Q61 key d vs re-solve a, Q65 key a vs re-solve b, Q75 key c vs re-solve a)
19-11 10:05:17   [word] REJECTED review fix Key_Facts_en.txt: reviewer still reports - Item 19 wildcard examples use regex syntax `{1,}` instead of Word's `@` for one-or-more
19-11 10:07:01   [ling_vachan_karak] REJECTED review fix PYQ_hi.txt: reviewer still reports - In section 3 (कारक चिह्न पहचान), trap description: "कर्ता कारक 'ने' केवल अन्य पुरुष, भूतकाल, 
19-11 10:07:52   [ling_vachan_karak] review Important_Rules_hi.txt: 2 issue(s): - नियम ४(घ) का कथन "इ/ई/उ/ऊ/ए/ओकारांत: प्रायः अपरिवर्तित" गलत है क्योंकि स्त्रीलिंग इ/ईकारांत संज्ञाएँ बहुव
19-11 10:08:02   [samas] Practice_hi_Set_03.txt try 2: re-solve disagrees (Q63 key c vs re-solve d, Q65 key a vs re-solve b, Q71 key a vs re-solve b)
19-11 10:09:09   [word] review PYQ_en.txt: 2 issue(s): - In Example 1 explanation, the claim "Ctrl + Shift + F opens the Font dialog with focus on the Font list (legacy behav
19-11 10:11:27   [ling_vachan_karak] REJECTED review fix Important_Rules_hi.txt: reviewer still reports - Rule 4 (ङ) misclassifies 'वीर' (ईकारांत पुल्लिंग) under उ/ऊ/ए/ओकारांत पुल्लिंग. →
19-11 10:11:27   [ling_vachan_karak] review: 0 section(s) corrected, 4 failed
19-11 10:11:27   [ling_vachan_karak] written 0, failed 4; AI calls today 303/100000
19-11 10:11:27 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak after 37 min: todo [] problems []
19-11 10:11:27 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
19-11 10:12:04   [word] REJECTED review fix PYQ_en.txt: reviewer still reports - Example 1 explanation claims "Ctrl + Shift + F changes the font size in some versions" → Ctrl
19-11 10:12:05   [upsarg_pratyay] Practice_hi_Set_02.txt try 3: re-solve disagrees (Q32 key d vs re-solve c)
19-11 10:13:03   [word] review: 0 section(s) corrected, 4 failed
19-11 10:13:03   [word] written 0, failed 4; AI calls today 306/100000
19-11 10:13:04 NOT OK 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_07_word after 47 min: todo [] problems []
19-11 10:13:04 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
19-11 10:14:14   [varn_vartani] review Content_hi.txt: 2 issue(s): - In section 3.4, the table lists the pronunciation place of 'ड़' and 'ढ़' as "तालव्य" (palatal); the correct place
19-11 10:15:40   [samas] Practice_hi_Set_03.txt try 3: re-solve disagrees (Q58 key a vs re-solve d)
19-11 10:16:58   [samas] Practice_hi_Set_03.txt try 4: rejected (Q53:duplicate_options)
19-11 10:16:58   [samas] REJECTED Practice_hi_Set_03.txt: no version passed the checks — not written
19-11 10:18:06   [sangya_sarvanam] review Key_Facts_hi.txt: 2 issue(s): - Point 4: Rule "व्यंजनांत → एँ/ओं" is incorrect; consonant-ending nouns form plural with "एँ" (e.g., घर → घरें, 
19-11 10:20:19   [upsarg_pratyay] Practice_hi_Set_02.txt try 4: re-solve disagrees (Q47 key a vs re-solve b)
19-11 10:20:19   [upsarg_pratyay] REJECTED Practice_hi_Set_02.txt: no version passed the checks — not written
19-11 10:22:06   [varn_vartani] REJECTED review fix Content_hi.txt: reviewer still reports - In the "सामान्य त्रुटियाँ और उनके सुधार" table, the row for अशुद्ध "सष्त्र" → शुद्ध "शस्त
19-11 10:22:53   [varn_vartani] review Key_Facts_hi.txt: 1 issue(s): - Point 6 claims only 2 nukta consonants (ऩ, ऱ) but Point 16 explicitly lists ज़, फ़, ख़ as nukta forms used in U
19-11 10:24:01   [varn_vartani] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 24 incorrectly cites "रों" as a plural marker; the correct oblique plural ending 
19-11 10:24:49   [varn_vartani] review Feynman_hi.txt: 6 issue(s): - Section 3, Rule 1: "हंसना = हंस पक्षी" is a wrong meaning; "हंसना" is not a word for "swan bird" (हंस) — it is ju
19-11 10:25:10   [upsarg_pratyay] Practice_hi_Set_03.txt try 1: re-solve disagrees (Q70 key b vs re-solve a, Q71 key c vs re-solve b)
19-11 10:28:27   [upsarg_pratyay] Practice_hi_Set_03.txt try 2: re-solve disagrees (Q52 key c vs re-solve b, Q70 key c vs re-solve a, Q71 key d vs re-solve b, Q73 key a vs re-solve c)
19-11 10:28:39   [varn_vartani] REJECTED review fix Feynman_hi.txt: reviewer still reports - Section 1: States 33 consonants but lists 36 (including क्ष, त्र, ज्ञ); 11+33=44 contradi
19-11 10:32:11   [upsarg_pratyay] Practice_hi_Set_03.txt try 3: re-solve disagrees (Q52 key a vs re-solve b, Q71 key c vs re-solve b)
19-11 10:32:40   [samas] Practice_hi_Set_05.txt try 1: re-solve disagrees (Q115 key a vs re-solve ?, Q119 key c vs re-solve d, Q121 key b vs re-solve c)
```
