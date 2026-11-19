# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 03:10 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 11:36 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

⏸️ अभी कोई worker नहीं चल रहा (रुका हुआ या सब पूरा)।

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 91 |
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

- Chapter 01 varn vartani (Hindi) — 2 बार
- Chapter 06 kaal vachya (Hindi) — 2 बार
- Chapter 03 sangya sarvanam (Hindi) — 2 बार
- Chapter 05 ling vachan karak (Hindi) — 2 बार
- Chapter 08 excel (Computer) — 1 बार
- Chapter 08 samas (Hindi) — 1 बार
- Chapter 07 word (Computer) — 1 बार
- Chapter 07 sandhi (Hindi) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 14:01:52   [varn_vartani] REJECTED review fix Important_Rules_hi.txt: reviewer still reports - Rule 1 note lists derived consonants as "ड़" and "ढ" → should be "ड़" and "ढ़"
19-11 14:01:52   [varn_vartani] review: 0 section(s) corrected, 4 failed
19-11 14:01:52   [varn_vartani] written 0, failed 4; AI calls today 159/100000
19-11 14:01:52 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani after 91 min: todo [] problems []
19-11 14:01:52 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_06_kaal_vachya (OK: todo 0, problems 0)
19-11 14:01:53   [kaal_vachya] Book autopilot upgrade: draining existing work and saving unfinished files for the new worker/rate policy
19-11 14:01:53   [kaal_vachya] stopping: new worker/rate policy queued; no new API work started in the older runner
19-11 14:01:53 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_06_kaal_vachya after 0 min: todo [] problems []
19-11 14:01:53 worker 2: stop file found — stopping
19-11 14:05:01   [sangya_sarvanam] REJECTED review fix Content_hi.txt: reviewer still reports - The suffix 'आव' listed among common suffixes for forming abstract nouns (भाववाचक संज्ञा) 
19-11 14:06:51   [sangya_sarvanam] review Key_Facts_hi.txt: 3 issue(s): - In point 4, the plural rule for consonant‑ending nouns incorrectly lists “फल → फल/फलें” and “घर → घर/घरें”; the
19-11 14:09:05   [sangya_sarvanam] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 13: “क्या” के रूपों में “किसे (कभी-कभी)” दिया गया है → “क्या” का “किसे” रूप नहीं 
19-11 14:11:14   [ling_vachan_karak] review Content_hi.txt: 9 issue(s): - Section 1 (लिंग Table): "कमरा", "पत्तल", "फल", "ज्ञान" listed under **नपुंसकलिंग** → Incorrect gender classificat
19-11 14:14:09   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - In the "बहुवचन बनाने के नियम" table, the row for स्त्रीलिंग with एकवचन अंत "आ" gives rule
19-11 14:14:48   [ling_vachan_karak] review Key_Facts_hi.txt: 7 issue(s): - Point 4: Neuter gender claim and examples are wrong — Hindi does not treat inanimate nouns as neuter; किताब and
19-11 14:16:38   [ling_vachan_karak] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - In point 6, “शिष्य → शिष्या” is given as an example of अकारांत पुल्लिंग, but शिष्य ends
19-11 14:19:16   [ling_vachan_karak] review PYQ_hi.txt: 5 issue(s): - "SSC GD में इस अध्याय से 3–5 प्रश्न आते हैं" → invented exam statistic without year or source; remove or cite a speci
19-11 14:19:39   [sandhi] FAILED Practice_hi_Set_05.txt: too_long
19-11 14:20:42   [sandhi] Practice_hi_Set_06.txt try 1: rejected (Q129:duplicate_options,Q133:duplicate_options,Q137:duplicate_options,Q139:duplicate_options,Q149:duplicate_opt
19-11 14:23:00   [sangya_sarvanam] review Important_Rules_hi.txt: 5 issue(s): - नियम २: "आ कारांत स्त्रीलिंग" के उदाहरण (माता, बहन, चिड़िया, सास, नानी) आ-कारांत नहीं हैं; "ई कारांत पुल्
19-11 14:26:00   [sangya_sarvanam] REJECTED review fix Important_Rules_hi.txt: reviewer still reports - नियम २ की टिप्पणी में "माता", "चिड़िया" आदि को "आ-कारांत नहीं" बताया गया है जबकि 
19-11 14:26:00   [sangya_sarvanam] review: 0 section(s) corrected, 3 failed
19-11 14:26:00   [sangya_sarvanam] written 0, failed 3; AI calls today 183/100000
19-11 14:26:00 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam after 48 min: todo [] problems []
19-11 14:26:00 worker 1: stop file found — stopping
19-11 14:27:16   [ling_vachan_karak] REJECTED review fix PYQ_hi.txt: reviewer still reports - Section 6 table, row "कारक चिह्न लोप": example "राम सीता मिला (को लोप)" is wrong because "मिल
19-11 14:28:38   [ling_vachan_karak] review Important_Rules_hi.txt: 2 issue(s): - नियम ११ में अधिकरण कारक के चिह्न केवल "में/पर" बताए गए हैं, परन्तु उदाहरण "रात को" में "को" प्रयुक्त है →
19-11 14:30:36   [ling_vachan_karak] REJECTED review fix Important_Rules_hi.txt: reviewer still reports - नियम ४(घ) में कहा गया है कि इ/ई/उ/ऊ/ए/ओकारांत संज्ञाएँ प्रायः बहुवचन में अपरिवर्त
19-11 14:30:36   [ling_vachan_karak] review: 0 section(s) corrected, 4 failed
19-11 14:30:36   [ling_vachan_karak] written 0, failed 4; AI calls today 186/100000
19-11 14:30:36 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak after 40 min: todo [] problems []
19-11 14:30:36 worker 3: stop file found — stopping
19-11 14:40:50   [sandhi] Practice_hi_Set_06.txt try 2: re-solve disagrees (Q126 key d vs re-solve a, Q134 key c vs re-solve ?, Q136 key d vs re-solve b, Q137 key b vs re-solve
19-11 14:57:24   [sandhi] Practice_hi_Set_06.txt try 3: re-solve disagrees (Q140 key d vs re-solve b, Q144 key c vs re-solve ?, Q145 key d vs re-solve a, Q148 key a vs re-solve
19-11 15:08:57   [sandhi] Practice_hi_Set_06.txt try 4: re-solve disagrees (Q126 key c vs re-solve ?, Q129 key a vs re-solve b, Q131 key d vs re-solve c, Q134 key b vs re-solve
19-11 15:08:57   [sandhi] REJECTED Practice_hi_Set_06.txt: no version passed the checks — not written
19-11 15:08:57   [sandhi] written 0, failed 5; AI calls today 190/100000
19-11 15:08:57 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_07_sandhi after 189 min: todo ['Set 01 hi: todo', 'Set 02 hi: todo', 'Set 03 hi: todo', 'Set 05 hi: todo'] problems []
19-11 15:08:57 worker 0: stop file found — stopping
19-11 15:10:23 autopilot end: done 0, failed 8
```
