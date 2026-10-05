# 📚 Book Autopilot — लाइव स्थिति

**आख़िरी update:** 05-10-2026 10:03 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 05-10 09:32 PM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 Noun (Graduation English) | 🔎 review हो रहा है | 14 मिनट |
| W2 | Chapter 02 Pronoun (Graduation English) | ✍️ लिख रहा है | 30 मिनट |
| W3 | Chapter 03 Adjective (Graduation English) | ✍️ लिख रहा है | 30 मिनट |
| W4 | Chapter 05 Tense (Graduation English) | ✍️ लिख रहा है | 18 मिनट |

## 📊 हर किताब की प्रगति

| किताब | ✅ पूरे | 🔧 सुधार बाकी | 📝 लिखना बाकी |
|---|---|---|---|
| 10th GK | 19 | 0 | 0 |
| 10th Reasoning | 22 | 0 | 0 |
| 10th Maths | 9 | 13 | 0 |
| 10th English | 0 | 0 | 20 |
| 12th Maths | 0 | 0 | 23 |
| 12th GK | 0 | 0 | 24 |
| 12th Reasoning | 0 | 0 | 25 |
| 12th English | 0 | 0 | 25 |
| Graduation Maths | 0 | 0 | 28 |
| Graduation GK | 0 | 0 | 28 |
| Graduation Reasoning | 0 | 0 | 30 |
| Graduation English | 2 | 0 | 28 |
| **कुल** | **52** | **13** | **231** |

## ✅ autopilot से हाल में पूरे हुए

- 05-10 21:44 — Graduation English · Chapter 04 Verb

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
05-10 21:44:59   [Verb] File "/home/user/web-apps/study_station/v2/app/bookgen.py", line 640, in main
05-10 21:44:59   [Verb] written, failed = review(db, chapter)
05-10 21:44:59   [Verb] ^^^^^^^^^^^^^^^^^^^
05-10 21:44:59   [Verb] File "/home/user/web-apps/study_station/v2/app/bookgen.py", line 519, in review
05-10 21:44:59   [Verb] issues = _review_issues(_ask_review(db, review_request(name, text)))
05-10 21:44:59   [Verb] ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
05-10 21:44:59   [Verb] File "/home/user/web-apps/study_station/v2/app/bookgen.py", line 503, in _ask_review
05-10 21:44:59   [Verb] return nvidia.call(REVIEW_SYSTEM, user, max_tokens=MAX_TOKENS, temperature=0, model=config.NVIDIA_CHECK_MODEL)
05-10 21:44:59   [Verb] ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
05-10 21:44:59   [Verb] File "/home/user/web-apps/study_station/v2/app/nvidia.py", line 29, in call
05-10 21:44:59   [Verb] return _call_once(system, user, max_tokens, temperature, model)
05-10 21:44:59   [Verb] ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
05-10 21:44:59   [Verb] File "/home/user/web-apps/study_station/v2/app/nvidia.py", line 82, in _call_once
05-10 21:44:59   [Verb] raise AIUnavailable('empty')
05-10 21:44:59   [Verb] app.ai.AIUnavailable: empty
05-10 21:45:05 DONE Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_04_Verb in 13 min → a151d95
05-10 21:45:05 START Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_05_Tense (TODO: todo 26, problems 0)
05-10 21:45:27   [Pronoun] wrote Practice_en_Set_04.txt (write, 25 MCQs)
05-10 21:46:36   [Tense] wrote Content_en.txt (7122 chars)
05-10 21:47:44   [Adjective] wrote Practice_en_Set_03.txt (write, 25 MCQs)
05-10 21:48:05   [Pronoun] wrote Practice_hi_Set_04.txt (translate from Practice_en_Set_04.txt, 25 MCQs)
05-10 21:48:10   [Noun] wrote Practice_hi_Set_06.txt (translate from Practice_en_Set_06.txt, 25 MCQs)
05-10 21:48:10   [Noun] written 2, failed 0; AI calls today 315/100000
05-10 21:48:53   [Noun] repaired Mind_Map_hi.txt (2118 chars)
05-10 21:48:53   [Noun] written 1, failed 0; AI calls today 316/100000
05-10 21:49:08   [Tense] wrote Content_hi.txt (8350 chars)
05-10 21:49:50   [Tense] wrote Feynman_en.txt (2918 chars)
05-10 21:50:56   [Adjective] wrote Practice_hi_Set_03.txt (translate from Practice_en_Set_03.txt, 25 MCQs)
05-10 21:51:24   [Tense] wrote Feynman_hi.txt (2507 chars)
05-10 21:51:53   [Tense] wrote Mind_Map_en.txt (2131 chars)
05-10 21:52:22   [Tense] wrote Mind_Map_hi.txt (1711 chars)
05-10 21:53:35   [Tense] wrote Flashcards_en.txt (4448 chars)
05-10 21:55:20   [Tense] wrote Flashcards_hi.txt (4172 chars)
05-10 21:56:33   [Tense] wrote PYQ_en.txt (7207 chars)
05-10 21:56:45   [Noun] review Content_en.txt: 1 issue(s): - The mnemonic SIT-PC lists "Irons (spectacles/goggles family)" but "irons" does not mean spectacles/goggles → Repl
05-10 21:57:54   [Pronoun] Practice_en_Set_05.txt try 1: re-solve disagrees (Q103 key b vs re-solve a, Q123 key b vs re-solve a, Q124 key c vs re-solve a)
05-10 21:58:04   [Tense] wrote PYQ_hi.txt (6136 chars)
05-10 21:59:41   [Tense] wrote Short_Tricks_en.txt (7916 chars)
05-10 22:00:59   [Tense] wrote Short_Tricks_hi.txt (7353 chars)
05-10 22:02:29   [Tense] wrote Important_Rules_en.txt (5694 chars)
```
