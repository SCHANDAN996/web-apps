# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 18-11-2026 09:55 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 18-11 09:08 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 46 मिनट |
| W2 | Chapter 03 sangya sarvanam (10th Hindi) | 🔎 review हो रहा है | 46 मिनट |
| W3 | Chapter 05 ling vachan karak (10th Hindi) | 🔎 review हो रहा है | 32 मिनट |
| W4 | Chapter 06 kaal vachya (10th Hindi) | 🔎 review हो रहा है | 3 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 37 |
| key 4 | 34 |

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

- Chapter 04 visheshan kriya (Hindi) — 1 बार
- Chapter 04 software os (Computer) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
18-11 21:08:34 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
18-11 21:08:35 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
18-11 21:08:39 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam (OK: todo 0, problems 0)
18-11 21:08:45 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya (OK: todo 0, problems 0)
18-11 21:08:50 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_04_software_os (OK: todo 0, problems 0)
18-11 21:10:35   [visheshan_kriya] review Content_hi.txt: 1 issue(s): - In section 1.3 table 'विशेषण के रूप-परिवर्तन', 'नीला' and 'मीठा' are incorrectly classified as अरूपांतरित विशेषण 
18-11 21:10:45   [varn_vartani] review Content_hi.txt: 7 issue(s): - The consonant count claims 39 व्यंजन but the listed categories (25 वर्गीय + 8 अवर्गीय + 4 संयुक्त) total 37 → Cor
18-11 21:13:54   [visheshan_kriya] REJECTED review fix Content_hi.txt: reviewer still reports - In section 3, the exam tip "यदि शब्द के बाद 'है/हैं/था/थे/होगा/होंगे' आए → क्रिया" is inc
18-11 21:14:59   [sangya_sarvanam] review Content_hi.txt: 2 issue(s): - "परीक्षा उपयोगी सूत्र" में व्यक्तिवाचक/जातिवाचक के लिए "पहला अक्षर बड़ा/छोटे अक्षर से शुरू" लिखा है → हिंदी (देवन
18-11 21:19:35   [varn_vartani] REJECTED review fix Content_hi.txt: reviewer still reports - In Worked Example 1 (अनुस्वार/अनुनासिक), the explanation states that in "संभव" anusvar co
18-11 21:20:48   [visheshan_kriya] review PYQ_hi.txt: 1 issue(s): - In the 'क्रिया विशेषण (Adverb) भ्रम' row, the example '❌ वह धीरे-धीरे चलता है।' incorrectly marks a grammatically cor
18-11 21:20:53   [varn_vartani] review Key_Facts_hi.txt: 2 issue(s): - Point 6 lists nukta letters as ऩ and ऱ, claiming they are for Marathi/Sanskrit; in standard Hindi, nukta letter
18-11 21:22:51   [visheshan_kriya] review: 1 section(s) corrected, 1 failed
18-11 21:22:52   [visheshan_kriya] written 1, failed 1; AI calls today 23/100000
18-11 21:22:52 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_04_visheshan_kriya after 14 min: todo [] problems []
18-11 21:22:52 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak (OK: todo 0, problems 0)
18-11 21:24:08   [ling_vachan_karak] review Content_hi.txt: 5 issue(s): - Section 1 gender table misclassifies "कमरा" (masculine), "पत्तल" (feminine), "फल" (masculine), "ज्ञान" (masculine
18-11 21:24:40   [varn_vartani] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 19: Visarga sandhi rule misstated — visarga before क/ख does not become क्/ख्, and
18-11 21:27:02   [varn_vartani] review Feynman_hi.txt: 5 issue(s): - Section 1 claims 33 consonants but lists 36 items (including क्ष, त्र, ज्ञ) → Change count to 36 or list only the
18-11 21:28:49   [ling_vachan_karak] REJECTED review fix Content_hi.txt: reviewer still reports - The 'बहुवचन नियम' table's row for 'आ (स्त्रीलिंग)' gives examples 'लड़की → लड़कियाँ' and 
18-11 21:30:49   [ling_vachan_karak] review Key_Facts_hi.txt: 6 issue(s): - Point 4: Neuter gender examples (किताब, मेज, पानी, आकाश) are factually wrong; these nouns are masculine/feminin
18-11 21:33:53   [sangya_sarvanam] review Key_Facts_hi.txt: 4 issue(s): - Section 6 (कारक चिह्न): Example "लड़कोंने खेला" for "ने" is wrong because "खेलना" is intransitive; "ने" require
18-11 21:34:31   [ling_vachan_karak] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 6: Example शेर→शेरनी given for अकारांत पुल्लिंग feminine formation, but शेर is co
18-11 21:36:19   [ling_vachan_karak] review Feynman_hi.txt: 5 issue(s): - In the लिंग table, "पुस्तक" is incorrectly listed as पुल्लिंग (marked अपवाद); "पुस्तक" is स्त्रीलिंग → Move "पुस्
18-11 21:36:46   [sangya_sarvanam] REJECTED review fix Key_Facts_hi.txt: reviewer still reports - Point 4: The plural examples for consonant‑ending nouns incorrectly list the singular f
18-11 21:39:00   [ling_vachan_karak] REJECTED review fix Feynman_hi.txt: reviewer still reports - लिंग तालिका में "कहानी" को पुल्लिंग दिखाया गया है → "कहानी" स्त्रीलिंग है
18-11 21:40:22   [software_os] review Mind_Map.txt: 1 issue(s): - "Types of OS" placed as a child component of "Operating System" (alongside Kernel, Memory Management) → Move "Types
18-11 21:40:31   [ling_vachan_karak] review Flashcards_hi.txt: 1 issue(s): - Card 9 rule says "उ" को "एँ" में बदलें but examples show "गुरुएँ" (retaining उ) → Rule should be: "उ" के बाद "
18-11 21:40:56   [software_os] REJECTED review fix Mind_Map.txt: reviewer still reports - "Types of OS / ऑपरेटिंग सिस्टम के प्रकार" is incorrectly placed as a direct child of "Syste
18-11 21:43:32   [varn_vartani] REJECTED review fix Feynman_hi.txt: reviewer still reports - Table "वर्तनी के सामान्य नियम" row "अनुस्वार (ं) vs अनुनासिक (ँ)": Incorrectly states "हँ
18-11 21:44:29   [ling_vachan_karak] review PYQ_hi.txt: 3 issue(s): - Invented exam statistic: "SSC GD में इस अध्याय से 3–5 प्रश्न आते हैं" → Remove the claim or cite a specific year and 
18-11 21:48:03   [software_os] review Important_Rules_en.txt: 3 issue(s): - Rule 4: Virtual memory example incorrectly states that 8 GB RAM + 12 GB page file = 20 GB virtual address
18-11 21:48:13   [sangya_sarvanam] review PYQ_hi.txt: 5 issue(s): - Error Detection example answer (d) but error is in part (c) 'अपने' → Answer should be (c)
18-11 21:50:25   [varn_vartani] review Flashcards_hi.txt: 1 issue(s): - Card 17 incorrectly presents विशेष/बिशेष, क्षमा/कश्मा, ज्ञान/ग्यान, श्रेष्ठ/श्रेस्ठ as same‑pronunciation diff
18-11 21:51:38   [software_os] REJECTED review fix Important_Rules_en.txt: reviewer still reports - "Windows uses NTFS as the default file system since Windows NT 3.1." → Windows 95
18-11 21:51:59   [software_os] review: 0 section(s) corrected, 2 failed
18-11 21:51:59   [software_os] written 0, failed 2; AI calls today 68/100000
18-11 21:51:59 NOT OK 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_04_software_os after 43 min: todo [] problems []
18-11 21:52:00 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_06_kaal_vachya (OK: todo 0, problems 0)
18-11 21:53:16   [varn_vartani] REJECTED review fix Flashcards_hi.txt: reviewer still reports - Card 11: The रेफ example “र्क (कर्ता)” is incorrect; कर्ता uses र्त (रेफ above त) → Co
```
