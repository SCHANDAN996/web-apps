# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 11:19 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 06:58 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 29 मिनट |
| W2 | Chapter 09 upsarg pratyay (10th Hindi) | ✍️ लिख रहा है | 109 मिनट |
| W4 | Chapter 06 kaal vachya (10th Hindi) | 🔎 review हो रहा है | 41 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 175 |
| key 4 | 224 |

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
- Chapter 03 sangya sarvanam (Hindi) — 3 बार
- Chapter 06 kaal vachya (Hindi) — 2 बार
- Chapter 01 varn vartani (Hindi) — 3 बार
- Chapter 08 samas (Hindi) — 2 बार
- Chapter 07 word (Computer) — 2 बार
- Chapter 07 sandhi (Hindi) — 1 बार
- Chapter 08 excel (Computer) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 10:40:00   [varn_vartani] REJECTED review fix Flashcards_hi.txt: reviewer still reports - Card 5: Chandrabindu rule states it is used "जब मात्रा पहले से लगी हो" but the example
19-11 10:41:57   [varn_vartani] review PYQ_hi.txt: 1 issue(s): - The rule for 'न्' before य/र/ल/व/श/ष/स/ह incorrectly states it becomes anusvara (ं); in standard Hindi spelling, 'न्'
19-11 10:42:40   [samas] Practice_hi_Set_05.txt try 3: re-solve disagrees (Q114 key c vs re-solve b, Q121 key c vs re-solve b)
19-11 10:44:20   [upsarg_pratyay] Practice_hi_Set_04.txt try 2: re-solve disagrees (Q78 key d vs re-solve b, Q86 key d vs re-solve b, Q94 key a vs re-solve c, Q98 key c vs re-solve d)
19-11 10:44:58   [samas] Practice_hi_Set_05.txt try 4: re-solve disagrees (Q114 key a vs re-solve b, Q121 key b vs re-solve c)
19-11 10:44:58   [samas] REJECTED Practice_hi_Set_05.txt: no version passed the checks — not written
19-11 10:47:27   [upsarg_pratyay] Practice_hi_Set_04.txt try 3: re-solve disagrees (Q78 key d vs re-solve b)
19-11 10:48:12   [varn_vartani] review Important_Rules_hi.txt: 6 issue(s): - Rule 1: "३४ व्यंजन" claimed but only 33 consonants listed → correct to "३३ व्यंजन" or add ड़, ढ़ to the l
19-11 10:50:01   [kaal_vachya] review Content_hi.txt: 5 issue(s): - Present Perfect Continuous structure incorrectly includes "को" (only "से" is used for duration) → Remove "को"; st
19-11 10:50:28   [varn_vartani] REJECTED review fix Important_Rules_hi.txt: reviewer still reports - Rule 1 states “४५ मूल वर्ण — ११ स्वर और ३४ व्यंजन” but the consonant list contain
19-11 10:50:28   [varn_vartani] review: 1 section(s) corrected, 5 failed
19-11 10:50:28   [varn_vartani] written 1, failed 5; AI calls today 360/100000
19-11 10:50:28 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani after 39 min: todo [] problems []
19-11 10:50:29 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
19-11 10:55:10   [upsarg_pratyay] Practice_hi_Set_04.txt try 4: re-solve disagrees (Q78 key b vs re-solve d)
19-11 10:55:10   [upsarg_pratyay] REJECTED Practice_hi_Set_04.txt: no version passed the checks — not written
19-11 10:55:16   [samas] Practice_hi_Set_06.txt try 1: re-solve disagrees (Q131 key d vs re-solve c, Q138 key c vs re-solve b, Q145 key d vs re-solve b, Q147 key a vs re-solve
19-11 10:56:31   [ling_vachan_karak] review Content_hi.txt: 7 issue(s): - Section 1 table 'लिंग के प्रकार': 'कमरा' and 'ज्ञान' are पुल्लिंग, 'पत्तल' is स्त्रीलिंग; they are misclassified 
19-11 10:56:54   [upsarg_pratyay] Practice_hi_Set_05.txt try 1: re-solve disagrees (Q117 key d vs re-solve c)
19-11 10:59:13   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - वचन तालिका में 'आ (स्त्रीलिंग)' नियम के उदाहरण में 'बहन → बहनें' दिया गया है, लेकिन 'बहन'
19-11 11:00:19   [kaal_vachya] REJECTED review fix Content_hi.txt: reviewer still reports - भविष्यत काल की सतत संरचना गलत: "मूल क्रिया + रहा/रहे/रही + गा/गे/गी" → सही: "मूल क्रिया +
19-11 11:01:43   [kaal_vachya] review Key_Facts_hi.txt: 4 issue(s): - बिंदु 7 का उदाहरण "राम से पढ़ा जाता है" अपूर्ण/अशुद्ध कर्मवाच्य वाक्य है क्योंकि इसमें कर्म (कर्तृवाच्य का कर्म
19-11 11:03:05   [upsarg_pratyay] wrote Practice_hi_Set_05.txt (write, 25 MCQs)
19-11 11:04:28   [upsarg_pratyay] Practice_hi_Set_06.txt try 1: rejected (parsed 24 questions, numbers 126…150)
19-11 11:04:31   [samas] Practice_hi_Set_06.txt try 2: re-solve disagrees (Q138 key c vs re-solve b, Q139 key d vs re-solve c)
19-11 11:05:40   [ling_vachan_karak] review Key_Facts_hi.txt: 6 issue(s): - Point 4: Neuter gender examples are wrong – किताब, मेज, पानी, आकाश are not नपुंसकलिंग in Hindi → Remove the cla
19-11 11:06:12   [kaal_vachya] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 2 lists “संदिग्ध वर्तमान” as a present tense form; Hindi present tense has only t
19-11 11:08:55   [samas] Practice_hi_Set_06.txt try 3: re-solve disagrees (Q132 key a vs re-solve c, Q138 key a vs re-solve b, Q139 key c vs re-solve d, Q147 key d vs re-solve
19-11 11:09:58   [kaal_vachya] review PYQ_hi.txt: 1 issue(s): - Section 1.3 (काल-संगति): The rule “मुख्य वाक्य वर्तमान में → अधीनस्थ वाक्य भविष्यत् में” and the trap “कि वाले वाक्य 
19-11 11:12:54   [ling_vachan_karak] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 4 incorrectly states Hindi has a neuter gender (नपुंसकलिंग) and cites बच्चा, फल, 
19-11 11:13:04   [samas] Practice_hi_Set_06.txt try 4: re-solve disagrees (Q147 key a vs re-solve d)
19-11 11:13:04   [samas] REJECTED Practice_hi_Set_06.txt: no version passed the checks — not written
19-11 11:13:05   [samas] written 0, failed 4; AI calls today 390/100000
19-11 11:13:05 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_08_samas after 103 min: todo ['Set 01 hi: todo', 'Set 03 hi: todo', 'Set 05 hi: todo', 'Set 06 hi: todo'] problems []
19-11 11:13:05 worker 2: nothing left
19-11 11:13:22   [ling_vachan_karak] review PYQ_hi.txt: 5 issue(s): - Invented exam statistic "SSC GD में इस अध्याय से 3–5 प्रश्न आते हैं" without year or source → remove or cite a specif
19-11 11:14:26   [kaal_vachya] REJECTED review fix PYQ_hi.txt: reviewer still reports - Section 1.3 (काल-संगति) rule and PYQ-style उदाहरण 2 wrongly claim that a past main clause bin
19-11 11:15:47   [ling_vachan_karak] REJECTED review fix PYQ_hi.txt: reviewer still reports - Section 7 heuristic "आकारान्त → एँ" is incorrect for masculine a-ending nouns (e.g., लड़का → 
19-11 11:15:52   [upsarg_pratyay] Practice_hi_Set_06.txt try 2: rejected (Q132:duplicate_options)
19-11 11:16:28   [ling_vachan_karak] review Important_Rules_hi.txt: 1 issue(s): - नियम ४ (घ) में कहा गया है कि इ/ई/उ/ऊ/ए/ओकारांत संज्ञाएँ प्रायः अपरिवर्तित रहती हैं, लेकिन उदाहरण "नदी → न
```
