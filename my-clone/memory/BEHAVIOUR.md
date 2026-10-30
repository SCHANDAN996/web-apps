# व्यवहार का विकसित होता नक्शा
अद्यतन: 2026-10-27 · ये वर्णन हैं, मनोवैज्ञानिक निदान या brain-function के वैज्ञानिक निष्कर्ष नहीं।

## स्पष्ट कथन और देखे हुए उदाहरण
| संकेत | उदाहरण / स्रोत | अभी की व्याख्या | भरोसा और सीमा |
|---|---|---|---|
| लिखने और पढ़ने की लिपि अलग हो सकती है | उपयोगकर्ता Roman Hindi में बोलता/लिखता है, पर देवनागरी जवाब चाहता है; वर्तमान चैट | input की लिपि से output की पसंद न निकालें | उच्च; सीधी पुष्टि |
| छोटे संदर्भ आधारित संदेश | “Next”, “Cover”, “Promt”, “Status”; Vidhivat, avatar, comedy chats | assistant से पिछला संदर्भ बनाए रखने की अपेक्षा | मध्यम; कई उपलब्ध उदाहरण, पूरा इतिहास नहीं |
| बीच काम में सुधार जोड़ना | पहले clone structure, फिर chat style, फिर तारीखवार project review; वर्तमान चैट | नए निर्देश अक्सर चालू लक्ष्य को विस्तार देते हैं | उच्च, इस session तक; हर संदेश को नया प्रोजेक्ट न समझें |
| हल्की अस्वीकृति के बाद सुधार स्वीकार हो सकता है | comedy chat: “Nahi thik nahi h”, फिर अंतिम scene का निर्देश और “ab thik…” | यह output की अस्वीकृति थी; पूरा comedy project बंद नहीं | मध्यम; क्रम में उपलब्ध bounded turns |
| साधारण विचार से अलग कुछ चाहता है | Instagram Snake Videos में extraordinary idea का सीधा अनुरोध | उस video concept में novelty की मांग | मध्यम; सभी कामों की स्थायी पसंद घोषित न करें |
| दृश्य के छोटे विवरण सुधारता है | comedy ending में दोनों का हँसते हुए भागना | creative direction में बारीक feedback | मध्यम; एक उपलब्ध episode |
| काम दूसरी chat में जारी रखना | avatar chat का full handover अनुरोध और वर्तमान portable memory | continuity एक स्पष्ट जरूरत है | उच्च |
| सामान्य सवाल में अनावश्यक account access नहीं चाहता | Automation System Feasibility में “generally question”, account खोलने की जरूरत नहीं | सवाल की प्रकृति पहले समझें; हर उत्तर के लिए tools न चलाएँ | उच्च, उस संदर्भ में |
| कमाई कई रास्तों से खोजता है | वर्तमान explicit goal, ऐप/YouTube/Instagram, job chat | आर्थिक परिणाम फिलहाल मुख्य कसौटी | उच्च वर्तमान goal; असीम जोखिम पसंद का अनुमान नहीं |
| रुचि और दृढ़ता हमेशा समान नहीं | अपने क्षणिक विचार और जमकर लगने का self-report | विचार, commitment और action अलग track करें | उच्च self-report; कारण अज्ञात |

## बोलने/लिखने की शैली को कैसे पढ़ें
- Roman Hindi, हिंदी और English product शब्द साथ आ सकते हैं। विरामचिह्न कम या वाक्य लंबे हो सकते हैं। voice transcription संभव है, पर बिना पुष्टि इसे निश्चित न लिखें।
- “guitar” जैसे शब्द का आशय संदर्भ में GitHub हो सकता है। परिणामकारी अस्पष्टता पर स्पष्ट करें; गलत spelling को व्यक्तित्व का गुण न मानें।
- “हाँ”, “करो”, “next” का अर्थ उसी वक्त के प्रस्ताव से निकालें। उसे नए खर्च/प्रकाशन की स्थायी सहमति न बनाएँ।
- निराशा, थकान, ध्यान की बीमारी, impulsivity या अन्य clinical labels भाषा के आधार पर न लिखें।

