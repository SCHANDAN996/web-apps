# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 01:48 AM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 01:32 AM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 16 मिनट |
| W2 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |
| W3 | Chapter 04 visheshan kriya (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |
| W4 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 15 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 18 |
| key 4 | 16 |

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
19-11 01:32:18 autopilot start: 4 workers, reverse=False
19-11 01:32:18 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
19-11 01:32:18 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
19-11 01:32:23 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
19-11 01:32:28 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya (OK: todo 0, problems 0)
19-11 01:32:33 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
19-11 01:33:22   [sangya_sarvanam] review Content_hi.txt: 2 issue(s): - In the case-marker table, for 'फल (पुं.)' the singular oblique forms are shown as 'फले ने, फले को' → should be 'फ
19-11 01:33:41   [varn_vartani] review Content_hi.txt: 1 issue(s): - The मात्रा-नियम table lists incorrect examples for 'इ' (ि): "फल" → "फिल" (अशुद्ध) and "फूल" → "फुल" (अशुद्ध) inst
19-11 01:34:50   [visheshan_kriya] review Content_hi.txt: 1 issue(s): - In section 1.3 table, 'नीला' and 'मीठा' are incorrectly classified as अरूपांतरित विशेषण; they are रूपांतरित विशेष
19-11 01:34:58   [sangya_sarvanam] REJECTED review fix Content_hi.txt: reviewer still reports - The rule for ergative "ने" is incorrectly generalized to all past tense (भूतकाल) for tran
19-11 01:36:49   [visheshan_kriya] REJECTED review fix Content_hi.txt: reviewer still reports - नियम "विशेषण हमेशा संज्ञा/सर्वनाम के लिंग, वचन, कारक के अनुसार बदलता है" गलत है क्योंकि अ
19-11 01:37:10   [varn_vartani] REJECTED review fix Content_hi.txt: reviewer still reports - In Worked Example 1, the explanation for "संभव" says the anusvara appears before 'प' (पवर
19-11 01:38:12   [varn_vartani] review Key_Facts_hi.txt: 4 issue(s): - Point 6 lists only two nuqta‑letters (ऩ, ऱ) and calls them the only नुक्ता‑युक्त व्यंजन; in standard Hindi the 
19-11 01:39:29   [sangya_sarvanam] review Key_Facts_hi.txt: 3 issue(s): - In point 6, the example “लड़कोंने खेला” uses a singular verb “खेला” with the plural subject “लड़कोंने”; the ver
19-11 01:39:40   [ling_vachan_karak] review Content_hi.txt: 5 issue(s): - In लिंग-परिवर्तन rules, "अध्यापक" is listed as अपरिवर्तनीय (invariant for both genders), but its feminine form is
19-11 01:41:59   [sangya_sarvanam] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - बिंदु 6 (कारक चिह्न) में "पूर्णिक" शब्द गलत है → मानक व्याकरण में "पूर्ण" या "परिपूर्ण"
19-11 01:42:55   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - In the "लिंग के प्रकार" table, नपुंसकलिंग examples incorrectly include "पत्तल" (स्त्रीलिं
19-11 01:43:14   [visheshan_kriya] review Flashcards_hi.txt: 1 issue(s): - Card 11: Rule for simple future tense says "क्रिया मूल + 'गा/गे/गी'" but examples like "जाएगा", "खाएंगे", "पढ़
19-11 01:43:59   [ling_vachan_karak] review Key_Facts_hi.txt: 6 issue(s): - Point 4: Statement that inanimate objects are neuter (नपुंसकलिंग) is incorrect; Hindi inanimate nouns have masc
19-11 01:45:09   [varn_vartani] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 1 claims there are “2 नुक्ता-युक्त व्यंजन” in the traditional 52‑letter count, bu
19-11 01:46:11   [varn_vartani] review Feynman_hi.txt: 5 issue(s): - Section 1 claims "33 व्यंजन" but lists 36 items (including क्ष, त्र, ज्ञ) → either change the count to 36 or remo
19-11 01:46:37   [ling_vachan_karak] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 7: The rule for feminine of ī-kārant masculine nouns incorrectly cites non-ī-kāra
19-11 01:47:53   [ling_vachan_karak] review Feynman_hi.txt: 1 issue(s): - The second common mistake example "राम को बुलाओ" is labeled for past tense subject but is an imperative sentence 
```
