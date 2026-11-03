# Login और 3-महीने trial का UX plan

26 October 2026 · स्थिति: login और 3-calendar-month trial लागू हैं; rollout तथा जाँच का रिकॉर्ड `docs/LOGIN_TRIAL_RELEASE.md` में है।
Owner decision: पुराने और नए दोनों users को 3 महीने का trial; paid membership की मौजूदा अवधि सुरक्षित। नया UI ही आधार रहेगा।

## मौजूदा code में मिली उलझन
- membership.html login को /classroom?return_to=/membership पर भेजता है: सामान्य पढ़ाई के लिए Classroom का संदर्भ अनावश्यक है।
- Login के बाद trial अलग activation button से शुरू होता है; learner को दो अलग सफलताओं को समझना पड़ता है।
- membership.js में status GET विफल हो तो panel छिप जाता है; error और loading का स्पष्ट रास्ता नहीं।
- 3 दिन/72 घंटे कई strings में लिखे हैं। अवधि के लिए एक server-owned policy चाहिए।
- membership panel का default payment-unavailable संदेश website के सक्रिय PayU और Play के disabled checkout में अंतर साफ नहीं बताता।

## मुख्य user journey
1. पढ़ाई की शुरुआत पर एक focused welcome screen: “3 महीने मुफ़्त पढ़ें”, “कोई भुगतान विवरण नहीं”, “अपने आप पैसे नहीं कटेंगे”। Feature list छोटी और केवल उपलब्ध features की।
2. Primary action “Google से शुरू करें”; secondary “यूज़र नाम से अकाउंट बनाएँ”; existing users के लिए स्पष्ट “पहले से अकाउंट है? लॉगिन करें”। Google unavailable होने पर काम करता password विकल्प दिखे।
3. अलग /login और account screen; Classroom route केवल Classroom के लिए। Trial offer sign-in button से पहले स्पष्ट हो: सफल sign-in के बाद trial अपने आप शुरू होगा।
4. सफल sign-in → authenticated server activation → membership confirmation → offline-access refresh → पहले चुनी पढ़ाई/सवाल पर वापसी। कोई दूसरा activation button या दोबारा login नहीं। Return destination same-origin allowlist से validate हो।
5. छोटा confirmation: “आपका 3 महीने का मुफ़्त trial शुरू हो गया” और वास्तविक समाप्ति तारीख। मुख्य button “पढ़ाई शुरू करें”। Confirmation dismiss होने के बाद status Account और छोटे Home indicator में मिले।

Login सफल लेकिन activation/network विफल हो तो “आप लॉगिन हैं; trial शुरू नहीं हो पाया” + Retry। User को signed out न दिखाएँ और पढ़ाई चालू होने का झूठा दावा न करें। Offline refresh विफल हो तो online access और offline readiness अलग बताएँ।

## Screen states
| स्थिति | user को क्या दिखे | action |
|---|---|---|
| Guest | trial offer और login विकल्प | Google / username |
| Signing in | “लॉगिन हो रहा है…” | duplicate taps बंद; cancel के बाद retry |
| Activating | “आपकी पढ़ाई तैयार कर रहे हैं…” | bounded wait; failure पर retry |
| Active trial | “मुफ़्त trial चालू”, शेष दिन और exact end date | पढ़ाई जारी रखें |
| Paid | “सदस्यता चालू”, paid end date | पढ़ाई जारी रखें |
| Offline-ready | अंतिम सफल जाँच और दोबारा जाँच की जरूरत कब है | पढ़ाई जारी रखें |
| Network problem | “अभी इंटरनेट से जाँच नहीं हो सकी” | Retry; valid offline access सुरक्षित |
| Expired | वास्तविक end date और उपलब्ध private-data actions | platform-appropriate renewal, export/settings |

Loading, cancelled login, wrong password, server error, signed-out और expired अलग states हों। Temporary request failure पर panel गायब न हो, status expired न बने। Error code/stack/internal namespace user को न दिखे।