## सीखने के लिए अलग-अलग प्रश्न
क्या व्यक्ति विचार reject कर रहा है या उस output की quality? क्या लक्ष्य बदला, या तरीका? क्या वापस लौटने का प्रमाण है? क्या रुकावट account/login, लागत, समय, तकनीक, गुणवत्ता या रुचि थी? यदि कारण नहीं बताया, unknown लिखें।

## अभी परीक्षण योग्य अनुमान
H01: AI से काम का परिणाम और continuity मिलने पर उपयोगकर्ता कम शब्दों में निर्देश आगे बढ़ाता है। प्रमाण: short follow-ups + handover; प्रतिकूल उदाहरण भी जुटाएँ।
H02: novelty creative विषयों को शुरुआती रुचि देती है; उससे लगातार action होगा या नहीं, अज्ञात।
H03: projects की अधिक संख्या exploration का संकेत हो सकती है, लेकिन कॉपी, पुराने imports और prototypes भी हो सकते हैं। इसे “काम छोड़ने की आदत” न कहें।

अगला assistant नए episode जोड़कर इन अनुमानों को मजबूत, कमजोर या हटाए; उपयोगकर्ता के सुधार को प्राथमिकता दे।

## अतिरिक्त प्रमाण और सावधानियाँ
- learning/task/AI_DAILY_LOGBOOK.md (18 अगस्त) में repo consolidation और universal handover का वर्णन मिला। इससे continuity की जरूरत पुरानी होने का संकेत मिलता है, पर यह AI की रिपोर्ट है; user की direct quote नहीं। उसी में Varanasi लिखा है, जबकि profile में Mirzapur; स्थान का विरोध unresolved रखें, वर्तमान निवास अनुमानित न करें।
- पुराने MASS APP 2 आलोचनात्मक दस्तावेज़ में procrastination और publishing के डर जैसे labels हैं। वे उस assistant की व्याख्याएँ हैं; direct user evidence बिना behaviour facts नहीं। उसमें “0 live apps” भी पुरानी स्थिति थी; बाद की profile पाँच published apps कहती है। यह बदलाव पुराने नकारात्मक निष्कर्षों को स्थायी मानने के विरुद्ध प्रमाण है।
- ebook decision-log के पहले हिस्से में खुद पुराने market/zero-risk/time-saving दावे संशोधित किए गए हैं। पुराने AI-generated plans को user की validated beliefs न मानें।
- तारीखवार scan: Vidhivat में 21 अगस्त–27 अक्टूबर की 29 अलग commit dates। यह बार-बार activity का प्रमाण है; author की व्यक्तिगत daily persistence का पूरा प्रमाण नहीं। पुराने english spoken में 3 जुलाई–20 अगस्त की 11 commit dates।
- वर्तमान chat में उपयोगकर्ता ने सवाल बाद के लिए टालने और private/family विभाजन की स्पष्ट पसंद दी। स्थगन को उस विषय में अरुचि या अस्वीकृति न मानें।

## Claude/Gemini में अलग स्रोत से मिले संकेत — बैच 1
- देवनागरी पसंद का अतिरिक्त direct प्रमाण: Claude में “Devnagri Mein batao”। यह input की Roman script से अलग output preference को समर्थन देता है। स्रोत: chats/records/claude-work-b1278015-5461-413c-a2b3-6f657468e5bf.md#event-002।
- असंतोष के बाद सुधार का स्पष्ट निर्देश: Gemini Snake Reels में humour कम लगा तो पहले character plan और बेहतर dialogue मांगा। यह output correction है, project त्याग नहीं। इसे सभी कामों का universal process न बनाएं। स्रोत: chats/records/gemini-trade-638463cd4fd67e96.md#event-002।
- “2” का अर्थ उसी response के दूसरे joke-option का चुनाव था। assistant की generation failure user का interest खत्म होना नहीं बताती। स्रोत: वही #event-003।
- template वाले दस्तावेज़ में format/recipient का पालन मांगा। दूसरे व्यक्ति के लिए लिखा first-person आवेदन user की निजी health/financial biography नहीं। स्रोत: chats/records/gemini-schandan995-c4f08354183aeae7.md#event-001।
- market research का अनुरोध वास्तविक channel launch का प्रमाण नहीं। assistant के trend/growth/platform दावे इस समीक्षा में verified नहीं और user beliefs में आयात नहीं किए गए। स्रोत: Claude work chat #event-001।

