# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 18-11-2026 12:45 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 17-11 11:58 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | ✍️ लिख रहा है | 46 मिनट |
| W2 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 31 मिनट |
| W3 | Chapter 04 visheshan kriya (10th Hindi) | 🔎 review हो रहा है | 6 मिनट |
| W4 | Chapter 04 software os (12th Computer) | 🔎 review हो रहा है | 46 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 13 |
| key 4 | 28 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th Hindi | 4 | 0 | 13 |
| 12th Computer | 5 | 0 | 9 |
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
| **कुल** | **305** | **0** | **22** |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
17-11 23:58:51 autopilot start: 4 workers, reverse=False
17-11 23:58:51 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
17-11 23:58:51 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (TODO: todo 2, problems 0)
17-11 23:58:51   [varn_vartani] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 23:58:56 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (TODO: todo 1, problems 0)
17-11 23:58:56   [sangya_sarvanam] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 23:59:01 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya (TODO: todo 1, problems 0)
17-11 23:59:01   [visheshan_kriya] Hindi-only writer: direct Hindi content; English generation and translation disabled
17-11 23:59:06 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_04_software_os (OK: todo 0, problems 0)
18-11 00:00:23   [varn_vartani] Practice_hi_Set_01.txt try 1: rejected (Q18:duplicate_options)
18-11 00:02:17   [sangya_sarvanam] Practice_hi_Set_01.txt try 1: re-solve disagrees (Q5 key a vs re-solve b, Q12 key d vs re-solve c, Q25 key a vs re-solve b)
18-11 00:05:43   [sangya_sarvanam] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q5 key a vs re-solve b, Q25 key a vs re-solve b)
18-11 00:09:28   [sangya_sarvanam] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q5 key d vs re-solve b)
18-11 00:12:13   [varn_vartani] Practice_hi_Set_01.txt try 2: re-solve disagrees (Q8 key d vs re-solve b, Q10 key a vs re-solve ?, Q13 key a vs re-solve b, Q24 key d vs re-solve c)
18-11 00:13:39   [sangya_sarvanam] wrote Practice_hi_Set_01.txt (write, 25 MCQs)
18-11 00:13:39   [sangya_sarvanam] written 1, failed 0; AI calls today 11/100000
18-11 00:20:41   [varn_vartani] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q4 key a vs re-solve b, Q13 key c vs re-solve b)
18-11 00:20:46   [visheshan_kriya] Practice_hi_Set_02.txt try 1: re-solve disagrees (Q46 key d vs re-solve ?, Q47 key d vs re-solve ?, Q50 key c vs re-solve b)
18-11 00:22:52   [sangya_sarvanam] review Content_hi.txt: 5 issue(s): - "परीक्षा उपयोगी सूत्र" बॉक्स में लिखा है "व्यक्तिवाचक → विशेष नाम (पहला अक्षर बड़ा)" और "जातिवाचक → सामान्य नाम (
18-11 00:26:20   [sangya_sarvanam] REJECTED review fix Content_hi.txt: reviewer still reports - "औरत" को बहुवचन में रूप न बदलने वाले शब्दों की सूची (उदाहरण 6 और त्वरित पुनरावृत्ति बिंदु
18-11 00:27:52   [sangya_sarvanam] review Key_Facts_hi.txt: 4 issue(s): - Point 4: Wrong plural forms "फलें" and "घरें" for consonant-ending nouns → Correct oblique plurals: "फलों" and 
18-11 00:32:20   [software_os] review Content_hi.txt: 2 issue(s): - "बड़ी फ़ाइलें अनुमत करता है" (उदाहरण 1 में) → "बड़ी फ़ाइलों का समर्थन करता है" या "बड़ी फ़ाइलों को अनुमति देता है
18-11 00:38:29   [varn_vartani] wrote Practice_hi_Set_01.txt (write, 25 MCQs)
18-11 00:39:28   [visheshan_kriya] wrote Practice_hi_Set_02.txt (write, 25 MCQs)
18-11 00:39:28   [visheshan_kriya] written 1, failed 0; AI calls today 31/100000
18-11 00:41:08   [varn_vartani] Practice_hi_Set_03.txt try 1: rejected (parsed 0 questions, numbers -…-)
18-11 00:41:17   [software_os] review Feynman_en.txt: 4 issue(s): - "Application software are" (grammar: software is singular) → "Application software is"
18-11 00:42:04   [visheshan_kriya] review Content_hi.txt: 1 issue(s): - In the table "विशेषण के रूप-परिवर्तन (लिंग-वचन-कारक अनुसार)", the adjectives **"नीला"** and **"मीठा"** are incorr
18-11 00:42:40   [varn_vartani] Practice_hi_Set_03.txt try 2: rejected (Q59:duplicate_options,Q64:duplicate_options,Q75:duplicate_options)
```
