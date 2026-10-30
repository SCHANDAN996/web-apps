# चंदन की विशेषज्ञ मंडली
27 अक्टूबर 2026 · मुख्य समन्वयक + नौ विशेषज्ञ

| भूमिका | ID | काम |
|---|---|---|
| मुख्य समन्वयक | `chandan_main` | विशेषज्ञों को काम बाँटना और सब जानकारी को एक जगह जोड़ना |
| व्यवहार और स्वयं को समझना | `chandan_person` | रुचि, अस्वीकृति, वापसी और लगातार काम के संदर्भ समझना |
| बातचीत विशेषज्ञ | `chandan_chat` | असली शब्द, संदर्भ और संवाद की शैली दर्ज करना |
| मूल्य और सिद्धांत | `chandan_values` | बताए हुए मूल्य, सही–गलत के कारण और दुविधाएँ समझना |
| राय और विचार सहयोगी | `chandan_advisor` | विकल्प, लाभ-हानि और उपयोगकर्ता के लिए उपयोगी अगला कदम |
| बच्चों और विरासत विशेषज्ञ | `chandan_legacy` | अपनी आवाज़ में यादें, सीख और परिवार के लिए सामग्री |
| आर्थिक स्थिति विशेषज्ञ | `chandan_finance` | बताई गई आय, खर्च, जरूरत, बजट और आर्थिक लक्ष्य |
| जीवन लक्ष्य विशेषज्ञ | `chandan_goals` | वर्तमान और दीर्घकालीन लक्ष्य तथा प्राथमिकताओं का बदलाव |
| काम और प्रोजेक्ट विशेषज्ञ | `chandan_projects` | तारीखवार गतिविधि, परिणाम और आगे करने का स्पष्ट क्रम |
| प्रमाण और गोपनीयता समीक्षक | `chandan_evidence` | गलत निष्कर्ष, विरोध, दोहराव और निजी जानकारी की जाँच |

## मुख्य एजेंट कैसे काम बाँटे
मुख्य बातचीत का assistant मुख्य समन्वयक की भूमिका ले और chandan_main के निर्देश पढ़े। अलग named coordinator तभी बुलाए जब उसी को इस run का एकमात्र writer नियुक्त किया जाए; parent उसके साथ memory न लिखे।

| अनुरोध | किन विशेषज्ञों की जरूरत |
|---|---|
| इस चैट से memory अपडेट | बातचीत + प्रमाण; मुख्य समन्वयक संकलित करे |
| मुझे/मेरे व्यवहार को समझो | बातचीत + व्यवहार + प्रमाण |
| मूल्य या दुविधा | मूल्य + जरूरत पर सलाह + प्रमाण |
| आर्थिक स्थिति/कमाई | आर्थिक + लक्ष्य + जरूरत पर प्रोजेक्ट/सलाह + प्रमाण |
| जीवन की दिशा | लक्ष्य + व्यवहार/मूल्य + सलाह |
| बच्चों के लिए यादें/संदेश | विरासत + जरूरत पर मूल्य + प्रमाण |
| कौन सा काम अब करना है | प्रोजेक्ट + लक्ष्य + जरूरत पर आर्थिक + सलाह |

हर सवाल पर दसों agents चलाना जरूरी नहीं। उपलब्ध क्षमता में काम बैचों में लें; सरल प्रश्न सीधे coordinator हल कर सकता है। कुछ विषयों की राय टकराए तो असहमति और आधार रखें; majority vote से तथ्य या उपयोगकर्ता की इच्छा तय न करें। अंतिम विकल्प उपयोगकर्ता का है।

## एक run का क्रम
1. वर्तमान अनुरोध/सीमा तय, manifest revision पढ़ें; मुख्य writer तय करें।
2. chat recorder से source proposal; जरूरी विषय विशेषज्ञों को उतना ही संदर्भ दें जितना काम के लिए चाहिए।
3. specialists अलग work/agents/<run-id>/<role>.md प्रस्ताव दें; shared files न लिखें।
4. evidence reviewer स्वतंत्र जाँच करे। unresolved बात को unresolved ही रखें।
5. coordinator एक stable chat file अपडेट करे, dedup/conflict जाँचकर मुख्य memory में delta जोड़े।
6. revision/changelog/handover, chats index/compilation और portable file साथ refresh करे।
7. करने के काम को agents/ACTION-PLAN.md के ढाँचे में लिखे; planned और done अलग हों।

## उपलब्धता की सही स्थिति
दो live review agents ने structure की समीक्षा की। दस custom-agent TOML definitions .codex/agents में बनाई गई हैं, बिना model override के। इसी session में नई definitions के auto-load की पुष्टि नहीं; अगली project session में runtime support के अनुसार उपलब्ध होंगी। आवश्यक हो तो coordinator वही role instructions generic subagent को दे सकता है। साधारण ChatGPT में यह role-based reading workflow है, स्वतः चलने वाले दस bots नहीं। persistent server bot, account connectors और background monitoring अभी नहीं बने हैं।

आधिकारिक आधार: [Codex custom subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) — project-scoped standalone TOML में name, description और developer_instructions। Global config/credentials नहीं बदले गए।