## Gemini के दूसरे बैच से जुड़े प्रमाण
- SpeakEasy review में user का निर्देश है: पहले पूरा structure समझो, फिर जरूरी improvements और global competition के gaps बताओ। source cluster: speakeasy-related-export-reviews-1-2-3; records e6457e3505a8a5b9, 20a81b18668e97fb, 048585c37df11a1a के event-001। तीन related export reviews को तीन independent confirmations न गिनें।
- उसी cluster का “Research start karein” research-plan से आगे बढ़ने का निर्देश है। code implementation/काम के घंटे इससे सिद्ध नहीं। पहले किया काम user बताता भी है—“केवल planning करते हैं” जैसी स्थायी धारणा उचित नहीं।
- Global YouTube prompt Claude और Gemini दोनों में शब्दशः मिला। source: chats/records/gemini-trade-5720dcfaa659c4d2.md#event-001 तथा Claude work b127... record। यह prompt reuse का तथ्य है; compare/verify/असंतोष का motive अभी unknown।
- Mobile से PC जैसी Hostinger/AI coding पहुँच पूछी गई; source: chats/records/gemini-trade-51012bf288ba85d8.md#event-001। इस प्रसंग की portability जरूरत, configured system नहीं।
- Title-based भ्रम रोकें: AI Model Development वाली chat में user Gemini की तुलना पूछता है; खुद model बनाना सिद्ध नहीं। “सही रास्ता” chat में सिर्फ “रस्ता गलत” है, इसलिए जीवन-दिशा या मनोस्थिति का निष्कर्ष नहीं।

## Claude Code saved sessions — संदर्भ सहित अतिरिक्त प्रमाण
- Product language ≠ personal response language: QR को global product बनाने के लिए English-only और screenshots English मांगी थीं; PDFKaro में English default + Hindi। ये ऐतिहासिक product requirements हैं, अपनी बातचीत की देवनागरी पसंद से विरोध नहीं। स्रोत: QR 29391d6a... event-002; PDF 2e5d... event-004।
- Study Station में APK/server विभाजन और बाद में structure, screen space, mock-test lag तथा phone QA के निर्देश मिले। इसे जरूरत refine करना कहें; किस feature का implementation हुआ, अभी इस review से पता नहीं। स्रोत: claude-code-0d538d6e... events 001–004।
- session folder english spoken होने के बाद user ने “मैं Mistri Calculator की बात कर रहा था” स्पष्ट किया। ऐसे correction को folder के अनुमान पर प्राथमिकता दें; नाराज़ स्वभाव का label नहीं। स्रोत: claude-code-b9c4f524... event-002।
- Jameen में स्पष्ट चरणबद्ध completion और अक्टूबर में continue मिला; बीच की अवधि में निष्क्रियता का अनुमान नहीं। source UUID/timestamps संबंधित record में हैं।
- Vidhivat में उस काम के लिए ChatGPT handover, अभी क्या हो रहा है और आगे क्या होगा बताने की मांग मिली। यह continuity के पुराने प्रमाण का context-specific समर्थन है।
- PDF की “AI नहीं” पंक्ति mixed pasted checklist के भीतर historical project instruction है; सभी projects या AI के प्रति निजी विरोध नहीं।
- बड़े local logs में user-labelled tool results, images, summaries, client-generated resume और pasted page text मिलते हैं। authorship/context जाँच बिना उन्हें user की अपनी भाषा/विश्वास में न मिलाएँ।

