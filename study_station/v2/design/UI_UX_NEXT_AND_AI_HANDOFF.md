# Study Station: अगला UI/UX चरण और AI handoff

तारीख: 23 October 2026। स्थिति: प्रस्तावित plan, implementation नहीं।
आधार: मौजूदा PC templates, design system, implementation notes और Git history। यह नया phone usability test नहीं है।

## लक्ष्य
Hindi-first learner को पढ़ाई, अभ्यास और अपना workspace कम taps में मिले। पहले से बने features और learner data सुरक्षित रहें। केवल नया दिखना सफलता का माप नहीं है।

## क्या पहले से मौजूद है
2×2 illustrated Home cards, तीन themes, custom choice sheets, structured question/result cards, favourites/share, scoped reset, offline study, named notebooks/fullscreen drawing, group/class/shared workspace flows मौजूद हैं। इन्हें फिर से बनाने की जरूरत नहीं।

## सुधारों का क्रम

| क्रम | हिस्सा | प्रस्ताव | स्वीकार करने की जाँच |
|---|---|---|---|
| P0 | Home | सबसे ऊपर compact Continue/आज की पढ़ाई action; membership को account/status क्षेत्र में छोटा entry बनाना। Workspace, Group, Teacher Class, Shared के चार मुख्य cards ऊपर ही रहें। पढ़ना/अभ्यास/रिवीजन साफ study block में; Jobs और detailed stats बाद में। दोनों मुख्य blocks की ऊँचाई कम रखें। | 360px phone पर मुख्य action स्पष्ट; बड़े अक्षरों में भी cards या buttons न कटें; existing main collaboration entries छिपें नहीं। |
| P0 | Shared controls | एक card/button/choice sheet/dialog spacing system; long Hindi labels, keyboard, landscape और Android Back के लिए एक सा व्यवहार। Press/ripple card के radius के भीतर। | कोई touching action, horizontal scroll या कटता अंतिम option नहीं; focus/Back सही जगह लौटें। |
| P0 | पढ़ना और सवाल | headings, numbered steps, paragraphs और solution hierarchy एक जैसी। प्रश्न संख्या, palette selection और resume state एक ही source से। Justify केवल पढ़ने के paragraphs पर; options/short UI labels पर नहीं। | सवाल 12/50 resume पर 12 ही दिखे; next/previous से उत्तर या rough work न खोए। |
| P1 | Mock | exam cards पर exam, question count, duration, negative marking और availability स्पष्ट। नया attempt, जारी attempt और पुराना result अलग actions। | अधूरा question bank होने पर misleading Full mock label नहीं; submit/cancel/timer/scoring बरकरार। |
| P1 | Jobs | compact notification list; संस्था, पद, योग्यता, अंतिम तारीख और official source पहले। Search वास्तव में कितने loaded results पर है यह स्पष्ट; filter reset के बाद state सही। Detail पर notice और apply अलग actions। | 100 loaded entries को पूरी database search न बताया जाए; unverified source को verified न दिखाएँ। |
| P1 | Workspace | अधिक canvas, compact icon tools, color/width sheet, स्पष्ट save state, Fit page और ? Help। Group/Class screens में role, privacy, sharing/edit permission और reconnect state साफ। | दो-finger zoom/pan से ink न बने; zoom save-history न बढ़ाए; keyboard/rotation में toolbar reachable; named notebooks और exports पुराने data सहित खुलें। |
| P1 | Progress/Settings | progress पढ़ने योग्य summaries; chapter/subject/all reset का scope व preview स्पष्ट। Local data, backup और cloud/shared data की अलग भाषा। | Cancel से कुछ न मिटे; एक learner/reset scope दूसरे का data न छुए; confirmation यह साफ बताए कि क्या बचेगा। |
| P2 | Visual polish | existing tokens, readable Hindi fonts, समान icon stroke/size; हल्की depth केवल navigation cards पर। Reading surfaces शांत। Motion छोटे transform/opacity transitions तक। | Light/Dark/Paper, reduced-motion, keyboard focus और 44px touch targets; low-end phone में heavy blur या permanent animation नहीं। |

### सीमा
नई voice/video teaching, AI-generated illustrations का पूरा set, नया framework या paid analytics इस UI चरण का हिस्सा नहीं। उपलब्ध feature के लिए ही दावा दिखे। Glass/3D styling पढ़ाई की readability और speed से ऊपर नहीं होगी।

## पहले वाले AI / Claude को सूचना

