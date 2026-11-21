# Study Station · किताबों की लाइव स्थिति

**आखिरी अपडेट:** 21-11-2026 03:40 PM IST · **रन शुरू:** 21-11 03:38 PM IST

पेज लगभग हर 15 मिनट और प्रगति सेव होने पर अपडेट होता है। नई स्थिति देखने के लिए पेज रीफ़्रेश करें।
[GitHub Actions पर रन की स्थिति](https://github.com/SCHANDAN996/web-apps/actions/runs/44891035153)

**काम पर लगे workers:** 3/12

## अभी क्या चल रहा है

| Worker | अध्याय | काम | बीता समय |
|---|---|---|---|
| W1 | Chapter 07 sandhi (10th Hindi) | ✍️ लिख रहा है | 1 मिनट |
| W2 | Chapter 16 rikt sthan vakya kram (10th Hindi) | ✍️ लिख रहा है | 1 मिनट |
| W3 | Chapter 01 varn vartani (10th Hindi) | 🧮 उत्तर दोबारा जाँच रहा है | -1 मिनट |

| API key | इस रन में शुरू हुए अनुरोध |
|---|---:|
| key 3 | 1 |
| key 4 | 1 |
| key 5 | 1 |
| key 6 | 1 |

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

- अभी कोई नहीं

<details>
<summary>हाल की तकनीकी गतिविधि</summary>

````text
21-11 15:38:34 autopilot start: 12 workers, reverse=False
21-11 15:38:34 API policy: account start interval=20s; key start interval=15s; in-flight per key=1
21-11 15:38:35 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_07_sandhi (TODO: todo 5, problems 0)
21-11 15:38:36   [sandhi] Hindi-only writer: direct Hindi content; English generation and translation disabled
21-11 15:38:41 START 10th_Level/Hindi/Foundation_10th_Hindi_WorldClass/Chapter_16_rikt_sthan_vakya_kram (TODO: todo 2, problems 0)
21-11 15:38:41   [rikt_sthan_vakya_kram] Hindi-only writer: direct Hindi content; English generation and translation disabled
21-11 15:40:22   [sandhi] Practice_hi_Set_01.txt try 1: rejected (Q6:duplicate_options,Q20:duplicate_options)
21-11 15:40:49   [input_output_ports] QA needs_reference: sources:Content_hi.txt
21-11 15:40:48   [varn_vartani] QA needs_reference: sources:Feynman_hi.txt
21-11 15:40:50   [ling_vachan_karak] QA needs_reference: sources:Feynman_hi.txt
21-11 15:40:50   [shabd_bhed] QA needs_reference: sources:Feynman_hi.txt
21-11 15:40:50   [organization_cpu] QA needs_reference: sources:Content_hi.txt
21-11 15:40:50   [sangya_sarvanam] QA needs_reference: sources:Feynman_hi.txt
21-11 15:40:50   [visheshan_kriya] QA needs_reference: sources:Feynman_hi.txt
21-11 15:40:50   [windows_files] QA needs_reference: sources:Content_hi.txt
21-11 15:40:50   [software_os] QA needs_reference: sources:Content_hi.txt
21-11 15:40:50   [memory_storage_backup] QA needs_reference: sources:Content_hi.txt
21-11 15:41:15   [memory_storage_backup] QA passed: editorial:Feynman_en.txt
21-11 15:41:15   [memory_storage_backup] QA needs_reference: sources:Feynman_en.txt
````

</details>
