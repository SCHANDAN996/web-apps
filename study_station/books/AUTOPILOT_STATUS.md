# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 20-11-2026 07:59 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 20-11 07:28 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 31 मिनट |
| W2 | Chapter 09 upsarg pratyay (10th Hindi) | 🔎 review हो रहा है | 31 मिनट |
| W3 | Chapter 10 paryayvachi (10th Hindi) | 🔎 review हो रहा है | 31 मिनट |
| W4 | Chapter 11 vilom (10th Hindi) | 🔎 review हो रहा है | 31 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 11 |
| key 4 | 24 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 10 | 0 | 7 |
| 12th Computer | 11 | 0 | 3 |
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
| **कुल** | **317** | **0** | **10** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
20-11 07:28:02 autopilot start: 4 workers, reverse=False
20-11 07:28:02 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
20-11 07:28:03 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_07_sandhi (TODO: todo 5, problems 0)
20-11 07:28:04   [sandhi] Hindi-only writer: direct Hindi content; English generation and translation disabled
20-11 07:28:08 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_09_upsarg_pratyay (OK: todo 0, problems 0)
20-11 07:28:08   [upsarg_pratyay] review Content_hi.txt: resumed private correction draft
20-11 07:28:13 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_10_paryayvachi (OK: todo 0, problems 0)
20-11 07:28:13   [paryayvachi] review Important_Rules_hi.txt: resumed private correction draft
20-11 07:28:18 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_11_vilom (OK: todo 0, problems 0)
20-11 07:28:18   [vilom] review Content_hi.txt: resumed private correction draft
20-11 07:29:09   [sandhi] Practice_hi_Set_01.txt try 1: rejected (Q1:duplicate_options,Q3:duplicate_options,Q5:duplicate_options,Q7:duplicate_options,Q9:duplicate_options)
20-11 07:30:05   [sandhi] Practice_hi_Set_01.txt try 2: rejected (Q1:duplicate_options,Q3:duplicate_options,Q5:duplicate_options,Q7:duplicate_options,Q9:duplicate_options)
20-11 07:31:14   [upsarg_pratyay] review Content_hi.txt round 1: 2 issue(s): - In the कृदंत प्रत्यय table, the row for suffix **"-त्व / -त"** lists **"सत्य"** as an example for **"-त"*
20-11 07:34:03   [upsarg_pratyay] review Content_hi.txt round 2: 2 issue(s): - In the कृदंत प्रत्यय table (section 3.2 क), the row for “-त्व / -त” is incorrectly classified as a कृदंत 
20-11 07:36:31   [paryayvachi] review Important_Rules_hi.txt round 1: 4 issue(s): - नियम २ के उदाहरण में "बालक" दो बार लिखा गया है → तीसरे स्थान पर "बालक" के स्थान पर भिन्न रूप जैसे
20-11 07:38:19   [upsarg_pratyay] REJECTED review fix Content_hi.txt: reviewer still reports - The स्त्रीलिंग प्रत्यय table lists suffix '-त्री' with example 'गायक → गायिका', but '-त्र
20-11 07:38:19   [upsarg_pratyay] review Key_Facts_hi.txt: resumed private correction draft
20-11 07:38:29   [sandhi] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q4 key d vs re-solve b, Q6 key a vs re-solve d, Q7 key b vs re-solve c, Q8 key a vs re-solve c, Q9 k
20-11 07:39:53   [vilom] review Content_hi.txt round 1: 1 issue(s): - Common Errors, Error 2 incorrectly states that 'कुरूप' is a masculine adjective with feminine form 'कुरूप
20-11 07:40:03   [upsarg_pratyay] review Key_Facts_hi.txt round 1: 3 issue(s): - Point 6: Example "लिख" + "न" = "लिखना" does not show a part-of-speech change (it remains a verb) → Repl
20-11 07:42:35   [upsarg_pratyay] review Key_Facts_hi.txt round 2: 3 issue(s): - Point 20: Example “पा + न = पाना” is wrong; the infinitive suffix is “ना”, not “न”. → Correct: “पा + ना
20-11 07:44:00   [upsarg_pratyay] review Feynman_hi.txt: resumed private correction draft
20-11 07:45:22   [sandhi] Practice_hi_Set_01.txt try 4: rejected (Q1:duplicate_options)
20-11 07:45:22   [sandhi] REJECTED Practice_hi_Set_01.txt: no version passed the checks — not written
20-11 07:45:52   [upsarg_pratyay] review Feynman_hi.txt round 1: 3 issue(s): - Section 2 table (उपसर्ग "उप-"): example "चार" → "उपचार" uses wrong root "चार" (which means four); the roo
20-11 07:46:26   [sandhi] Practice_hi_Set_02.txt try 1: rejected (Q44:duplicate_options)
20-11 07:49:19   [upsarg_pratyay] review Feynman_hi.txt round 2: 3 issue(s): - अनुचित का विच्छेद गलत (उदाहरण 1 और फ्लैशकार्ड 11): 'अनु + चित (चि+त)' दिया गया है → सही विच्छेद: 'अनु + उ
20-11 07:51:19   [upsarg_pratyay] review Flashcards_hi.txt: resumed private correction draft
20-11 07:53:02   [upsarg_pratyay] review Flashcards_hi.txt round 1: 1 issue(s): - Card 18: The sandhi explanation for “दुर्नीति” incorrectly claims the prefix becomes “दुर्”; actually 
20-11 07:54:53   [upsarg_pratyay] review Flashcards_hi.txt round 2: 4 issue(s): - Card 4: The example “दु+” + “कर्म” = “दुष्कर्म” is wrong; the prefix “दु-” becomes “दुः” before क, so 
20-11 07:56:51   [upsarg_pratyay] REJECTED review fix Flashcards_hi.txt: reviewer still reports - Card 4: "दु-" उपसर्ग के नियम में त्रुटि → लिखा है "क, ख, ग, घ, ङ के पहले विसर्ग हो जात
20-11 07:56:51   [upsarg_pratyay] review PYQ_hi.txt: resumed private correction draft
20-11 07:58:07   [sandhi] Practice_hi_Set_02.txt try 2: re-solve disagrees (Q26 key d vs re-solve c, Q28 key b vs re-solve c, Q29 key a vs re-solve c, Q30 key a vs re-solve ?, 
20-11 07:58:08   [upsarg_pratyay] review PYQ_hi.txt round 1: 2 issue(s): - In Pattern B, option (a) incorrectly lists the suffix as "नीया" instead of "नीय" → Option (a) should read "नी
20-11 07:59:07   [vilom] review Key_Facts_hi.txt: resumed private correction draft
20-11 07:59:07   [vilom] 2026-11-20 02:29:07,774 WARNING NVIDIA rate_limited — retrying in 20s
```