## अवधि और पुराने users
- “3 महीने” = 3 calendar months, 90 दिन नहीं। Month-end पर destination month की आखिरी तारीख पर clamp करें; backend UTC, display स्थानीय तारीख/timezone में।
- नए user: पहली सफल sign-in/activation पर server time से 3 महीने। Re-login/reinstall/new phone trial दोबारा शुरू नहीं करें।
- पुराने non-paid trial users, expired सहित: rollout के एक स्थिर recorded timestamp से कम-से-कम 3 महीने। Existing later trial end हो तो कम न करें। Migration idempotent और versioned हो।
- Paid users: paid_until न घटाएँ, paid grant/refund ledger न बदलें। Launch trial eligibility को paid access से अलग record करें; final access = existing paid और applicable trial में जो बाद में समाप्त हो। किसी refund/automatic charge का वादा नहीं।
- तारीख केवल server तय करे; local clock, browser storage, username rename या progress reset से trial न बदले। Account reset और commercial entitlement अलग रहें।
- Rollout anchor 26 October 2026, 07:18:12 UTC पर स्थिर है। दोबारा login या deployment से यह नहीं बदलता।

## Account और Home
Account पर एक स्पष्ट summary: signed-in identity, trial/paid status, end date, offline readiness, logout और account/privacy controls। Home पर छोटा status link; हर screen पर paywall, timer या repeated popup नहीं। Trial में payment form मुख्य content से हटे। 3 महीने बाद कोई automatic debit नहीं।

Website में expiry के पास PayU renewal उपलब्ध होने पर ही दिखे। Play app में purchase अभी बंद रखने का मौजूदा निर्णय सुरक्षित; कोई external-payment bypass या disabled button को active दिखाना नहीं। Pricing ₹9/month और ₹51/year यथावत।

## Visual system
एक-column focused mobile screen, readable Hindi, छोटा progress feedback, एक primary CTA, स्पष्ट secondary login link। Existing tokens और Light/Dark/Paper themes। Keyboard के ऊपर submit/error visible; password show/hide और accessible labels। Tap targets >=44px, reduced motion, slow-network और screen reader status support। बड़े glass/3D panels login form या reading की readability कम न करें।

## Implementation batches
1. Dedicated login/account states, return-to behavior, localized copy और component preview।
2. Shared 3-calendar-month policy + atomic/idempotent activation + old-user rollout migration और rollback report। पहले dry-run counts, फिर backed-up migration; passwords/progress/payments को न छुएँ।
3. Home/account status, platform-specific membership page, native lease renewal और recovery paths।
4. Tests → source commit/push → matching server deployment → Android build/version update अलग। Play review/submitted bundle की वास्तविक स्थिति जाँचकर अगला upload तय करें।

## Acceptance
- Fresh Google signup, username signup, existing login, cancelled/failed Google, wrong password, rate limit, retry और return-to-question flows।
- First login पर केवल एक trial grant; concurrent taps और दो devices पर एक ही end date।
- Month-end/leap-year/year rollover; old active/expired/paid accounts; migration दोबारा चलाने पर कोई extra extension नहीं।
- Login succeed + activation fail, activation succeed + lease fail, logout/account switch और stale request responses।
- Valid offline access को temporary network failure पर न मिटाएँ; daily check policy और protected private-data actions सुरक्षित।
- HI/EN, तीन themes, 360px phone, short landscape, बड़े text और keyboard।
- Full Linux pytest, browser journeys, Android relevant unit tests और generated shell check। Production और real-phone verification अलग दर्ज हों; untested flow को passed न कहें।

## Scope boundary
यह plan approval के बाद implementation का आधार है। अभी 72-hour constant/strings/server dates नहीं बदले गए। Secrets, promo schedules और Play billing/UCB enable flags इस काम में नहीं बदलेंगे।

## Compact UI follow-up — 26 October 2026
Home और सामान्य cards के लिए एक साझा surface, border और shadow token set। Login/account पर वही illustrations, rounded cards और themes; केवल मुख्य action, access status और समाप्ति तारीख सामने। वैकल्पिक सहायता और payment/privacy जानकारी खोलने पर उपलब्ध। Errors, daily offline check, trial अवधि और prices अपरिवर्तित। Authentication और account scope के अलावा बाकी मुख्य pages पर भी mobile/theme/overflow smoke check करें।