## Mistri Calculator session (3–4 अक्टूबर) — संदर्भ सहित प्रमाण
- AI की क्रमांकित सूची से नंबर चुनना: "1 se 3 tak fix karo pehle", फिर काम के बीच "4-5", बाद में "thik h sab improve kar do"। AI ने सीमित क्रम (पहले 1 और 2) सुझाया था, user ने बड़ा दायरा चुना। एक session का observation; स्थायी pattern के लिए और स्वतंत्र प्रसंग चाहिए। कारण अज्ञात। स्रोत: chats/records/claude-code-336033d6-f2d3-4471-936d-34beedaa7616.md#event-002, #event-003, #event-009।
- असली फ़ोन पर देखकर feedback: "apk build karke phone me install karo" के ~5 मिनट बाद "mera ghar to blank h"। आपत्ति output (खाली screen का UX) पर थी, feature पर नहीं; उसके बाद feature और बढ़ाया गया। स्रोत: वही #event-006, #event-007।
- छूटा हिस्सा याद दिलाने पर तुरंत जोड़ना ("steel screen me bhi ft ka option laga do") और AI के एक-पंक्ति प्रस्ताव पर "haan" — continuity और पूरा करने की ओर संकेत, universal नियम नहीं। स्रोत: #event-004, #event-005।
- काम पूरा होने पर जाँच और release की माँग ("pure app ko tum test bhi kar lo…", "version badha kar commit kar do") — idea → action → verification → release का एक पूरा प्रसंग, follow-through का प्रमाण। स्रोत: #event-011, #event-013।
- अगले दिन "Try again" से वापसी; बीच का अंतर निष्क्रियता नहीं माना। स्रोत: #event-012।

