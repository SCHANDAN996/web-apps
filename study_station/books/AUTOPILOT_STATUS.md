# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 18-11-2026 11:03 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 18-11 10:17 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 12 मिनट |
| W2 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 21 मिनट |
| W3 | Chapter 04 visheshan kriya (10th Hindi) | 🔎 review हो रहा है | 46 मिनट |
| W4 | Chapter 04 software os (12th Computer) | 🔎 review हो रहा है | 46 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 35 |
| key 4 | 26 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 5 | 0 | 12 |
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
| **कुल** | **308** | **0** | **19** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 03 sangya sarvanam (Hindi) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
18-11 10:17:18 autopilot start: 4 workers, reverse=False
18-11 10:17:18 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
18-11 10:17:18 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (TODO: todo 1, problems 0)
18-11 10:17:19   [varn_vartani] Hindi-only writer: direct Hindi content; English generation and translation disabled
18-11 10:17:23 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
18-11 10:17:28 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya (OK: todo 0, problems 0)
18-11 10:17:33 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_04_software_os (OK: todo 0, problems 0)
18-11 10:18:22   [varn_vartani] Practice_hi_Set_03.txt try 1: rejected (Q63:duplicate_options,Q70:duplicate_options)
18-11 10:19:57   [visheshan_kriya] review Content_hi.txt: 1 issue(s): - In section 1.3 table, "नीला" and "मीठा" are incorrectly listed as अरूपांतरित विशेषण; they are रूपांतरित विशेषण (न
18-11 10:21:02   [sangya_sarvanam] review Content_hi.txt: 1 issue(s): - Example 6 lists “औरत” and “बच्चा” as words whose plural form is identical to the singular, but “औरत” plural is “औ
18-11 10:22:56   [sangya_sarvanam] REJECTED review fix Content_hi.txt: reviewer still reports - In Section 3 table, the case markers (कारक चिह्न) are given only for singular oblique for
18-11 10:23:09   [visheshan_kriya] REJECTED review fix Content_hi.txt: reviewer still reports - In Section 1.3 table, "नीला" is incorrectly listed as an example of अरूपांतरित विशेषण (no
18-11 10:26:05   [visheshan_kriya] review Feynman_hi.txt: 3 issue(s): - Question 1 answer states only (ख) is correct for "सुन्दर" as adjective, but (घ) "सुन्दर बनो" also uses "सुन्दर" a
18-11 10:27:41   [sangya_sarvanam] review Key_Facts_hi.txt: 4 issue(s): - Plural rule for consonant-ending nouns gives incorrect examples showing singular forms as plural options (फल → 
18-11 10:28:36   [visheshan_kriya] REJECTED review fix Feynman_hi.txt: reviewer still reports - The 'काल के चिह्न' table incorrectly lists past tense suffixes as 'या/यी/ये' while the ex
18-11 10:29:50   [sangya_sarvanam] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 4 plural rule for consonant-ending nouns gives wrong examples: "फल → फलें, घर → घ
18-11 10:34:37   [sangya_sarvanam] review PYQ_hi.txt: 3 issue(s): - In section 5 (Error Detection), the answer key says (d) "किताब" but the error is in part (c) "अपने" (should be "अपनी"
18-11 10:37:05   [sangya_sarvanam] REJECTED review fix PYQ_hi.txt: reviewer still reports - In section 1, the explanation incorrectly identifies "माँ" as व्यक्तिवाचक संज्ञा; "माँ" is a 
18-11 10:38:31   [sangya_sarvanam] review Important_Rules_hi.txt: 6 issue(s): - Rule 2: The exception list heading 'ई कारांत पुल्लिंग' incorrectly lists feminine words 'पुत्री' and 'नौक
18-11 10:39:14   [varn_vartani] Practice_hi_Set_03.txt try 2: re-solve disagrees (Q64 key b vs re-solve ?, Q74 key d vs re-solve c)
18-11 10:42:41   [sangya_sarvanam] REJECTED review fix Important_Rules_hi.txt: reviewer still reports - In नियम २ and नियम ३, "हाथी" is incorrectly listed as an example of उकारांत/ऊकारा
18-11 10:42:41   [sangya_sarvanam] review: 0 section(s) corrected, 4 failed
18-11 10:42:41   [sangya_sarvanam] written 0, failed 4; AI calls today 31/100000
18-11 10:42:41 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam after 25 min: todo [] problems []
18-11 10:42:41 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
18-11 10:44:48   [ling_vachan_karak] review Content_hi.txt: 4 issue(s): - In the बहुवचन बनाने के नियम table, the row for 'आ (स्त्रीलिंग)' gives examples 'लड़की → लड़कियाँ' and 'नदी → नदिय
18-11 10:49:08   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - Neuter gender table incorrectly lists 'पत्तल', 'कमरा', 'ज्ञान' as neuter → 'पत्तल' is fem
18-11 10:50:55   [ling_vachan_karak] review Key_Facts_hi.txt: 6 issue(s): - Point 4: Neuter gender (नपुंसकलिंग) is incorrectly claimed for inanimate nouns; in modern Hindi these nouns are
18-11 10:51:18   [varn_vartani] wrote Practice_hi_Set_03.txt (write, 25 MCQs)
18-11 10:51:18   [varn_vartani] written 1, failed 0; AI calls today 39/100000
18-11 10:53:23   [visheshan_kriya] review PYQ_hi.txt: 1 issue(s): - In the "क्रिया विशेषण (Adverb) भ्रम" row, the example sentence "वह धीरे-धीरे चलता है।" is marked with ❌ but is gramma
18-11 10:54:07   [varn_vartani] review Content_hi.txt: 6 issue(s): - हिंदी वर्णमाला में कुल 52 वर्ण (13 स्वर + 39 व्यंजन) बताया गया है, लेकिन सूचीबद्ध व्यंजन (25 वर्गीय + 8 अवर्गीय +
18-11 10:55:10   [ling_vachan_karak] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 11: Example “पेड़ → पेड़े” is given for the आकारांत पुल्लिंग plural rule, but पेड
18-11 10:56:45   [ling_vachan_karak] review Feynman_hi.txt: 5 issue(s): - In the लिंग table, "पुस्तक" is listed under पुल्लिंग as an exception; "पुस्तक" is actually स्त्रीलिंग → Move "पुस
18-11 10:57:12   [varn_vartani] REJECTED review fix Content_hi.txt: reviewer still reports - In section 3.4 table, ड़ and ढ़ are incorrectly labeled as "तालव्य" (palatal) → they are 
18-11 10:58:06   [varn_vartani] review Key_Facts_hi.txt: 3 issue(s): - Point 5 lists four "द्वित्व व्यंजन" (ड़, ढ़, ऩ, ऱ) → In standard Hindi grammar, द्वित्व व्यंजन are only ड़ and 
18-11 10:59:30   [ling_vachan_karak] REJECTED review fix Feynman_hi.txt: reviewer still reports - लिंग table lists "कहानी" under पुल्लिंग → "कहानी" is स्त्रीलिंग; move it to स्त्रीलिंग co
18-11 11:00:21   [varn_vartani] review Feynman_hi.txt: 7 issue(s): - Section 1 claims 33 consonants but lists 36 (including क्ष, त्र, ज्ञ) → Correct the count to 36 consonants or lis
18-11 11:03:07   [software_os] review PYQ_en.txt: 2 issue(s): - Example 4 (Round Robin numerical): The calculated average waiting time is 16/3 ≈ 5.33, but the answer key lists (b) 3
```
