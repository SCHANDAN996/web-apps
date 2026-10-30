# काम करने का साझा ढाँचा
हर काम की अपनी ID, स्रोत और स्थिति रखें। विशेषज्ञ प्रस्ताव दे; coordinator एक consolidated plan रखे।

| task_id | लक्ष्य/क्यों | संबंधित विशेषज्ञ | अगला ठोस काम | जरूरत/बाधा | परिणाम का प्रमाण | स्थिति |
|---|---|---|---|---|---|---|
| memory-chat-001 | चैटों को अलग और ढूँढ़ने योग्य रखना | बातचीत, प्रमाण, मुख्य | stable chat records और compilation | उपलब्ध history की सीमा | chats/INDEX.json और अलग records | प्रारंभिक 12 records बनाए गए; पूर्ण history नहीं |
| values-001 | बताए हुए मूल्यों की memory | मूल्य, प्रमाण | आगे के वास्तविक उदाहरण source सहित जोड़ना | मूल्य स्वयं उपयोगकर्ता बताएँगे | confirmed statement + event link | ढाँचा तैयार; सामग्री अभी कम |
| finance-001 | आर्थिक स्थिति और कमाई का निर्णय | आर्थिक, लक्ष्य, सलाह | बताई गई राशि/समयसीमा से स्थिति भरना | वास्तविक जानकारी उपलब्ध नहीं | dated user statements | जानकारी प्रतीक्षारत; कोई transaction नहीं |
| legacy-001 | बच्चों के लिए original thoughts | विरासत, मूल्य, प्रमाण | उपयोगकर्ता तैयार हों तब approved यादें | प्रश्न बाद के लिए स्थगित | user-authored/approved सामग्री | स्थगित प्रश्न फिर न पूछें |
| project-001 | रुचि को काम और परिणाम से जोड़ना | प्रोजेक्ट, व्यवहार | तारीखवार इतिहास को वास्तविक deliverables से जोड़ना | अपूर्ण code/history review | source-linked outcome | शुरुआती timeline उपलब्ध |

प्रस्तावित सलाह, उपयोगकर्ता का निर्णय और किया हुआ काम अलग अवस्थाएँ हैं। नया खर्च/प्रकाशन/बाहरी संदेश सिर्फ role होने से अधिकृत नहीं होता। सामान्य reversible स्थानीय काम अनुरोध की सीमा में आगे बढ़ाएँ।


## revision 13 — विधिवत UI चैट से नया प्रमाण (27 अक्टूबर 2026)
| task_id | लक्ष्य | अगला ठोस काम | प्रमाण/सीमा | स्थिति |
|---|---|---|---|---|
| vidhivat-art-device-20261027 | नए छह चित्रों की वास्तविक device QA | उपयुक्त नवीन build और जुड़ा फोन मिलने पर tap/scroll/बड़े अक्षर | chats/records/codex-01a169c3-66b2-7a12-b047-e77a5791ee15.md#ui-event-029; desktop1491/21pass, कोई device नहीं | device QA बाकी; इस memory update में build नहीं |
| vidhivat-admin-deferred-20261025 | एक login/project tabs/analytics | release प्राथमिकता के बाद scoped integration की वर्तमान स्थिति तय | वही #ui-event-016–018 | Study Station placeholder; full SSO अपुष्ट |


## revision 14 — विधिवत audit चैट की मूल-स्रोत स्मृति (27 अक्टूबर 2026)
| task_id | लक्ष्य | अगला ठोस काम | प्रमाण/सीमा | स्थिति |
|---|---|---|---|---|
| memory-audit-chat-20261027 | इसchatकीस्रोतसहितस्मृति | indexedrecordऔरportablecopyसेअगलीchatसंदर्भले | `chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md`;19humanmessages,partialtoolhistory | इसrunमेंreviewedmerge |
| vidhivat-audit-release-followup | sourcefixबनामshippedpackageका अन्तर | नवीनcheckpointऔरभविष्यकेpackageकीपहचानकरJ025केfieldsमिलाएँ | [action002](../chats/records/codex-01a1661f-7a3c-7d23-9f85-d64b1f899181.md#audit-action-002); पुरानाcode8; नईbuildनिर्णयअनुमति नहीं | स्रोत/नयेpackage/deviceपरनिर्भर |


## revision 15 — Study Station की स्रोत-सहित स्मृति (28 अक्टूबर 2026)
इस memory अनुरोध के बाद अगला ठोस Study Station कदम: नवीन project checkpoint पढ़कर GitHub login और Study Station के brand Instagram/YouTube account की स्थिति जाँचें; फिर आवश्यक human login/consent को स्पष्ट करें। [social automation की माँग](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-072) और [Instagram अनिश्चित](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-073)। Telegram/Shorts existing GitHub workflow को server cron में दोहराना user ने रोका है ([चयन नियम/हैंडऑफ़](../chats/records/01a1342a-8d3b-71b1-b5b3-d23ffabdfa0f.md#ss-event-061)), अतः duplicate scheduler न जोड़ें। यह कार्ययोजना है; automation चालू होने का दावा नहीं।


## revision 17 — वर्तमान लक्ष्य की स्पष्टता
लक्ष्य: वैकल्पिक आय से नौकरी replace करना; उपलब्ध समय रोज5घंटे (user self-report)। अगला प्रस्तावित स्थानीय काम: पाँच मौजूदा उत्पादों का वर्तमान उपयोग/release/आय/छोटे अवरोध वाला पंजी। खर्च अस्पष्ट; बजट और replacement की तारीख तय नहीं। मुख्य coordinator एक प्रयोग की तुलना करवाए, निजी स्रोतों के आधार पर; कोई नया publish/खर्च/नौकरी छोड़ने का काम इस उत्तर से अधिकृत नहीं। [मूल उत्तर](../chats/records/01a17a01-396e-70e1-8f76-f9fe4447efac.md#current-event-013), [समय](../chats/records/01a17a01-396e-70e1-8f76-f9fe4447efac.md#current-event-014)।
