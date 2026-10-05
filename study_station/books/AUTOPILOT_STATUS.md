# 📚 Book Autopilot — लाइव स्थिति

**आख़िरी update:** 05-10-2026 09:44 PM IST · हर 15 मिनट और हर पूरे अध्याय पर अपने-आप update होता है · autopilot शुरू: 05-10 09:32 PM

> NVIDIA (Kimi-K3) लिखता है → दूसरा model हर सवाल ख़ुद हल करके उत्तर जाँचता है → `bookcheck` → reviewer model हर section पढ़कर गलती सुधरवाता है → तभी push।

## ⚙️ अभी क्या चल रहा है

| worker | अध्याय | काम | कब से |
|---|---|---|---|
| W1 | Chapter 01 Noun (Graduation English) | ✍️ लिख रहा है | 12 मिनट |
| W2 | Chapter 02 Pronoun (Graduation English) | ✍️ लिख रहा है | 12 मिनट |
| W3 | Chapter 03 Adjective (Graduation English) | ✍️ लिख रहा है | 12 मिनट |
| W4 | Chapter 04 Verb (Graduation English) | 📤 push हो रहा है | 0 मिनट |

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
| Graduation English | 1 | 0 | 29 |
| **कुल** | **51** | **13** | **232** |

## ✅ autopilot से हाल में पूरे हुए

- 05-10 21:44 — Graduation English · Chapter 04 Verb

## 📜 हाल की गतिविधि (नया सबसे नीचे)

```
05-10 21:27:32   [Adjective] Practice_en_Set_06.txt try 1: rejected (parsed 14 questions, numbers 126…149)
05-10 21:30:11   [Adjective] Practice_en_Set_06.txt try 2: rejected (parsed 12 questions, numbers 126…149)
05-10 21:30:26   [Verb] wrote Practice_en_Set_06.txt (write, 25 MCQs)
05-10 21:30:30   [Pronoun] wrote Practice_en_Set_03.txt (write, 25 MCQs)
05-10 21:32:07 autopilot start: 4 workers, reverse=True
05-10 21:32:07 START Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_01_Noun (TODO: todo 2, problems 1)
05-10 21:32:12 START Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_02_Pronoun (TODO: todo 7, problems 1)
05-10 21:32:17 START Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_03_Adjective (TODO: todo 6, problems 1)
05-10 21:32:22 START Graduation_Level/English/Advanced_Graduation_English_WorldClass/Chapter_04_Verb (TODO: todo 3, problems 0)
05-10 21:34:33   [Pronoun] wrote Practice_hi_Set_03.txt (translate from Practice_en_Set_03.txt, 25 MCQs)
05-10 21:34:58   [Verb] wrote Practice_en_Set_02.txt (write, 25 MCQs)
05-10 21:35:46   [Adjective] wrote Practice_en_Set_01.txt (write, 25 MCQs)
05-10 21:37:27   [Noun] Practice_en_Set_06.txt try 1: re-solve disagrees (Q132 key b vs re-solve ?)
05-10 21:37:34   [Verb] wrote Practice_hi_Set_02.txt (translate from Practice_en_Set_02.txt, 25 MCQs)
05-10 21:38:14   [Adjective] wrote Practice_hi_Set_01.txt (translate from Practice_en_Set_01.txt, 25 MCQs)
05-10 21:40:35   [Verb] wrote Practice_hi_Set_06.txt (translate from Practice_en_Set_06.txt, 25 MCQs)
05-10 21:40:35   [Verb] written 3, failed 0; AI calls today 306/100000
05-10 21:41:31   [Pronoun] Practice_en_Set_04.txt try 1: re-solve disagrees (Q83 key d vs re-solve a)
05-10 21:44:50   [Noun] wrote Practice_en_Set_06.txt (write, 25 MCQs)
05-10 21:44:59   [Verb] Traceback (most recent call last):
05-10 21:44:59   [Verb] File "<frozen runpy>", line 198, in _run_module_as_main
05-10 21:44:59   [Verb] File "<frozen runpy>", line 88, in _run_code
05-10 21:44:59   [Verb] File "/home/user/web-apps/study_station/v2/app/bookgen.py", line 654, in <module>
05-10 21:44:59   [Verb] sys.exit(main())
05-10 21:44:59   [Verb] ^^^^^^
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
```
