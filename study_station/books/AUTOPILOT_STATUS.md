# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 18-11-2026 05:07 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 18-11 04:51 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 5 मिनट |
| W2 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |
| W3 | Chapter 04 visheshan kriya (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |
| W4 | Chapter 04 software os (12th Computer) | 🔎 review हो रहा है | 15 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 26 |
| key 4 | 12 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 4 | 0 | 13 |
| 12th Computer | 6 | 0 | 8 |
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
| **कुल** | **306** | **0** | **21** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 01 varn vartani (Hindi) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
18-11 04:51:36 autopilot start: 4 workers, reverse=False
18-11 04:51:36 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
18-11 04:51:36 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (TODO: todo 1, problems 0)
18-11 04:51:36   [varn_vartani] Hindi-only writer: direct Hindi content; English generation and translation disabled
18-11 04:51:41 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
18-11 04:51:46 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya (OK: todo 0, problems 0)
18-11 04:51:51 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_04_software_os (OK: todo 0, problems 0)
18-11 04:52:20   [varn_vartani] Practice_hi_Set_03.txt try 1: rejected (parsed 24 questions, numbers 51…75)
18-11 04:52:50   [sangya_sarvanam] review Content_hi.txt: 3 issue(s): - In the table under Section 3 (लिंग, वचन और कारक), the row for pronoun "वह" lists case markers "उस ने, उस को" whic
18-11 04:53:08   [varn_vartani] Practice_hi_Set_03.txt try 2: rejected (parsed 24 questions, numbers 51…75)
18-11 04:53:49   [visheshan_kriya] review Content_hi.txt: 2 issue(s): - Section 1.3 table lists "नीला" and "मीठा" as अरूपांतरित विशेषण → they are रूपांतरित विशेषण (नीला→नीली, मीठा→मीठी)
18-11 04:55:48   [varn_vartani] Practice_hi_Set_03.txt try 3: rejected (Q58:duplicate_options)
18-11 04:55:50   [visheshan_kriya] REJECTED review fix Content_hi.txt: reviewer still reports - In section 1.3, the rule for रूपांतरित विशेषण says they end in आ and change to ई in femin
18-11 04:57:31   [visheshan_kriya] review Feynman_hi.txt: 1 issue(s): - Q1 explanation claims 'सुन्दर' in 'सुन्दर बनो' is not a विशेषण because it doesn't describe a noun; but it describ
18-11 04:57:43   [software_os] review Key_Facts_hi.txt: 1 issue(s): - Point 6 incorrectly lists Banker's Algorithm under deadlock detection; it is an avoidance algorithm → Change “प
18-11 05:01:29   [visheshan_kriya] REJECTED review fix Feynman_hi.txt: reviewer still reports - Question 1 answer and explanation are incorrect: "सुन्दर" in (घ) "सुन्दर बनो" is also an 
18-11 05:02:03   [varn_vartani] Practice_hi_Set_03.txt try 4: re-solve disagrees (Q54 key b vs re-solve d, Q57 key d vs re-solve a, Q58 key b vs re-solve a, Q62 key b vs re-solve a, 
18-11 05:02:03   [varn_vartani] REJECTED Practice_hi_Set_03.txt: no version passed the checks — not written
18-11 05:02:03   [varn_vartani] written 0, failed 1; AI calls today 26/100000
18-11 05:02:04 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani after 10 min: todo ['Set 03 hi: todo'] problems []
18-11 05:02:04 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
18-11 05:02:27   [visheshan_kriya] review Mind_Map.txt: 1 issue(s): - Node G4 "क्रियाविशेषणवाचक अव्यय" duplicates separate node F "क्रिया विशेषण" and uses non-standard terminology; in s
18-11 05:03:26   [ling_vachan_karak] review Content_hi.txt: 4 issue(s): - वचन तालिका में 'आ (स्त्रीलिंग) → एँ' नियम का उदाहरण 'लड़की → लड़कियाँ' गलत है क्योंकि 'लड़की' ई-कारांत है, आ-कारा
18-11 05:03:59   [software_os] review PYQ_en.txt: 2 issue(s): - Example 4 (Round Robin numerical) gives answer (b) 3.33 but the correct average waiting time is 16/3 ≈ 5.33; the opti
18-11 05:05:22   [visheshan_kriya] review PYQ_hi.txt: 2 issue(s): - "विशेषण का प्रकार" तालिका में "कई" को परिमाणवाचक विशेषण बताया गया है → "कई" संख्यावाचक विशेषण (अनिश्चयवाचक) है
18-11 05:06:40   [sangya_sarvanam] REJECTED review fix Content_hi.txt: reviewer still reports - "पहला अक्षर बड़ा" rule for व्यक्तिवाचक संज्ञा → Hindi Devanagari has no capital letters; 
18-11 05:06:53   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - Example 5 explanation incorrectly states the plural suffix for "भाई" as "याँ प्रत्यय" → t
18-11 05:07:35   [sangya_sarvanam] review Key_Facts_hi.txt: 5 issue(s): - Point 4: Plural rule for consonant-ending nouns incorrectly lists unchanged singular forms as plural (e.g., फल 
```
