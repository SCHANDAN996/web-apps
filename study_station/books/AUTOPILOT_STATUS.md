# 📚 Book Autopilot — लाइव स्थिति (four-chapters)

**आख़िरी update:** 19-11-2026 05:28 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 19-11 03:11 PM

> Nemotron-3-Ultra लिखता है → Ultra की अलग request हर सवाल हल करके उत्तर जाँचती है → `bookcheck` → Ultra reviewer हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 07 word (12th Computer) | 🔎 review हो रहा है | 14 मिनट |
| W2 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 100 मिनट |
| W3 | Chapter 06 kaal vachya (10th Hindi) | 🔎 review हो रहा है | 16 मिनट |
| W4 | Chapter 01 varn vartani (10th Hindi) | 🔎 review हो रहा है | 9 मिनट |

| सक्रिय API key | इस रन में शुरू हुई requests |
|---|---|
| key 3 | 101 |
| key 4 | 99 |

**बाकी साथ चल रहे runs:** [lane-2](autopilot/lane-2.md) · [lane-3](autopilot/lane-3.md) · [lane-4](autopilot/lane-4.md) · [lane-5](autopilot/lane-5.md) · [lane-6](autopilot/lane-6.md)

## 📊 हर किताब की प्रगति

ये गिनती लेखन और `bookcheck` की प्रारंभिक जाँच की है। अंतिम editorial review पास होना अलग है; सिर्फ़ इस तालिका से अध्याय को अंतिम स्वीकृत न मानें।

| किताब | प्रारंभिक जाँच पास | संरचना में सुधार बाकी | लिखना बाकी |
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

