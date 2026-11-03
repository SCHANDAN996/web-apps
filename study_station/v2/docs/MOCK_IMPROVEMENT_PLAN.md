# मॉक टेस्ट सुधार और विस्तार योजना

तैयार: 2 नवंबर 2026। स्थिति: प्रस्ताव; implementation और नई परीक्षा के आधिकारिक पैटर्न का सत्यापन बाकी है।

## मौजूदा स्थिति — कोड से मिले तथ्य

- `app/catalog.py` में आठ परीक्षा presets हैं: SSC GD, MTS, CHSL, CGL; RRB Group D, NTPC; IBPS Clerk, PO। यह सूची वर्तमान आधिकारिक pattern की पुष्टि नहीं है।
- उपलब्धता अभी मुख्यतः subject की प्रश्न संख्या से तय होती है। पर्याप्त संख्या होना परीक्षा के syllabus, स्तर और भाषा के पर्याप्त coverage का प्रमाण नहीं है।
- `services.start_mock` कम प्रश्न वाले sections छोड़कर अनुपात में समय घटाता है और attempt को Partial कहता है। इसे स्पष्ट अलग अभ्यास mode बनाना है।
- बैंकिंग के section समय और MTS के sessions catalog notes में लिखे हैं; मौजूदा player मुख्यतः पूरे attempt का timer और freely selectable section tabs देता है।
- सभी परीक्षाओं की उपलब्धता के लिए साझा aggregate/cache और bounded-query performance tests पहले से हैं; इन्हें बनाए रखना है।
- ऑनलाइन और APK के offline mock रास्ते दोनों मौजूद हैं। नई सुविधा दोनों पर एक जैसी होनी चाहिए।

## प्राथमिकता और चरण

### 1. भरोसेमंद टेस्ट और डेटा audit

- परीक्षा × stage × विषय × topic × भाषा × difficulty की coverage report तैयार करें। Reviewed, flagged, translated और repeat सवाल अलग गिनें।
- हर परीक्षा के pattern के साथ मूल official notification URL, notification year, checked date और immutable version रखें। पुराने global checked-month को पर्याप्त प्रमाण न मानें।
- Full Mock तभी उपलब्ध हो जब सभी अनिवार्य sections, प्रश्न प्रकार और लागू भाषा में पूरा paper बन सके। अधूरे paper को अलग Section Practice/Short Practice कहें; असली परीक्षा वाला दावा न करें।
- गलत परीक्षा में unrelated सवाल चुनने से बचाने के लिए exam/syllabus tags और topic quotas जोड़ें। Passage, DI और puzzle के linked questions को एक साथ चुनें।

### 2. Home से मेल खाती सरल screens

- क्रम: चुनी परीक्षा → अधूरा टेस्ट जारी रखें → Full Mock, Section Test, Topic Test, Custom Practice।
- परीक्षा खोज, category filter और favourite exam दें। मोबाइल में जगह के अनुसार cards, desktop में responsive grid रखें।
- Card पर परीक्षा/stage, प्रश्न, समय, उपलब्धता और एक मुख्य action हो। लंबे नियम भीतर रखें।
- शुरू करने से पहले compact summary: भाषा, समय, marking, लागू section restrictions और official pattern link।
- चयनित भाषा की पर्याप्त सामग्री न हो तो पहले बताएँ; बीच में चुपचाप दूसरी भाषा न दिखाएँ।

### 3. परीक्षा के नियमों वाला साझा engine

- Overall timer, sectional timer, multiple sessions, fixed/free section navigation और भाषा-choice को versioned configuration से चलाएँ। हर परीक्षा के लिए अलग player न बनाएँ।
- Attempt शुरू होते समय प्रश्नों का क्रम, paper version, marks, negative marking और timing/navigation rules freeze करें। बाद में catalog या सवाल बदलने से पुराने attempt का score न बदले।
- Server deadlines, duplicate submit protection, restart recovery और offline answer queue रखें। Offline result provisional रहे जब तक जरूरी validation/sync न हो।
- Study mode में save/share/rough-work; exam mode में समाधान submit के बाद। Rough work प्रश्न या section बदलने पर सुरक्षित रहे।

### 4. उपयोगी result और revision

- Score, accuracy, समय, सही/गलत/छोड़े सवाल और negative marks का छोटा overview।
- Section/topic breakdown; गलत सवाल दोहराएँ, explanation पढ़ें, bookmark करें और कमजोर topic का छोटा अभ्यास शुरू करें।
- अलग pattern/version या अलग difficulty वाले attempts को सीधे बराबर न मानें। पर्याप्त वैध cohort के बिना rank, percentile या selection prediction न दिखाएँ।

### 5. नई परीक्षाएँ जोड़ने का क्रम

- पहले मौजूदा आठ presets के rules और coverage सही करें।
- फिर सवालों के overlap और learner demand के आधार पर SBI तथा अन्य banking stages और SSC/Railway के अतिरिक्त stages की readiness जाँचें।
- राज्य भर्ती, पुलिस और teaching exams तब जोड़ें जब राज्य GK, हिंदी/अन्य भाषा और pedagogy जैसी जरूरी सामग्री उपलब्ध हो।
- हर नई परीक्षा के लिए release gate: official pattern → content mapping → complete paper validation → timing/scoring QA → web/offline parity।

### 6. गति और server लागत

- Exam cards/availability को versioned cache दें; सारे प्रश्न page load पर न भेजें।
- Device पर syllabus और downloadable question packs रखें। Packs में version/checksum हो; update केवल बदला हिस्सा लाए और storage हटाने का विकल्प दे।
- Test start पर आवश्यक payload ही पढ़ें; अगले सवाल local memory से खुलें। Question bank को हर card/section के लिए बार-बार scan न करें।
- शुरुआती performance targets: cached list लगभग एक सेकंड, downloaded paper का start लगभग दो सेकंड; reference phone/network तय करके p50/p95 मापें। ये लक्ष्य हैं, मौजूदा माप नहीं।
- Local packs या offline timer को high-stakes anti-cheating सुरक्षा न कहें; यह preparation app है।

## जाँच और rollout

- Timing/session boundaries, per-section marking, fractional penalties, skipped questions, language sufficiency, linked sets, duplicate IDs, retries और attempt rule freezing के tests।
- Web और APK offline mode में एक ही fixture paper का समान क्रम, समय और score जाँचें।
- Slow network, airplane mode, app close/reopen, expired attempt और sync conflict की जाँच करें।
- Mobile screenshots, Hindi/English layout, 44px actions, keyboard/screen-reader और reduced motion जाँचें।
- Full pytest, affected browser flows और performance checks के बाद छोटे commits; tested revision GitHub/PC/server पर समान रखें। APK अलग build/test से जाए।
- पुराने attempts/history सुरक्षित रखें। पहले एक मौजूदा परीक्षा पर rollout, फिर बाकी exams।

## पहला ठोस deliverable

आठ मौजूदा exams की readiness matrix: official pattern status, missing engine rules, topic/language coverage और Full/Section-only readiness। इसके बाद compact Mock dashboard और स्पष्ट partial-practice flow लागू करें।
