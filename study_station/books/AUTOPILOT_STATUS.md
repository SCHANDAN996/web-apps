# Study Station · किताबों की लाइव स्थिति

**आखिरी अपडेट:** 21-11-2026 03:36 PM IST · **रन शुरू:** 21-11 10:51 AM IST

पेज लगभग हर 15 मिनट और प्रगति सेव होने पर अपडेट होता है। नई स्थिति देखने के लिए पेज रीफ़्रेश करें।
[GitHub Actions पर रन की स्थिति](https://github.com/SCHANDAN996/web-apps/actions/runs/44865217555)

**काम पर लगे workers:** 0/12

## अभी क्या चल रहा है

इस अपडेट के समय कोई अध्याय worker को सौंपा नहीं था।

| API key | इस रन में शुरू हुए अनुरोध |
|---|---:|
| key 3 | 126 |
| key 4 | 126 |
| key 5 | 145 |
| key 6 | 109 |

## किताबों की प्रगति

लेखन की प्रारंभिक जाँच और गहरी QA के आँकड़े नीचे अलग दिए गए हैं।

| किताब | कुल अध्याय | संरचना पास | सुधार बाकी | लेखन बाकी |
|---|---:|---:|---:|---:|
| 10th Hindi | 17 | 15 | 0 | 2 |
| 12th Computer | 14 | 14 | 0 | 0 |
| 10th GK | 19 | 19 | 0 | 0 |
| 10th Reasoning | 22 | 22 | 0 | 0 |
| 10th Maths | 22 | 22 | 0 | 0 |
| 10th English | 20 | 20 | 0 | 0 |
| 12th Maths | 23 | 23 | 0 | 0 |
| 12th GK | 24 | 24 | 0 | 0 |
| 12th Reasoning | 25 | 25 | 0 | 0 |
| 12th English | 25 | 25 | 0 | 0 |
| Graduation Maths | 28 | 28 | 0 | 0 |
| Graduation GK | 28 | 28 | 0 | 0 |
| Graduation Reasoning | 30 | 30 | 0 | 0 |
| Graduation English | 30 | 30 | 0 | 0 |
| **कुल** | **327** | **325** | **0** | **2** |

## संरचना पास अध्यायों की गहरी QA

प्रमाण और सुधार वाले कॉलम उस अध्याय की वर्तमान QA स्थिति दिखाते हैं। मानवीय प्रकाशन मंजूरी अलग है।

| किताब | QA पास | जाँच बाकी | प्रमाण बाकी | सुधार अटका | मैनुअल | जाँचें पास / कुल |
|---|---:|---:|---:|---:|---:|---:|
| 10th Hindi | 0 | 15 | 0 | 0 | 0 | 31/540 |
| 12th Computer | 0 | 14 | 0 | 0 | 0 | 29/1092 |
| 10th GK | 0 | 19 | 0 | 0 | 0 | 43/1482 |
| 10th Reasoning | 0 | 22 | 0 | 0 | 0 | 49/1716 |
| 10th Maths | 0 | 22 | 0 | 0 | 0 | 62/1606 |
| 10th English | 0 | 20 | 0 | 0 | 0 | 51/1622 |
| 12th Maths | 0 | 23 | 0 | 0 | 0 | 62/1794 |
| 12th GK | 0 | 24 | 0 | 0 | 0 | 55/1872 |
| 12th Reasoning | 0 | 25 | 0 | 0 | 0 | 58/1950 |
| 12th English | 0 | 25 | 0 | 0 | 0 | 50/2025 |
| Graduation Maths | 0 | 28 | 0 | 0 | 0 | 0/2184 |
| Graduation GK | 0 | 28 | 0 | 0 | 0 | 0/2184 |
| Graduation Reasoning | 0 | 30 | 0 | 0 | 0 | 0/2340 |
| Graduation English | 0 | 30 | 0 | 0 | 0 | 0/2430 |
| **कुल** | 0 | 325 | 0 | 0 | 0 | 490/24837 |

## ✅ autopilot से हाल में पूरे हुए

- 21-11 11:05 — 10th Hindi · Chapter 15 vakya shuddhi

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 16 rikt sthan vakya kram (Hindi) — 3 बार
- Chapter 07 sandhi (Hindi) — 1 बार

<details>
<summary>हाल की तकनीकी गतिविधि</summary>

````text
21-11 14:49:14   [Error_Spotting_Adv] QA blocked: editorial:Content_hi.txt
21-11 14:49:14   [Error_Spotting_Adv] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 81, "passed": 2, "pending": 77, "blocked": 1, "needs_reference": 1, "remaining": 79, 
21-11 14:49:15 QA 12th_Level/English/Intermediate_12th_English_WorldClass/Chapter_18_Error_Spotting_Adv: {'status': 'pending', 'verified': False, 'total': 81, 'passed': 2, 'pending': 77, 'blocked': 1, 'needs_reference': 1, 'remaining': 79, 'failures': [{'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}, {'check': 'editorial:Content_hi.txt', 'status': 'blocked', 'issues': ['- नियम 1 में "Each/Every/One of + बहुवचन संज्ञा + एकवचन क्रिया" गलत है क्योंकि \'Every\' के साथ \'of + बहुवचन संज्ञा\' नहीं आता (जैसे "Every of the boys" असंगत है) → सही नियम: "Each of/One of/Every one of + बहुवचन संज्ञा + एकवचन क्रिया" या "Each/Every/Either/Neither + एकवचन संज्ञा + एकवचन क्रिया"।']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/12th_Level/English/Intermediate_12th_English_WorldClass/Chapter_18_Error_Spotting_Adv/QA.json'}
21-11 14:50:37   [Sentence_Improvement_Adv] QA passed: editorial:Content_hi.txt
21-11 14:50:54   [Sentence_Improvement_Adv] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 81, "passed": 3, "pending": 77, "blocked": 0, "needs_reference": 1, "remaining": 78, 
21-11 14:50:55 QA 12th_Level/English/Intermediate_12th_English_WorldClass/Chapter_20_Sentence_Improvement_Adv: {'status': 'pending', 'verified': False, 'total': 81, 'passed': 3, 'pending': 77, 'blocked': 0, 'needs_reference': 1, 'remaining': 78, 'failures': [{'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: "Since" + point of time (Monday, 2010, childhood); "for" + period of time (two years, a long time).']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/12th_Level/English/Intermediate_12th_English_WorldClass/Chapter_20_Sentence_Improvement_Adv/QA.json'}
21-11 14:50:56   [Para_Jumbles] QA passed: structure
21-11 14:51:37 worker 11: nothing left
21-11 14:51:41   [Cloze_Test] QA blocked: editorial:Content_en.txt
21-11 14:51:41   [Cloze_Test] QA needs_reference: sources:Content_en.txt
21-11 14:51:47   [Para_Jumbles] QA blocked: editorial:Content_en.txt
21-11 14:51:48   [Para_Jumbles] QA needs_reference: sources:Content_en.txt
21-11 14:52:05   [Cloze_Test] QA passed: editorial:Content_hi.txt
21-11 14:52:05   [Cloze_Test] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 81, "passed": 2, "pending": 77, "blocked": 1, "needs_reference": 1, "remaining": 79, 
21-11 14:52:06 QA 12th_Level/English/Intermediate_12th_English_WorldClass/Chapter_21_Cloze_Test: {'status': 'pending', 'verified': False, 'total': 81, 'passed': 2, 'pending': 77, 'blocked': 1, 'needs_reference': 1, 'remaining': 79, 'failures': [{'check': 'editorial:Content_en.txt', 'status': 'blocked', 'issues': ["- Worked example claims all four options pass grammar layer, but verb complementation rules eliminate prevent, forbid, block → Grammar layer must check complementation; only enable fits 'will ______ small businesses to grow.'"]}, {'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/12th_Level/English/Intermediate_12th_English_WorldClass/Chapter_21_Cloze_Test/QA.json'}
21-11 14:52:26 worker 3: nothing left
21-11 14:52:27   [Para_Jumbles] QA passed: editorial:Content_hi.txt
21-11 14:52:27   [Para_Jumbles] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 81, "passed": 2, "pending": 77, "blocked": 1, "needs_reference": 1, "remaining": 79, 
21-11 14:52:27 QA 12th_Level/English/Intermediate_12th_English_WorldClass/Chapter_22_Para_Jumbles: {'status': 'pending', 'verified': False, 'total': 81, 'passed': 2, 'pending': 77, 'blocked': 1, 'needs_reference': 1, 'remaining': 79, 'failures': [{'check': 'editorial:Content_en.txt', 'status': 'blocked', 'issues': ['- "Kerala\'s literacy campaign began in 1990 in Ernakulam district" (in Trap 1 example) → "Kerala\'s literacy campaign began in 1989 in Ernakulam district (declared fully literate in 1990)"']}, {'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/12th_Level/English/Intermediate_12th_English_WorldClass/Chapter_22_Para_Jumbles/QA.json'}
21-11 14:53:16 worker 9: nothing left
21-11 14:54:05 worker 1: nothing left
21-11 14:54:54 worker 10: nothing left
21-11 14:54:58   [rikt_sthan_vakya_kram] Practice_hi_Set_04.txt try 2: re-solve disagrees (Q84 key d vs re-solve a, Q88 key b vs re-solve a)
21-11 14:55:44 worker 6: nothing left
21-11 14:56:33 worker 5: nothing left
21-11 14:57:22 worker 2: nothing left
21-11 14:58:11 worker 8: nothing left
21-11 14:59:01 worker 4: nothing left
21-11 14:59:50 worker 7: nothing left
21-11 15:01:24   [rikt_sthan_vakya_kram] Practice_hi_Set_04.txt try 3: re-solve disagrees (Q83 key c vs re-solve b, Q88 key c vs re-solve a, Q94 key d vs re-solve b)
21-11 15:05:08   [rikt_sthan_vakya_kram] Practice_hi_Set_04.txt try 4: re-solve disagrees (Q80 key a vs re-solve d, Q83 key a vs re-solve c, Q88 key a vs re-solve d)
21-11 15:05:08   [rikt_sthan_vakya_kram] REJECTED Practice_hi_Set_04.txt: no version passed the checks — not written
21-11 15:06:19   [rikt_sthan_vakya_kram] Practice_hi_Set_06.txt try 1: rejected (Q128:duplicate_options,Q132:duplicate_options,Q138:duplicate_options,Q142:duplicate_options)
21-11 15:16:45   [rikt_sthan_vakya_kram] Practice_hi_Set_06.txt try 2: re-solve disagrees (Q132 key a vs re-solve d, Q141 key b vs re-solve a)
21-11 15:21:23   [rikt_sthan_vakya_kram] Practice_hi_Set_06.txt try 3: re-solve disagrees (Q134 key d vs re-solve c, Q140 key a vs re-solve c)
21-11 15:28:14   [rikt_sthan_vakya_kram] Practice_hi_Set_06.txt try 4: re-solve disagrees (Q132 key d vs re-solve a, Q134 key b vs re-solve c, Q140 key a vs re-solve c, Q143 key b vs re-solve
21-11 15:28:14   [rikt_sthan_vakya_kram] REJECTED Practice_hi_Set_06.txt: no version passed the checks — not written
21-11 15:28:14   [rikt_sthan_vakya_kram] written 0, failed 2; AI calls today 501/100000
21-11 15:28:14 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_16_rikt_sthan_vakya_kram after 49 min: todo ['Set 04 hi: todo', 'Set 06 hi: todo'] problems []
21-11 15:28:14 worker 0: nothing left
````

</details>
