# मॉक तैयारी की जाँच — 3 नवंबर 2026

Live server के question bank पर नए read-only `app.mock_audit` से जाँच की गई। पढ़ाई या learner records नहीं बदले गए। नीचे की स्थिति केवल वर्तमान catalog के लिए प्रश्न संख्या की पर्याप्तता है; नवीनतम आधिकारिक notification या syllabus की स्वीकृति नहीं।

| परीक्षा | ऑनलाइन विषयवार गिनती | उसी level पर गिनती | अतिरिक्त engine कमी |
|---|---|---|---|
| SSC GD | पर्याप्त | पर्याप्त | हिंदी भाषा का अलग section नहीं |
| SSC MTS | पर्याप्त | पर्याप्त | अलग sessions के timers नहीं |
| RRB Group D | पर्याप्त | पर्याप्त | साझा कमियाँ नीचे |
| SSC CHSL | पर्याप्त | पर्याप्त | साझा कमियाँ नीचे |
| RRB NTPC | पर्याप्त | पर्याप्त | साझा कमियाँ नीचे |
| SSC CGL | पर्याप्त | पर्याप्त | साझा कमियाँ नीचे |
| IBPS Clerk | पर्याप्त | पर्याप्त | sectional timer नहीं |
| IBPS PO | पर्याप्त | पर्याप्त | sectional timer नहीं |

## साझा कमियाँ और अगला क्रम

1. Online selection पूरे subject से होती है; APK exact exam level भी लगाता है। Exact-level pool में संख्या अभी पर्याप्त मिली, पर online/offline selection नीति समान करना बाकी है। Difficulty को exam suitability का पर्याप्त प्रमाण न मानें।
2. Online attempts के marking rules exam catalog से पढ़े जाते हैं। पुराने attempt के लिए rules और pattern version freeze करने होंगे; वर्तमान attempts सुरक्षित migrate हों।
3. Topic quotas, linked passages/DI/puzzles और language-specific पर्याप्तता को वास्तविक exam coverage से जोड़ना बाकी है। Audit में language, level, topic, difficulty और review status की गिनती मिलती है।
4. हर परीक्षा के लिए मूल official notification URL/year/check date और versioned pattern जाँचना बाकी है। पुराने global checked-month को नई आधिकारिक पुष्टि नहीं माना गया।
5. उसके बाद bank section timing और MTS sessions लागू करें; फिर नई परीक्षाएँ जोड़ें।

## इस चरण में लागू सुधार

- साझा online/offline exam search और SSC/RRB/IBPS filter; filtering पर नई question requests नहीं।
- अपने अधूरे, समय बचे mock का resume link। दूसरे learner का attempt नहीं दिखता।
- Online छोटे अभ्यास के card/detail में वही वास्तविक सवाल, समय और maximum marks जो start करते समय मिलेंगे। पूरा प्रश्न सेट और छोटा अभ्यास अलग labels।
- कठिन नियमों वाले presets पर timer/session सीमाएँ स्पष्ट। पूरे pattern के समान होने वाला पुराना blanket दावा हटाया।
- Offline English section में English text के बिना सवाल नहीं चुने जाएँगे।

## चलाना

`python -m app.mock_audit` — आठ exams की संक्षिप्त matrix।

`python -m app.mock_audit --json` — sections और topic/level/language/difficulty/review-status breakdown।

यह CLI schema/seed/cleanup नहीं चलाता; database केवल पढ़ता है। नया APK/Play bundle अलग build और device QA के बाद जाएगा।
