# 📚 Study Station किताबें — नियम (BOOK_RULES)

ये नियम **हर prompt से ऊपर** हैं। `Prompts/` की कोई file अगर इनसे टकराए (जैसे "पिछले 10 वर्षों की वर्ष-वार
आवृत्ति तालिका" या "source (exam name/year)"), तो यही नियम मानें। Agent (`ss-book-writer`) और API generator
(`v2/app/bookgen.py`) दोनों इसे पढ़ते हैं। जाँच: `cd v2 && python -m app.bookcheck <chapter या book>`।

## 1. ढाँचा (structure)

```
books/<Level>/<Subject>/[<Book>_WorldClass/]Chapter_NN_Name/
    chapter.json          ← metadata (नीचे)
    Content_hi.txt  Content_en.txt  …   ← तैयार किताब (यही app में दिखता है)
    Practice_hi_Set_01.txt … Practice_en_Set_06.txt
    Prompts/              ← सिर्फ़ prompts (spec) — इनमें content कभी न लिखें
```

- तैयार content **chapter root** में; `Prompts/` कभी overwrite नहीं होता।
- `books/` ही एकमात्र source है। `study_station/10th_Level|12th_Level|Graduation_Level` वाली पुरानी copies हटा दी गईं।
- `chapter.json`:
  ```json
  {"title_hi": "राज्य एवं नदियाँ", "title_en": "States & Rivers", "topic": "ga/indian-geography",
   "type": "static", "status": "draft", "as_of": null, "notes": ""}
  ```
  `type`: `static` | `dynamic` (करंट अफेयर्स — किताब में नहीं लिखा जाता, app `/current-affairs` दिखाता है)।
  `status`: `draft` (AI-लिखित, app में "समीक्षा बाकी" badge) → `reviewed` (ss-content-reviewer या इंसान की जाँच के बाद)।
  `as_of`: जिन अध्यायों में साल-दर-साल बदलने वाले तथ्य हैं (पुरस्कार, खेल, योजनाएँ, रिपोर्ट/सूचकांक, बजट, रक्षा) उनमें
  वह साल जहाँ तक तथ्य जाँचे गए — हर साल दोबारा जाँचें।

## 2. पाठक कौन है (level के अनुसार भाषा और गहराई)

| Level | परीक्षाएँ | ध्यान |
|---|---|---|
| 10th (Foundation) | SSC GD, SSC MTS, RRB Group D, राज्य पुलिस/कांस्टेबल | NCERT 6–10 स्तर, आसान भाषा, ज़्यादा उदाहरण |
| 12th (Intermediate) | SSC CHSL, RRB NTPC, SSC CGL Tier-1 की नींव | NCERT 6–12, थोड़ा गहरा |
| Graduation (Advanced) | SSC CGL, IBPS PO/Clerk, राज्य PCS prelims | विश्लेषण, कथन-आधारित प्रश्न |

10th की किताब में UPSC का हवाला न दें।

## 3. तथ्य (सबसे ज़रूरी)

- सिर्फ़ जाँचे जा सकने वाले स्थिर तथ्य — NCERT, सरकारी (`*.gov.in`, `*.nic.in`) या संस्थान की official site।
- शक हो तो official/NCERT source पर जाँचें, वरना तथ्य छोड़ दें। गढ़े हुए आँकड़े, प्रतिशत, गिनती, रैंक **कभी नहीं**।
- समय के साथ बदलने वाले तथ्य साल के साथ: "2024 में …"; "वर्तमान …" बिना तारीख़ के नहीं।

## 4. PYQ — कोई गढ़ा हुआ दावा नहीं

- PYQ section = **pattern analysis**: परीक्षाएँ इस अध्याय से किस तरह के सवाल पूछती हैं, कौन से उप-विषय बार-बार आते हैं,
  परीक्षक के जाल (लगभग-सही कथन, कालक्रम भ्रम, मिलते-जुलते नाम, नकारात्मक वाक्य) — **शब्दों में**, संख्याओं में नहीं।
- वर्ष-वार आवृत्ति तालिका, "भार %", "पिछले 10 साल में N प्रश्न" — **मना है** (हमारे पास ऐसा data नहीं है)।
- किसी प्रश्न पर `Source: SSC CGL 2019 (Tier-I, 05.03.2020 Shift 1)` तभी जब official question paper/answer key में मिला
  हो; वरना `Source: NCERT Class 9 Geography` (जिस किताब से concept है) या `Source: PYQ-style`।
- "15/45 सेकंड नियम" जैसे समय-सुझाव ठीक हैं — वे सलाह हैं, आँकड़ा नहीं।

## 5. हिंदी + English

- हर section दोनों भाषाओं में; English शब्द हिंदी में ज़रूरत पर कोष्ठक में।
- Practice Set N: पहले एक भाषा में लिखें, फिर **उन्हीं 25 प्रश्नों** का अनुवाद — वही क्रम, वही विकल्प-क्रम, वही उत्तर-अक्षर।

## 6. Practice sets का format (importer और bookcheck इसी को पढ़ते हैं)

```
प्रश्न 1–20: आसान | प्रश्न 21–25: मध्यम

51. प्रश्न का पाठ (कथन अलग-अलग पंक्तियों में ठीक हैं)
(a) विकल्प (b) विकल्प (c) विकल्प (d) विकल्प
उत्तर: (c)
हल: 1–3 वाक्य — (c) क्यों सही, और लुभाने वाला गलत विकल्प क्यों गलत।
स्रोत: NCERT कक्षा 10 भूगोल
```
English: `Answer:` `Solution:` `Source:`। Set N के प्रश्न (N−1)×25+1 … N×25। ठीक 4 विकल्प, ठीक 1 सही;
"उपरोक्त सभी/कोई नहीं" नहीं। हर प्रश्न अपने-आप में पूरा (किसी दूसरे प्रश्न का हवाला नहीं)। हर उत्तर दोबारा जाँचा हुआ।

## 7. बाकी sections

- **Mind Map**: सिर्फ़ एक ```` ```mermaid ```` block, `graph TD`, labels quotes में, `<br>` से नई पंक्ति। Rendered copy नहीं।
- **Flashcards**: `कार्ड N` / `सामने:` / `पीछे:` (English: `Card N` / `Front:` / `Back:`), 15–20 कार्ड।
- कोई chat-कचरा नहीं: "Here is…", "Sure!", "text / Copy / Download / Diagram", prompt के बारे में टिप्पणी।

## 8. Publish होने की शर्त

अध्याय app में तभी दिखता है जब `bookcheck` उसे `OK` कहे। AI-लिखा अध्याय `status: draft` रहता है जब तक जाँच न हो।
