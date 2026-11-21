# Study Station · किताबों की लाइव स्थिति

**आखिरी अपडेट:** 21-11-2026 08:03 PM IST · **रन शुरू:** 21-11 03:38 PM IST

पेज लगभग हर 15 मिनट और प्रगति सेव होने पर अपडेट होता है। नई स्थिति देखने के लिए पेज रीफ़्रेश करें।
[GitHub Actions पर रन की स्थिति](https://github.com/SCHANDAN996/web-apps/actions/runs/44891035153)

**काम पर लगे workers:** 1/12

## अभी क्या चल रहा है

| Worker | अध्याय | काम | बीता समय |
|---|---|---|---|
| W9 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 54 मिनट |

| API key | इस रन में शुरू हुए अनुरोध |
|---|---:|
| key 3 | 160 |
| key 4 | 142 |
| key 5 | 152 |
| key 6 | 146 |

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
| 10th Hindi | 0 | 15 | 0 | 0 | 0 | 48/540 |
| 12th Computer | 0 | 14 | 0 | 0 | 0 | 52/1092 |
| 10th GK | 0 | 19 | 0 | 0 | 0 | 76/1482 |
| 10th Reasoning | 0 | 22 | 0 | 0 | 0 | 83/1716 |
| 10th Maths | 0 | 22 | 0 | 0 | 0 | 100/1606 |
| 10th English | 0 | 20 | 0 | 0 | 0 | 81/1622 |
| 12th Maths | 0 | 23 | 0 | 0 | 0 | 104/1794 |
| 12th GK | 0 | 24 | 0 | 0 | 0 | 96/1872 |
| 12th Reasoning | 0 | 25 | 0 | 0 | 0 | 101/1950 |
| 12th English | 0 | 25 | 0 | 0 | 0 | 96/2025 |
| Graduation Maths | 0 | 28 | 0 | 0 | 0 | 75/2184 |
| Graduation GK | 0 | 28 | 0 | 0 | 0 | 38/2184 |
| Graduation Reasoning | 0 | 30 | 0 | 0 | 0 | 0/2340 |
| Graduation English | 0 | 30 | 0 | 0 | 0 | 0/2430 |
| **कुल** | 0 | 325 | 0 | 0 | 0 | 950/24837 |

## ✅ autopilot से हाल में पूरे हुए

- अभी कोई नहीं

## ⚠️ अटके अध्याय (दोबारा कोशिश होगी / मैं जाँचूँगा)

- Chapter 16 rikt sthan vakya kram (Hindi) — 3 बार
- Chapter 07 sandhi (Hindi) — 1 बार

<details>
<summary>हाल की तकनीकी गतिविधि</summary>

````text
21-11 19:44:20 QA Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_11_Chemistry: {'status': 'pending', 'verified': False, 'total': 78, 'passed': 2, 'pending': 74, 'blocked': 1, 'needs_reference': 1, 'remaining': 76, 'failures': [{'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}, {'check': 'editorial:Content_hi.txt', 'status': 'blocked', 'issues': ['- Proton discovery attributed to Goldstein in the fundamental particles table → Proton discovered by Ernest Rutherford (1919); Goldstein discovered anode rays (1886)']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_11_Chemistry/QA.json'}
21-11 19:44:33   [Awards] QA blocked: editorial:Content_hi.txt
21-11 19:44:33   [Awards] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 78, "passed": 2, "pending": 74, "blocked": 1, "needs_reference": 1, "remaining": 76, 
21-11 19:44:33 QA Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_13_Awards: {'status': 'pending', 'verified': False, 'total': 78, 'passed': 2, 'pending': 74, 'blocked': 1, 'needs_reference': 1, 'remaining': 76, 'failures': [{'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}, {'check': 'editorial:Content_hi.txt', 'status': 'blocked', 'issues': ["- 'पदक: सफेद सुनहरे रंग का पीपल-पत्ता आकार' (भारत रत्न पदक का वर्णन) → पदक कांस्य (bronze) का बना होता है जिस पर प्लैटिनम का सूर्य चिह्न होता है; रिबन सफेद होती है।"]}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_13_Awards/QA.json'}
21-11 19:44:53 worker 6: nothing left
21-11 19:45:18   [Culture_Art] QA passed: editorial:Content_hi.txt
21-11 19:45:18   [Culture_Art] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 78, "passed": 2, "pending": 74, "blocked": 1, "needs_reference": 1, "remaining": 76, 
21-11 19:45:18 QA Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_17_Culture_Art: {'status': 'pending', 'verified': False, 'total': 78, 'passed': 2, 'pending': 74, 'blocked': 1, 'needs_reference': 1, 'remaining': 76, 'failures': [{'check': 'editorial:Content_en.txt', 'status': 'blocked', 'issues': ['- Hook paragraph says Jana Gana Mana was sung at the 1911 Delhi Durbar → The song was first sung at the Calcutta Session of the Indian National Congress on 27 December 1911, not at the Delhi Durbar.', "- Ajanta Caves technique described as 'fresco/tempera' → The paintings use tempera (fresco-secco) technique, not true fresco.", "- Folk Theatre table claims 'Ramlila of Varanasi region is UNESCO-listed' → UNESCO inscribed 'Ramlila, the traditional performance of the Ramayana' as a tradition in 2008, not specifically the Varanasi region's Ramlila."]}, {'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_17_Culture_Art/QA.json'}
21-11 19:45:33 worker 10: nothing left
21-11 19:45:37   [Days_Dates] QA passed: editorial:Content_hi.txt
21-11 19:45:37   [Days_Dates] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 78, "passed": 3, "pending": 74, "blocked": 0, "needs_reference": 1, "remaining": 75, 
21-11 19:45:38 QA Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_15_Days_Dates: {'status': 'pending', 'verified': False, 'total': 78, 'passed': 3, 'pending': 74, 'blocked': 0, 'needs_reference': 1, 'remaining': 75, 'failures': [{'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_15_Days_Dates/QA.json'}
21-11 19:46:07   [Science_Tech] QA passed: editorial:Content_en.txt
21-11 19:46:08   [Science_Tech] QA needs_reference: sources:Content_en.txt
21-11 19:46:14 worker 1: nothing left
21-11 19:46:33   [Biology] QA passed: editorial:Content_en.txt
21-11 19:46:33   [Biology] QA needs_reference: sources:Content_en.txt
21-11 19:46:52   [Physics_Daily] QA passed: editorial:Content_en.txt
21-11 19:46:53   [Physics_Daily] QA needs_reference: sources:Content_en.txt
21-11 19:46:54 worker 5: nothing left
21-11 19:47:35 worker 4: nothing left
21-11 19:48:23   [Biology] QA blocked: editorial:Content_hi.txt
21-11 19:48:23   [Biology] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 78, "passed": 2, "pending": 74, "blocked": 1, "needs_reference": 1, "remaining": 76, 
21-11 19:48:23 QA Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_12_Biology: {'status': 'pending', 'verified': False, 'total': 78, 'passed': 2, 'pending': 74, 'blocked': 1, 'needs_reference': 1, 'remaining': 76, 'failures': [{'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}, {'check': 'editorial:Content_hi.txt', 'status': 'blocked', 'issues': ['- प्लेटलेटलेट्स (Platelets) → प्लेटलेट्स (Platelets)']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_12_Biology/QA.json'}
21-11 19:49:03 worker 3: nothing left
21-11 19:50:00   [rikt_sthan_vakya_kram] Practice_hi_Set_06.txt try 3: re-solve disagrees (Q131 key b vs re-solve a, Q132 key d vs re-solve b, Q146 key b vs re-solve c, Q150 key d vs re-solve
21-11 19:50:10   [Science_Tech] QA blocked: editorial:Content_hi.txt
21-11 19:50:11   [Science_Tech] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 78, "passed": 2, "pending": 74, "blocked": 1, "needs_reference": 1, "remaining": 76, 
21-11 19:50:11 QA Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_18_Science_Tech: {'status': 'pending', 'verified': False, 'total': 78, 'passed': 2, 'pending': 74, 'blocked': 1, 'needs_reference': 1, 'remaining': 76, 'failures': [{'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}, {'check': 'editorial:Content_hi.txt', 'status': 'blocked', 'issues': ['- खंड 4 (जैव प्रौद्योगिकी) में DNA संरचना का विवरण: "वॉटसन और क्रिक (1953, फ्रांसिस क्रिक के साथ रोजालिंड फ्रैंकलिन के X-ray डेटा का योगदान भी महत्वपूर्ण था)" → फ्रांसिस क्रिक स्वयं \'वॉटसन और क्रिक\' जोड़ी के सदस्य हैं, अलग नहीं; सही: "जेम्स वॉटसन और फ्रांसिस क्रिक ने 1953 में रोजालिंड फ्रैंकलिन के X-ray डेटा की मदद से डबल हेलिक्स संरचना प्रस्तावित की"']}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_18_Science_Tech/QA.json'}
21-11 19:50:50   [Physics_Daily] QA blocked: editorial:Content_hi.txt
21-11 19:50:50   [Physics_Daily] BOOK_QA_RESULT={"status": "pending", "verified": false, "total": 78, "passed": 2, "pending": 74, "blocked": 1, "needs_reference": 1, "remaining": 76, 
21-11 19:50:50 worker 0: nothing left
21-11 19:50:50 QA Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_10_Physics_Daily: {'status': 'pending', 'verified': False, 'total': 78, 'passed': 2, 'pending': 74, 'blocked': 1, 'needs_reference': 1, 'remaining': 76, 'failures': [{'check': 'sources:Content_en.txt', 'status': 'needs_reference', 'issues': ['Fetch official supporting evidence for: [file content]']}, {'check': 'editorial:Content_hi.txt', 'status': 'blocked', 'issues': ["- 'सर्पी घर्षण' is an incorrect Hindi term for sliding friction; the correct term is 'सरकन घर्षण' (or 'खिसकाव घर्षण') → replace 'सर्पी घर्षण' with 'सरकन घर्षण'"]}], 'ledger': '/home/runner/work/web-apps/web-apps/study_station/books/Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_10_Physics_Daily/QA.json'}
21-11 19:51:30 worker 9: nothing left
21-11 19:57:40   [sandhi] Practice_hi_Set_01.txt try 3: re-solve disagrees (Q2 key c vs re-solve a, Q9 key d vs re-solve a, Q10 key b vs re-solve a, Q16 key b vs re-solve d, Q1
21-11 19:59:58   [rikt_sthan_vakya_kram] Practice_hi_Set_06.txt try 4: re-solve disagrees (Q130 key d vs re-solve b, Q137 key d vs re-solve b, Q139 key d vs re-solve c)
21-11 19:59:58   [rikt_sthan_vakya_kram] REJECTED Practice_hi_Set_06.txt: no version passed the checks — not written
21-11 19:59:58   [rikt_sthan_vakya_kram] written 0, failed 2; AI calls today 598/100000
21-11 19:59:58 NOT OK 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_16_rikt_sthan_vakya_kram after 80 min: todo ['Set 04 hi: todo', 'Set 06 hi: todo'] problems []
21-11 19:59:58 worker 7: nothing left
````

</details>
