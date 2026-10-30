# “इसको अपडेट करो” — हर assistant के लिए प्रक्रिया

## शुरुआत
1. मुख्य फ़ोल्डर, CURRENT और version पहचानें। केवल पुराना ZIP मिला हो तो latest copy माँगें/खोजें। फ़ाइल पहुँच न हो तो updated files लौटाएँ; saved होने का झूठा दावा न करें।
2. उपलब्ध वर्तमान बातचीत पढ़ें। पुरानी chats उपलब्ध न हों तो अपने पास होने का दावा न करें। actual source/message या artifact दर्ज करें।
3. सब बातें save न करें: उपयोगी पहचान, पसंद, निर्णय, commitment, rejection, constraints, unfinished work और repeat patterns चुनें। निजी तीसरे व्यक्तियों का अनावश्यक विवरण छोड़ें।

## हर व्यवहार episode का रिकॉर्ड
id, observed_at (अनिश्चित हो तो null), recorded_at, source_id, source_kind, context, user_words, event_type, target, reaction_scope, interpretation, confidence, alternative_explanation, follow_up_state, related_episode_ids, privacy।
event_type: idea / interest / exploration / decision / commitment / action / correction / rejection / pause / return / completion / preference।
follow_up_state: unknown / not_yet_checked / acted / blocked / paused / abandoned_explicitly / completed।
चुप्पी = unknown; folder न बदलना = no recorded activity; केवल बोलना = action नहीं।
“नहीं ठीक नहीं” में target अस्पष्ट हो तो output-level provisional rejection लिखें, पूरे goal का rejection नहीं। एक chat का “हाँ” दूसरी chat की permission न बने।

## तथ्य और पैटर्न का अलग जीवनचक्र
- सीधा कथन: self-report/confirmed preference के रूप में रखें। system में वास्तव में हुई कार्रवाई: tool/artifact प्रमाण जोड़ें।
- assistant की पुरानी रिपोर्ट: reported state; दोबारा सत्यापन बिना verified न करें।
- एक घटना: observation। कई स्वतंत्र संदर्भों में दोहराव: candidate pattern। counterexample और time/context भी रखें।
- default रूप से कम से कम तीन अलग episodes के बाद ही स्थायी pattern प्रस्तावित करें; संख्या स्वयं वैज्ञानिक सत्यापन नहीं। उपयोगकर्ता की स्पष्ट पसंद तुरंत लागू हो सकती है।
- वर्तमान correction पुराने निष्कर्ष को supersede करे; पुराना record और कारण revision history में रहे।
- आय, health, relationships, व्यक्तित्व और risk-taking के निष्कर्ष बिना आधार न बनाएँ। brain-function नहीं, दिखाई देने वाला काम और self-report दर्ज करें।

## सुरक्षित संपादन और कई chats
1. बदलने वाली फ़ाइलों का dated backup archive/revisions में रखें। पहले current revision पढ़ें।
2. EPISODES.jsonl में unique id से append; समान source + event दोबारा न डालें।
3. CURRENT/PROFILE/BEHAVIOUR में केवल प्रमाणित अंतर merge करें। समान विषय पर विरोध हो तो दोनों source और unresolved status रखें।
4. लिखने से ठीक पहले revision फिर पढ़ें। बदल गया हो तो नई प्रति पर merge करें; दूसरे session का update overwrite न करें। एक समय एक writer रखें; future service में lock/transactions जोड़ें।
5. JSON पढ़कर validation, source links, वर्तमान तारीख और affected summary की consistency जाँचें।
6. CHANGELOG, manifest revision और HANDOVER अपडेट करें; बताएँ क्या सीखा, क्या बदला, क्या अनिश्चित है।
7. background collection या sync को तब तक active न बताएँ जब तक वास्तव में configured और tested न हो।

## session के अंत की उपयोगी समीक्षा
विचार क्या था? कौन सा विकल्प चुना? किस चीज़ को कितना reject किया? क्या वास्तविक action हुआ? अगली वापसी पर क्या जाँचना है? रुचि, समय और परिणाम को अलग रखें। हर बार लंबी questionnaire जरूरी नहीं।

## portable copy
फ़ाइल पहुँच वाली chat में main folder update करें। केवल attachments वाली chat में संशोधित files वापस दें और main copy में merge करें। snapshot की तारीख लिखें। cloud/server sync अभी planned है; automatic नहीं।

## निजी/परिवार और portable-file updates
नई व्यक्तिगत जानकारी का audience दर्ज करें: private/default, family_approved या undecided। परिवार से जुड़ा होना family publication की सहमति नहीं है। user के असली शब्द, approved summary और AI interpretation अलग रखें। बचे प्रश्न के लिए memory/OPEN-QUESTIONS.md पढ़ें; deferred प्रश्न बार-बार न पूछें।
बदलाव के बाद tools/Build-Portable.ps1 चलाकर MY-DIGITAL-MEMORY.md पुनः बनाएँ। केवल portable file वाली chat के assistant उसी file का revised version दे सकते हैं; main folder वाले assistant source files में merge करके snapshot बनाएँ। परिवार के लिए केवल legacy/family से export करें।

## प्रति-चैट record और मंडली
पहले protocols/CHAT-RECORD.md के अनुसार stable chat file बनाएँ/अपडेट करें। title/date बदलने से नई file न बने। source IDs न मिलें तो local IDs और possible duplicate सीमा लिखें। मूल शब्द, सार, hypotheses और AI advice अलग रखें। coordinator जरूरी specialists चुने, प्रमाण reviewer से जाँच करे और अकेला main-memory writer रहे। tools/build_chat_archive.py से chats index/compiled archive बनाएँ; semantic merge reviewed deltas से ही हो। उसके बाद tools/Build-Portable.ps1 चलाएँ। इस प्रक्रिया का अर्थ scheduled/background collection नहीं।