- Chapter 03 sangya sarvanam (Hindi) — 2 बार
- Chapter 05 ling vachan karak (Hindi) — 2 बार
- Chapter 07 word (Computer) — 1 बार
- Chapter 06 kaal vachya (Hindi) — 1 बार
- Chapter 01 varn vartani (Hindi) — 1 बार
- Chapter 08 samas (Hindi) — 1 बार

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
19-11 17:02:52   [ling_vachan_karak] review Key_Facts_hi.txt: resumed private correction draft
19-11 17:03:28   [samas] Practice_hi_Set_05.txt try 2: re-solve disagrees (Q103 key a vs re-solve d, Q107 key b vs re-solve a)
19-11 17:04:53   [ling_vachan_karak] review Key_Facts_hi.txt round 1: 3 issue(s): - Point 8: Rule states “या रूप बदलता है” but example “गुरु → गुरु (समान रूप)” shows unchanged form → Chan
19-11 17:05:52   [ling_vachan_karak] review Key_Facts_hi.txt round 2: 1 issue(s): - Point 14 example 'जू → जुएँ' uses a feminine noun (जू) for a masculine उ/ऊ-ending rule → replace with a
19-11 17:07:42   [ling_vachan_karak] review PYQ_hi.txt: resumed private correction draft
19-11 17:07:51   [samas] Practice_hi_Set_05.txt try 3: re-solve disagrees (Q107 key b vs re-solve a, Q118 key d vs re-solve b)
19-11 17:09:04   [ling_vachan_karak] review PYQ_hi.txt round 1: 1 issue(s): - In Section 7, the gender heuristic incorrectly lists साधु and गुरु as examples of ईकारान्त पुल्लिंग; they are
19-11 17:10:35   [ling_vachan_karak] review PYQ_hi.txt round 2: 2 issue(s): - Section 6 table row "कारक चिह्न लोप" claims the missing marker in "राम सीता मिला" is "को" → The verb "मिलना" 
19-11 17:12:50   [samas] Practice_hi_Set_05.txt try 4: re-solve disagrees (Q104 key b vs re-solve a, Q123 key d vs re-solve a)
19-11 17:12:50   [samas] REJECTED Practice_hi_Set_05.txt: no version passed the checks — not written
19-11 17:12:50   [samas] written 0, failed 3; AI calls today 177/100000
19-11 17:12:50 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_08_samas after 55 min: todo ['Set 01 hi: todo', 'Set 03 hi: todo', 'Set 05 hi: todo'] problems []
19-11 17:12:50 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_06_kaal_vachya (OK: todo 0, problems 0)
19-11 17:12:50   [kaal_vachya] review Content_hi.txt: resumed private correction draft
19-11 17:14:49   [ling_vachan_karak] REJECTED review fix PYQ_hi.txt: reviewer still reports - "भेड़ → भेड़ — प्रत्यक्ष कारक में एकवचन-बहुवचन समान" (Section 2) is incorrect; the direct plu
19-11 17:14:49   [ling_vachan_karak] review: 2 section(s) corrected, 1 failed
19-11 17:14:49   [ling_vachan_karak] written 2, failed 1; AI calls today 179/100000
19-11 17:14:49 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_05_ling_vachan_karak after 29 min: todo [] problems []
19-11 17:14:50 START 12th_Level/Computer/Competitive_Computer_WorldClass/Chapter_07_word (OK: todo 0, problems 0)
19-11 17:14:50   [word] review Content_hi.txt: resumed private correction draft
19-11 17:15:14   [sandhi] Practice_hi_Set_02.txt try 3: re-solve disagrees (Q26 key a vs re-solve b, Q27 key c vs re-solve b, Q35 key d vs re-solve c, Q40 key a vs re-solve c)
19-11 17:16:17   [kaal_vachya] review Content_hi.txt round 1: 2 issue(s): - In the Present Tense table, the structure for "पूर्ण सतत" incorrectly includes "से/को" as part of the ver
19-11 17:19:47   [sangya_sarvanam] REJECTED review fix Important_Rules_hi.txt: reviewer still reports - नियम ३ की तालिका में "ई कारांत (पुल्लिंग)" के बहुवचन नियम में "ओं" प्रत्यय गलत है
19-11 17:19:47   [sangya_sarvanam] review: 0 section(s) corrected, 1 failed
19-11 17:19:47   [sangya_sarvanam] written 0, failed 1; AI calls today 184/100000
19-11 17:19:47 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_03_sangya_sarvanam after 39 min: todo [] problems []
19-11 17:19:47 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_01_varn_vartani (OK: todo 0, problems 0)
19-11 17:19:47   [varn_vartani] review Key_Facts_hi.txt: resumed private correction draft
19-11 17:20:36   [word] review Content_hi.txt round 1: 1 issue(s): - फिर से करें (Redo) के लिए शॉर्टकट कॉलम में "Ctrl+Y (या Ctrl+Shift+Z)" लिखा है और स्कोप "Word" दिखाया गया 
19-11 17:21:07   [varn_vartani] review Key_Facts_hi.txt round 1: 2 issue(s): - Point 1: The breakdown “33 मूल व्यंजन + 4 संयुक्त व्यंजन + 2 द्वित्व व्यंजन + कई नुक्ता-युक्त व्यंजन = 
19-11 17:23:21   [word] review Key_Facts_en.txt: resumed private correction draft
19-11 17:24:09   [word] review Key_Facts_en.txt round 1: 3 issue(s): - Item 6: "Shift+arrow keys extend selection character/word/line/paragraph." → Shift+arrow keys extend se
19-11 17:24:21   [sandhi] Practice_hi_Set_02.txt try 4: re-solve disagrees (Q26 key a vs re-solve c, Q30 key c vs re-solve b)
19-11 17:24:21   [sandhi] REJECTED Practice_hi_Set_02.txt: no version passed the checks — not written
19-11 17:25:03   [word] review Key_Facts_en.txt round 2: 2 issue(s): - Ribbon Interface tabs list missing "Design" tab → The Ribbon tabs include Home, Insert, Design, Layout,
19-11 17:26:26   [varn_vartani] review Key_Facts_hi.txt round 2: 1 issue(s): - Point 18 lists only 10 vowels (अ, आ, इ, ई, उ, ऊ, ए, ऐ, ओ, औ) for chandrabindu usage, omitting ऋ → Inclu
19-11 17:26:57   [word] REJECTED review fix Key_Facts_en.txt: reviewer still reports - Point 20: “blue double underline = grammar” is incorrect; grammar errors are indicated 
19-11 17:26:57   [word] review PYQ_en.txt: resumed private correction draft
19-11 17:28:10   [kaal_vachya] review Content_hi.txt round 2: 1 issue(s): - In section 2.1, rules 1 and 2 for कर्तृ वाच्य → कर्म वाच्य conversion are reversed and misstated: they sa
19-11 17:28:12   [word] review PYQ_en.txt round 1: 1 issue(s): - In Example 1 solution, the statement "Ctrl + Shift + F opens the Font dialog with focus on the font list" is 
```