1. Handoff और promo integration पूरा पढ़ें: HANDOFF_CHATGPT.md, promo/INTEGRATE.md और v2/docs/PROMO_PC_INTEGRATION_2026-10-23.md।
2. PC का UI/advanced-feature code और upstream content अलग histories में हैं। पूरी branch reset/checkout, पूरे app directory का overwrite, और force-push न करें।
3. PC में workspace v2, groups/classes, favourites/share, question navigation, scoped reset, offline study, Google auth और membership code पहले से हैं। हर feature की वास्तविक implementation और tests पहले देखें। पुराने planning notes को current status न मानें।
4. DESIGN.md में theme/navigation descriptions और UI_UX_STATUS.md में कुछ pending claims पुराने हैं। पहले current status matrix बनाएँ: source में बना, browser verified, phone verified, deployed, Play bundle में शामिल—ये अलग columns हों।
5. 1.2.0/code 3 Google review में भेजा गया है। नए source changes उस submitted bundle का हिस्सा नहीं हैं। अगली release में नया version code और नए सत्यापित screenshots चाहिए।
6. Website PayU चलता है; Play app में खरीदारी अभी बंद रखने का owner निर्णय है। UI redesign के बहाने UCB/Play billing चालू न करें, trial/prices न बदलें। GST अज्ञात है और अतिरिक्त financial retention को owner ने मंजूरी नहीं दी है।
7. Promo selection के नियम, AIR/PIB provenance, question parser, scoring, auth, account isolation और backup validation को visual polish के लिए ढीला न करें।
8. Telegram और Shorts सिर्फ GitHub Actions से चलेंगे। posted.json और posted_shorts.json workflow-owned हैं; हाथ से edit या QA render से mutate न करें। QA के लिए PROMO_POSTED temporary path रखें।
9. कोई token/password/DB/keystore/APK/video/screenshot commit न करें। Existing user progress या production account पर destructive QA न करें।
10. हर batch के अंत में exact changed files, before/after screenshots, tests, remaining limits और source/deploy/APK inclusion अलग रिपोर्ट करें।

## GitHub पर सुरक्षित एकीकरण

### 1. संरक्षण और तुलना
- PC HEAD, tracked staged/unstaged changes और untracked source का सुरक्षित local checkpoint लें; secrets/build artifacts अलग और बाहर रहें। Existing index/staged work न खोए।
- origin से work branch व main fetch करें। UI, auth/offline, classroom/workspace, membership और content का अलग change manifest बनाएँ।
- Initial integration में histories 35 local बनाम 1517 upstream commits से diverged थीं; वह संख्या current status मानकर reuse न करें। हर बार नया comparison करें।

### 2. Reviewable integration
- latest upstream work branch से isolated integration checkout तैयार करें; PC checkout को reset न करें।
- PC features को dependency order में छोटे reviewed commits में port करें: foundation/UI assets → question/reader → workspace/classroom → auth/offline/privacy → membership policy-preserving changes। Existing upstream implementation मिलने पर duplicate feature न बनाएँ।
- Books, Current Affairs tools, promo, workflow changes और newest posted logs upstream से सुरक्षित रहें। File-by-file conflicts resolve करें; broad ours/theirs merge नहीं।
- main पर चल रहे promo workflows को work-branch UI integration के बहाने बदलने/दोबारा scheduler बनाने की जरूरत नहीं।

### 3. जाँच के बाद push
- दोनों भाषाओं और तीन themes में 360px portrait, short landscape और बड़े text size पर screenshots/flows जाँचें।
- pytest -q; affected browser flows; app.shell --check; Android unit/build checks जब native changes हों। Linux पर full suite आवश्यक; Windows symlink privilege failure को छिपाएँ नहीं।
- Offline reading, resume, mock scoring, favorites, reset cancel/confirm, backup isolation और workspace gestures regressions जाँचें। Promo dry-run और isolated single-video render भी जाँचें।
- Push से ठीक पहले fetch करें; bot/Claude के नए commits पर rebase/resolve करें और प्रभावित checks दोहराएँ। Normal push केवल claude/elegant-rubin-sgov1q पर; force-push नहीं।
- Source push, production server deploy और Play update अलग steps हैं। इस plan में source planning मात्र है; submitted Play release नहीं बदली गई।

## पहले implementation batch की सीमा
Home hierarchy + shared cards/buttons/dialog spacing + current feature-status documentation। पहले इसी छोटे batch की before/after समीक्षा; फिर reader/questions, Jobs/Mock और Workspace polish के अलग batches।