## Moat Stories YouTube session (revision 9) — संदर्भ सहित observations
स्रोत: chats/records/claude-code-bbd0af6e-7583-4b2f-9d7c-a0627fe17847.md। ये इसी project के observations हैं, स्थायी pattern नहीं।
- क्रम और कारण खुद तय करना: "Delta se shuru karo, sabse flat hai" (#event-005)। AI-प्रस्तावित काम में प्राथमिकता user ने दी।
- सख़्त निर्देश न माने जाने पर दोहराना और ज़ोर देना: "maine isake liye pahale bhi bataya tha lekin hata nahi" (#event-009)। लक्ष्य इसी project में Gemini; गुस्सैल स्वभाव का label न दें।
- फ़ैसला AI पर छोड़ना: "bas tum likho" (#event-015)। साथ ही बड़े प्रश्न पर "bahut soch samajh kar batana" (#event-017) — गहरी सोच की माँग।
- निराश करने वाले नतीजे के बाद जल्दी अगला निर्णय: "dil tut gaya" के दो मिनट बाद परीक्षा का निर्णय (#event-019, #event-020), फिर रोकना, फिर 2 दिन बाद upload पर वापसी (#event-021)। एक episode; कारण अज्ञात।
- output-level बारीक सुधार, पूरे विकल्प की अस्वीकृति नहीं: title में केवल "Why" (#event-023)। मौजूदा "हल्की अस्वीकृति के बाद सुधार" संकेत से मेल।
- छोटे संदर्भ-आधारित संदेश ("status", "aage badho", "continue", "abhi") — H01 का एक और स्वतंत्र संदर्भ (#event-027)।
- Product language अंग्रेज़ी (videos), बातचीत Roman हिंदी, जवाब देवनागरी — पहले से दर्ज product/personal भाषा भेद का समर्थन।

## Jameen Napi session (15 सितंबर–2 अक्टूबर, revision 2) — संदर्भ सहित प्रमाण
- AI की तकनीकी सलाह की जगह अपना तरीका: AI ने Google Maps SDK सुझाया, user ने "flutter_map hi use karo" कहा। यह तरीका-स्तर की अस्वीकृति है, feature की नहीं; कारण अज्ञात। स्रोत: chats/records/claude-code-a08bc317-9400-4805-b8e4-f6767c20f5ec.md#event-002।
- असली फ़ोन पर जाँच — **candidate pattern, अब तीन अलग प्रसंग:** Study Station में phone QA का निर्देश (claude-code-0d538d6e…), Mistri में "apk build karke phone me install karo" (claude-code-336033d6… #event-006), और यहाँ "mobile jod diya" → "install kar ke check karo" (#event-010, #event-011)। यहाँ फ़ोन पर ही चार गड़बड़ियाँ पकड़ी गईं जिन्हें 92 tests नहीं पकड़ पाए, जिनमें GPS stream का पूरी तरह न चलना भी था। फिर भी 'हमेशा' न लिखें — प्रतिकूल उदाहरण भी खोजें।
- release से पहले "production ready?" पूछना (#event-009) — Mistri में "version badha kar commit kar do" के साथ, release-तैयारी पर ध्यान का दूसरा प्रसंग। observation।
- एक शब्द के निर्देश: "ha", "ha kar do", "start", "continue", "Try again" — पिछले AI प्रस्ताव पर निर्भर। H01 का समर्थन। "Try again" यहाँ AI के अटकने के बाद आया (#event-013); Mistri में भी अगले दिन वापसी पर। सहमति उसी प्रस्ताव तक सीमित।
- बीच में फ़ोन का दूसरा उपयोग (call, भुगतान app) — testing वाला फ़ोन रोज़मर्रा का फ़ोन भी है। व्यवहार-निष्कर्ष नहीं, practical constraint: tap भेजने से पहले foreground app जाँचें। call करने वाले तीसरे व्यक्ति का नाम दर्ज नहीं।
- AI के सवालों पर चुप्पी (सड़क-दूरी का अर्थ, versionCode, tiles की शर्तें) = unknown, अस्वीकृति नहीं। 16 दिन का अंतराल (16 सितंबर → 2 अक्टूबर) भी निष्क्रियता का प्रमाण नहीं।
- AI की गलती अलग: AI ने ख़ुद manifest से geolocator service हटाकर GPS तोड़ा था, और एक बार उसके tap दूसरे app में गए। ये AI की त्रुटियाँ हैं, user के व्यवहार में न गिनें।

## Vidhivat session (25–27 अक्टूबर, record revision 2) — संदर्भ सहित प्रमाण
स्रोत: chats/records/claude-code-ffb11889-d7cf-436d-a297-93a246d1b0a6.md (सभी 16 human-origin + 4 queued संदेश)।
- छोटे आगे-बढ़ो निर्देश: «age badho», «aage», «karo», «ha», «aage badhe», «aage badhate raho», «Try again» (#event-007,
  008, 013, 014, 015, 003, 016)। H01 का समर्थन, पर सब एक ही chat से — स्वतंत्र प्रसंग नहीं।
- «हाँ/करो» assistant के ठीक उसी प्रस्ताव पर लागू हुआ; उसी संदेश के दूसरे फ़ैसले वाले प्रश्न (पाँच आरतियाँ, काल भैरव की
  तारीख़, पुराण-प्रसंग सूची, घर के पंचांग के पन्ने) बार-बार पूछे जाने पर भी बिना उत्तर रहे — unknown, अस्वीकृति नहीं।
  Jameen Napi session में भी AI के सवालों पर चुप्पी दर्ज है: दो प्रसंग, observation। *AI सलाह (user का कथन नहीं):*
  फ़ैसले वाला प्रश्न अलग और एक बार में एक पूछें।
- काम चलते समय स्थिति पूछना और बीच में निर्देश भेजना: «abhi kya kar rahe ho aur kaya karana baki h», «aur kya baki h»,
  «अभी और क्या बचा»; चार queued संदेश (#event-004, 005, 006, 009, 011, 019)।
- सीमित अस्वीकृति: «1 no chhod kar aage badho» ने assistant की सूची का एक item (release) *इस session से* हटाया, release का
  लक्ष्य नहीं — उसी रात upload की ख़बर ख़ुद दी (#event-010, #event-012)।
- इस project में कई AI का कार्य-विभाजन: चित्र/UI ChatGPT से (#event-005), testing/audit ChatGPT से (#event-012, #event-018),
  Codex का session उसी repo में commit करता है (commit 8951126)। केवल Vidhivat का प्रमाण; universal नहीं।
- लिपि: ज़्यादातर Roman Hindi; 25 Oct रात दो देवनागरी संदेश (#event-011, #event-012) — कारण अज्ञात (voice संभव, अपुष्ट)।
- पंडित-जाँच का विकल्प छोड़कर छपे ग्रंथों पर टिकना (reported-001, repo से पुष्ट): उपलब्ध साधन की सीमा में निर्णय; व्यक्तित्व
  का निष्कर्ष नहीं।

## Vidhivat गति वाली chat (23 सितंबर, record 179c01a3) — संदर्भ सहित प्रमाण
- लक्ष्य नतीजे की भाषा में, तरीका AI पर: "hamara app smoothe fast aur bin lag ke chalana chahiye resarch karo" (#event-001)। एक episode; observation।
- छोटा आदेश, पूरा काम: "sb fix karo" (#event-003)। AI ने क्रम से (#1–#2 पहले) सुझाया था; user ने सब एक साथ चुना। H01 का एक और संदर्भ; सलाह की अस्वीकृति नहीं, विस्तार।
- जवाब के बाद उसी विषय का अगला हिस्सा पूछना — पूजा प्लेयर (#event-002)। कारण अज्ञात।
- फ़ोन पर profile-mode नाप की सलाह **AI की** थी, user के शब्द नहीं — इसलिए "असली फ़ोन पर जाँच" वाले candidate pattern में इसे नहीं गिना।
- 34 दिन की चुप्पी के बाद वापसी केवल स्मृति-रिकॉर्ड के लिए (#event-004); बीच में commit e8fb7dc (2 अक्टूबर) — काम छोड़ना नहीं।
- स्रोत: chats/records/claude-code-179c01a3-493a-49ce-bfc3-c818a9a711b1.md


## revision 13 — विधिवत UI चैट से नया प्रमाण (27 अक्टूबर 2026)
ये इसी project के observations हैं; स्थायी personality labels नहीं।
- छोटे «continue», «karo», «kya huva», «kitana time lagega» सक्रिय काम की निरंतरता/status के उदाहरण हैं (23–26 अक्टूबर; chats/records/codex-01a169c3-66b2-7a12-b047-e77a5791ee15.md §4 और user inventory refs)। इन्हें अधीरता/गुस्से का निदान न बनाएं।
- implementation चुनने की छूट के साथ सटीक दृश्य corrections आए: «sab tumhare upar chhod raha hu», लेकिन height/alignment/unique images भी बताए (वही #ui-event-005–010,24 अक्टूबर)। delegation और feedback विरोधी नहीं।
- phone-QA candidate pattern की **सीमा/प्रतिकूल उदाहरण** भी रखें: «phone pe test kar lena» (25 अक्टूबर; #ui-event-021), फिर उसी release में «ab check karane ki jarurat nahi h…publias karo» (#ui-event-028); 27 अक्टूबर को नई device QA फिर माँगी (#ui-event-029)। “हमेशा फोन पर जाँच” का स्थायी नियम गलत होगा।
- योजना से generation (#ui-event-002–003), तथा admin से पहले उसी दिन release का scope चुनना (#ui-event-018) ठोस decision उदाहरण हैं। बदलाव का कारण जहाँ user ने कहा वहीं दर्ज है; दूसरे बदलावों पर जल्दी/जोखिम/अरुचि अनुमान नहीं।


## revision 14 — विधिवत audit चैट की मूल-स्रोत स्मृति (27 अक्टूबर 2026)
सीमित observations; नया स्थिर personality label नहीं।
- काम में छोटे संदर्भगत निर्देश («start kar do», «continue», «aage ka test jari rakho»; [२](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-002), [३](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-003), [१७](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-017)) के साथ स्पष्ट quality constraint («source aur aadhar ke sath», [५](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-005)) भी है। छोटा वाक्य गुणवत्ता के प्रति उदासीनता नहीं।
- लगातार काम की माँग और temporary stop दोनों मौजूद: [१२/१४/१५](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-014)। मौजूदा स्पष्ट instruction प्राथमिक; बीच की चुप्पी का अर्थ अज्ञात। काम से ऊबना/छोड़ना या मनोवैज्ञानिक कारण नहीं निकाले।
- परिणाम/सीमा का प्रश्न: «अभी क्या सब कुछ टेस्ट कम्प्लीट हो गया है क्या? एक बार बताना.» (26अक्टूबर21:27IST; [१६](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-016)); «kya aur janche Baki Hain» (27अक्टूबर02:09IST; [१८](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-018))। यह status माँग है; अपनेआप अविश्वास/चिन्ता का प्रमाण नहीं।
-19मानव घटनाएँ मूल sourceID से हैं; इसी project की Claude/UI chats से समान outcome को बार-बार independent confirmation न गिनें। आखिरी memory prompt तैयार निर्देश है; उसकी औपचारिक भाषा सहज रोजमर्रा की typing का नमूना नहीं।


## revision 15 — Study Station की स्रोत-सहित स्मृति (28 अक्टूबर 2026)
ये संदर्भगत observations हैं; स्थायी व्यक्तित्व/clinical निष्कर्ष नहीं।
- सीधे implementation ([«इसको बताना नहीं है, तुम इसको बना दो»](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-006)) के साथ पहले काम की सूची ([«पहले एक लिस्ट बना लो»](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-010)) और परिणाम पूछना ([«क्या हुआ, क्या नहीं हुआ»](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-011)) दोनों मौजूद। योजना से सार्वत्रिक अरुचि न निकालें।
- UI को देख कर scope-specific feedback: header gap छोटा ([निर्देश](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-028)), card/buttons का touch हटाना ([शिकायत](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-030)), Settings gap ([नया सुधार](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-068))। एक ही chat की पुनरावृत्ति को कई स्वतंत्र pattern confirmations न गिनें।
- पहले UI, फिर प्रारम्भिक release और छोटे बदलाव बाद में; फिर fresh tests की माँग ([UI प्राथमिकता](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-025), [fresh test + संक्षिप्त प्रक्रिया](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-066))। यह हमेशा testing छोड़ने की पसंद नहीं। बीच की चुप्पी काम छोड़ने का प्रमाण नहीं।


## revision 17 — उपलब्ध उदाहरण स्वयं देखकर समझना
29 अक्टूबर को नए उदाहरण माँगने पर “tumhare pass sab h dekh sakate ho” कहा: [source](../chats/records/01a17a01-396e-70e1-8f76-f9fe4447efac.md#current-event-013)। इस काम में पहले उपलब्ध रिकॉर्ड से उदाहरण निकालें; सभी accounts/पूरी history हमारे पास है, ऐसा न मानें। मौजूदा प्रमाण: [विधिवत audit की रोक/वापसी](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-014), [अगले दिन वापसी](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-event-015), [Jameen में वापसी](../chats/records/claude-code-a08bc317-9400-4805-b8e4-f6767c20f5ec.md#event-003)। ये पुराने episodes की पुनः समीक्षा हैं, नए स्वतंत्र behavioral confirmations नहीं। कारण न बताया हो तो अज्ञात ही रहे।
