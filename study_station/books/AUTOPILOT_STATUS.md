# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 11:27 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 08:36 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 2 मिनट |
| W2 | Chapter 10 paryayvachi (10th Hindi) | ✍️ लिख रहा है | 103 मिनट |
| W3 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 170 मिनट |
| W4 | Chapter 08 samas (10th Hindi) | 🔎 review हो रहा है | 42 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 72 |
| key 4 | 97 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 7 | 0 | 10 |
| 12th Computer | 9 | 0 | 5 |
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
| **कुल** | **312** | **0** | **15** |

## ✅ autopilot से हाल में पूरे हुए

- 19-11 23:24 — 12th Computer · Chapter 09 powerpoint
- 19-11 21:39 — 12th Computer · Chapter 07 word
- 19-11 21:00 — 12th Computer · Chapter 08 excel
- 19-11 20:42 — 10th Hindi · Chapter 06 kaal vachya

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 01 varn vartani (Hindi) — 2 बार
- Chapter 08 samas (Hindi) — 1 बार
- Chapter 09 upsarg pratyay (Hindi) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 22:33:26   [varn_vartani] written 1, failed 1; AI calls today 113/100000
19-11 22:33:26 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani after 22 min: todo [] problems []
19-11 22:33:27 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_08_samas (TODO: todo 1, problems 0)
19-11 22:33:27   [samas] Hindi-only writer: direct Hindi content; English generation and translation disabled
19-11 22:34:10   [paryayvachi] wrote Practice_hi_Set_01.txt (write, 25 MCQs)
19-11 22:36:12   [samas] Practice_hi_Set_03.txt try 1: rejected (parsed 24 questions, numbers 51…75)
19-11 22:37:35   [samas] Practice_hi_Set_03.txt try 2: rejected (parsed 24 questions, numbers 51…75)
19-11 22:38:04   [sandhi] Practice_hi_Set_02.txt try 2: re-solve disagrees (Q26 key b vs re-solve c, Q30 key b vs re-solve ?, Q32 key b vs re-solve d, Q36 key d vs re-solve ?, 
19-11 22:44:35   [samas] wrote Practice_hi_Set_03.txt (write, 25 MCQs)
19-11 22:44:35   [samas] written 1, failed 0; AI calls today 123/100000
19-11 22:45:06   [paryayvachi] 2026-11-19 17:15:06,564 WARNING NVIDIA rate_limited — retrying in 20s
19-11 22:46:17   [paryayvachi] wrote Practice_hi_Set_02.txt (write, 25 MCQs)
19-11 22:49:24   [paryayvachi] wrote Practice_hi_Set_03.txt (write, 25 MCQs)
19-11 22:50:22   [samas] review Content_hi.txt round 1: 3 issue(s): - "हिंदी व्याकरण में मुख्यतः छह प्रकार के समास माने जाते हैं" → There are four main types (द्वन्द्व, तत्पुर
19-11 22:52:17   [sandhi] Practice_hi_Set_02.txt try 3: re-solve disagrees (Q26 key b vs re-solve a, Q28 key d vs re-solve c, Q29 key d vs re-solve b, Q30 key a vs re-solve c, 
19-11 22:53:28   [samas] review Content_hi.txt round 2: 3 issue(s): - 'अनुग्रह' is incorrectly classified as अव्ययीभाव with meaning 'कृपा के अनुसार' → 'अनुग्रह' means 'कृपा' a
19-11 22:56:41   [powerpoint] review PYQ_hi.txt round 2: 1 issue(s): - 'नकारात्मक वाक्य' जाल के उदाहरण में प्रश्न "कौन-सा" (एकवचन) है लेकिन उत्तर तीन विकल्प (`.pptm`, `.potx`, `.pp
19-11 22:57:33   [powerpoint] 2026-11-19 17:27:33,652 WARNING NVIDIA rate_limited — retrying in 20s
19-11 22:59:07   [powerpoint] review Important_Rules_en.txt: resumed private correction draft
19-11 23:00:40   [powerpoint] review Important_Rules_en.txt round 1: 1 issue(s): - Rule 13: Incorrect menu path for "Package Presentation for CD" given as "File → Export → Package 
19-11 23:03:42   [powerpoint] review Important_Rules_en.txt round 2: 1 issue(s): - Rule 7 exception states Presenter View can be used with a single monitor via the “Use Presenter V
19-11 23:04:06   [powerpoint] 2026-11-19 17:34:06,852 WARNING NVIDIA rate_limited — retrying in 20s
19-11 23:06:44   [sandhi] FAILED Practice_hi_Set_02.txt: too_long
19-11 23:07:23   [sandhi] Practice_hi_Set_03.txt try 1: rejected (Q61:duplicate_options)
19-11 23:09:15   [powerpoint] review Important_Rules_hi.txt round 1: 3 issue(s): - नियम 3: एक्सेंट 1 (Accent 1) थीम रंग बदलने से हाइपरलिंक का रंग नहीं बदलता → हाइपरलिंक रंग अलग "हा
19-11 23:11:38   [samas] review Key_Facts_hi.txt round 1: 4 issue(s): - Point 3: Examples "अनुराग" and "उपवन" for अव्ययीभाव are incorrect; they are not used as indeclinables. 
19-11 23:12:55   [samas] review Key_Facts_hi.txt round 2: 3 issue(s): - "अनुकूल" को अव्ययीभाव समास का उदाहरण बताया गया है → "अनुकूल" अव्ययीभाव नहीं है (यह विशेषण/तत्पुरुष/कर्म
19-11 23:15:35   [samas] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 3: “उपवन” and “अनुज” are wrongly cited as अव्ययीभाव examples; they are तत्पुरुष स
19-11 23:17:13   [samas] review Feynman_hi.txt round 1: 3 issue(s): - The example "न + विद्या = अविद्या (कर्मधारय समास)" is incorrect; अविद्या is a नञ् तत्पुरुष (नञ् समास), no
19-11 23:18:54   [samas] review Mind_Map.txt round 1: 3 issue(s): - Node D labeled "बहुव्रीहि समास" but its children D1/D2 describe द्वंद्व types (इतरेतर द्वंद्व, समाहार द्वंद
19-11 23:20:41   [samas] review Mind_Map.txt round 2: 1 issue(s): - "सुंदरकांड" listed under बहुव्रीहि (गुण/विशेषण बोधक) is a wrong example; it is a कर्मधारय/तत्पुरुष compound
19-11 23:23:13   [powerpoint] review Important_Rules_hi.txt round 2: 1 issue(s): - नियम 6: "मूल चित्र एम्बेड रहता है, संपीड़ित प्रति सहेजी जाती है" गलत है → पावरपॉइंट में चित्र संप
19-11 23:24:37   [powerpoint] review: 4 section(s) corrected, 0 failed
19-11 23:24:37   [powerpoint] written 4, failed 0; AI calls today 163/100000
19-11 23:24:49   [sandhi] Practice_hi_Set_03.txt try 2: re-solve disagrees (Q54 key a vs re-solve c, Q56 key c vs re-solve a, Q58 key d vs re-solve c, Q59 key c vs re-solve b, 
19-11 23:25:01 DONE 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_09_powerpoint in 105 min → 56074b8e
19-11 23:25:01 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
19-11 23:25:02   [varn_vartani] review Important_Rules_hi.txt: resumed private correction draft
19-11 23:25:29   [paryayvachi] wrote Practice_hi_Set_04.txt (write, 25 MCQs)
19-11 23:26:51   [samas] REJECTED review fix Mind_Map.txt: reviewer still reports - कर्मधारय समास is incorrectly listed as a main type of समास; it is a sub-type of तत्पुरुष सम
```
