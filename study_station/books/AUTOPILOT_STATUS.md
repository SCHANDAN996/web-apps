# 📚 Book Autopilot — लाइव स्थिति

**आख़िरी update:** 05-10-2026 10:18 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 05-10 09:32 PM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 06 Adverb (Graduation English) | ✍️ लिख रहा है | 13 मिनट |
| W2 | Chapter 02 Pronoun (Graduation English) | ✍️ लिख रहा है | 46 मिनट |
| W3 | Chapter 03 Adjective (Graduation English) | 🔎 review हो रहा है | 3 मिनट |
| W4 | Chapter 05 Tense (Graduation English) | ✍️ लिख रहा है | 33 मिनट |

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
| Graduation English | 3 | 0 | 27 |
| **कुल** | **53** | **13** | **230** |

## ✅ autopilot से हाल में पूरे हुए

- 05-10 22:04 — Graduation English · Chapter 01 Noun
- 05-10 21:44 — Graduation English · Chapter 04 Verb

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
05-10 22:04:44   [Noun] File "<frozen runpy>", line 198, in _run_module_as_main
05-10 22:04:44   [Noun] File "<frozen runpy>", line 88, in _run_code
05-10 22:04:44   [Noun] File "/home/user/web-apps/study_station/v2/app/bookgen.py", line 654, in <module>
05-10 22:04:44   [Noun] sys.exit(main())
05-10 22:04:44   [Noun] ^^^^^^
05-10 22:04:44   [Noun] File "/home/user/web-apps/study_station/v2/app/bookgen.py", line 640, in main
05-10 22:04:44   [Noun] written, failed = review(db, chapter)
05-10 22:04:44   [Noun] ^^^^^^^^^^^^^^^^^^^
05-10 22:04:44   [Noun] File "/home/user/web-apps/study_station/v2/app/bookgen.py", line 519, in review
05-10 22:04:44   [Noun] issues = _review_issues(_ask_review(db, review_request(name, text)))
05-10 22:04:44   [Noun] ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
05-10 22:04:44   [Noun] File "/home/user/web-apps/study_station/v2/app/bookgen.py", line 503, in _ask_review
05-10 22:04:44   [Noun] return nvidia.call(REVIEW_SYSTEM, user, max_tokens=MAX_TOKENS, temperature=0, model=config.NVIDIA_CHECK_MODEL)
05-10 22:04:44   [Noun] ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
05-10 22:04:44   [Noun] File "/home/user/web-apps/study_station/v2/app/nvidia.py", line 29, in call
05-10 22:04:44   [Noun] return _call_once(system, user, max_tokens, temperature, model)
05-10 22:04:44   [Noun] ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
05-10 22:04:44   [Noun] File "/home/user/web-apps/study_station/v2/app/nvidia.py", line 82, in _call_once
05-10 22:04:44   [Noun] raise AIUnavailable('empty')
05-10 22:04:44   [Noun] app.ai.AIUnavailable: empty
05-10 22:04:50 DONE Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_01_Noun in 33 min → b12aba8
05-10 22:04:50 START Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_06_Adverb (TODO: todo 26, problems 0)
05-10 22:07:13   [Pronoun] Practice_en_Set_05.txt try 2: re-solve disagrees (Q123 key c vs re-solve a, Q124 key b vs re-solve a)
05-10 22:09:27   [Tense] FAILED Practice_en_Set_01.txt: empty
05-10 22:09:27   [Tense] skip Practice_hi_Set_01.txt: its pair Practice_en_Set_01.txt was not written
05-10 22:09:39   [Adverb] FAILED Content_en.txt: empty
05-10 22:09:54   [Adjective] wrote Practice_en_Set_06.txt (write, 25 MCQs)
05-10 22:12:19   [Adverb] wrote Content_hi.txt (7629 chars)
05-10 22:13:05   [Adjective] wrote Practice_hi_Set_06.txt (translate from Practice_en_Set_06.txt, 25 MCQs)
05-10 22:13:05   [Adjective] written 6, failed 0; AI calls today 345/100000
05-10 22:14:17   [Adjective] repaired Mind_Map_hi.txt (2283 chars)
05-10 22:14:17   [Adjective] written 1, failed 0; AI calls today 346/100000
05-10 22:14:34   [Pronoun] Practice_en_Set_05.txt try 3: re-solve disagrees (Q113 key d vs re-solve c)
05-10 22:14:34   [Pronoun] REJECTED Practice_en_Set_05.txt: no version passed the checks — not written
05-10 22:14:34   [Pronoun] skip Practice_hi_Set_05.txt: its pair Practice_en_Set_05.txt was not written
05-10 22:15:05   [Tense] wrote Practice_en_Set_02.txt (write, 25 MCQs)
05-10 22:15:18   [Adverb] wrote Feynman_en.txt (2522 chars)
05-10 22:16:50   [Adverb] wrote Feynman_hi.txt (2959 chars)
05-10 22:17:32   [Adverb] wrote Mind_Map_en.txt (2414 chars)
05-10 22:18:02   [Adjective] review Content_en.txt: 2 issue(s): - The claim that almost every SSC CGL, IBPS PO, and State PCS prelims paper has 2–4 adjective-error questions is an
```
