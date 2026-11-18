# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 18-11-2026 04:14 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 18-11 03:42 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 31 मिनट |
| W2 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 31 मिनट |
| W3 | Chapter 04 visheshan kriya (10th Hindi) | 🔎 review हो रहा है | 31 मिनट |
| W4 | Chapter 04 software os (12th Computer) | 🔎 review हो रहा है | 31 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 30 |
| key 4 | 20 |

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

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
18-11 15:42:57 autopilot start: 4 workers, reverse=False
18-11 15:42:57 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
18-11 15:42:57 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
18-11 15:43:02 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
18-11 15:43:07 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya (OK: todo 0, problems 0)
18-11 15:43:12 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_04_software_os (OK: todo 0, problems 0)
18-11 15:44:23   [sangya_sarvanam] review Content_hi.txt: 1 issue(s): - Example 2 lists "हट" as a common suffix for forming abstract nouns (भाववाचक संज्ञा) → "हट" is not a valid suffix;
18-11 15:45:31   [varn_vartani] review Content_hi.txt: 6 issue(s): - The claim that Hindi has 39 consonants (व्यंजन) is inconsistent with the given breakdown (5 vargas ×5 =25, 8 avar
18-11 15:47:45   [sangya_sarvanam] REJECTED review fix Content_hi.txt: reviewer still reports - In Section 3 table (लिंग, वचन और कारक), the 'कारक चिह्न' column shows singular oblique ca
18-11 15:48:36   [varn_vartani] REJECTED review fix Content_hi.txt: reviewer still reports - The example "सँभालना" in section 2.1 and practice question 1 incorrectly presents chandra
18-11 15:49:25   [sangya_sarvanam] review Key_Facts_hi.txt: 2 issue(s): - In point 13, the declension of “क्या” incorrectly includes “किसे” as a dative form; “क्या” (for inanimate) has 
18-11 15:50:02   [varn_vartani] review Key_Facts_hi.txt: 3 issue(s): - बिंदु 18 में चंद्रबिंदु के उदाहरण गलत हैं: "मँहगा" और "पँख" मानक हिंदी वर्तनी नहीं हैं → सही उदाहरण: "महँगा" (च
18-11 15:51:59   [sangya_sarvanam] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Section 16 (भाववाचक बनाना): Rule heading says suffix "ता/ती" but example "मीठा → मिठास"
18-11 15:52:32   [varn_vartani] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 1: The breakdown of 41 consonants includes “2 नुक्ता-युक्त व्यंजन (ऩ, ऱ)”; these 
18-11 15:53:52   [varn_vartani] review Feynman_hi.txt: 5 issue(s): - Section 1 claims 33 consonants but lists 36 items (including क्ष, त्र, ज्ञ) → Either list only the 33 basic conso
18-11 15:57:07   [visheshan_kriya] review Content_hi.txt: 3 issue(s): - In Section 1.3 table, 'नीला' and 'मीठा' are incorrectly classified as अरूपांतरित विशेषण; they are रूपांतरित विशेष
18-11 15:57:25   [varn_vartani] REJECTED review fix Feynman_hi.txt: reviewer still reports - In section 4 table, the row for "आश्चर्य" shows both correct and incorrect spellings as i
18-11 15:59:58   [visheshan_kriya] REJECTED review fix Content_hi.txt: reviewer still reports - In section 1.3 table, "हरा" is listed as अरूपांतरित विशेषण but it is रूपांतरित (हरा → हरी
18-11 16:01:51   [sangya_sarvanam] review PYQ_hi.txt: 4 issue(s): - Section 5 "कारक चिह्न लोप" trap incorrectly marks "राम घर गया" as अशुद्ध and gives contradictory corrections → "राम घ
18-11 16:01:52   [software_os] review Feynman_en.txt: 1 issue(s): - Windows boot process incorrectly states Windows Boot Manager directly loads ntoskrnl.exe, skipping the Windows OS
18-11 16:03:58   [visheshan_kriya] review Mind_Map.txt: 1 issue(s): - क्रिया (Verb) को कारक (Case) से जोड़ा गया है → क्रिया का कारक नहीं होता; कारक संज्ञा, सर्वनाम, विशेषण पर लागू होता 
18-11 16:05:32   [varn_vartani] review Flashcards_hi.txt: 6 issue(s): - Card 1: States Hindi alphabet has 41 consonants (52 total) → Standard Hindi varnamala has 11 vowels and 33 con
18-11 16:06:25   [software_os] REJECTED review fix Feynman_en.txt: reviewer still reports - Windows NT is incorrectly classified as a monolithic kernel; it is a hybrid kernel → Mono
18-11 16:09:22   [varn_vartani] REJECTED review fix Flashcards_hi.txt: reviewer still reports - Card 1: Incorrect consonant count — claims 25 vargiya + 8 avargiya + ड़, ढ़ = 33, but 
18-11 16:09:25   [sangya_sarvanam] REJECTED review fix PYQ_hi.txt: reviewer still reports - खंड 1 में "माँ" को व्यक्तिवाचक संज्ञा बताया गया है, जबकि "माँ" जातिवाचक संज्ञा है। → "माँ" जा
18-11 16:11:43   [varn_vartani] review PYQ_hi.txt: 2 issue(s): - 1.2 अशुद्ध वर्तनी पहचान के हल में बताया गया है कि "विधालय" में 'ध' के बाद 'आ' की मात्रा गलत है, जबकि त्रुटि 'ध' के स्
18-11 16:12:33   [sangya_sarvanam] review Important_Rules_hi.txt: 5 issue(s): - नियम २ में "ई" कारांत पुल्लिंग के उदाहरण "पुत्री" और "नौकरानी" गलत हैं क्योंकि ये स्त्रीलिंग हैं → "ई" का
```
