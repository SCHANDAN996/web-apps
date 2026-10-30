# एक चैट, एक स्थिर रिकॉर्ड

## पहचान और फ़ाइल
chats/records/<chat-id>.md रखें। शीर्षक/तारीख बदलने से file ID न बदलें। ID न हो तो local-<uuid> दें और बाद में alias जोड़ें। केवल शीर्षक से दो chats merge न करें। एक ही chat के बाद के updates उसी file में नए events/revisions हों।

metadata का छोटा JSON-संगत front matter: schema_version, record_id, chat_id, title, source_kind, source_order, coverage, first_message_at, last_message_at, recorded_at, record_revision, audience, review_state। समय अज्ञात हो तो null; record का creation day वास्तविक घटना का दिन नहीं।

## हर event
- stable event ID, actual source message/turn ID यदि उपलब्ध हो; नहीं तो local observation ID और source excerpt fingerprint।
- मूल शब्द अलग quote; सार अलग; AI व्याख्या/भरोसा/alternative अलग।
- घटना का समय/unknown और दर्ज करने की तारीख अलग।
- idea, interest, exploration, decision, commitment, action, correction, rejection, pause, return, completion, preference में प्रकार।
- किस चीज़ पर प्रतिक्रिया: विचार/तरीका/output/समय/लागत/अस्पष्ट।
- वास्तविक action का प्रमाण; केवल assistant का दावा हो तो reported।
- follow-up unknown/blocked/paused/acted/completed/explicitly_abandoned; चुप्पी से abandoned नहीं।
- audience private/default; family approval केवल approved अंश पर।
- corrections पुराने event को supersedes link से सुधारें; पुराने शब्द मिटाएँ नहीं।

## दोहराव और compilation
dedup key: chat ID + source message ID + event type + target। source IDs गायब हों तो local IDs के आधार पर record रखें और संभावित duplicate flag करें; समान short phrase दो अलग घटनाएँ भी हो सकती है। तीन summaries एक मूल episode की तीन independent confirmations नहीं हैं।

tools/build_chat_archive.py अलग records का index और CHAT-COMPILATION.md बनाता है; यह यांत्रिक compilation है। यह व्यक्तित्व निष्कर्ष नहीं निकालता और main memory में अपने-आप merge नहीं करता। विषय विशेषज्ञ + प्रमाण समीक्षक + coordinator semantic merge करें। मुख्य memory निष्कर्षों में chat-file#event-id references हों।

## access और ईमानदार coverage
केवल उपलब्ध इतिहास को रिकॉर्ड करें; partial का अर्थ partial। पुराने bounded cache से बने records full transcripts नहीं। Quotes truncated हों तो स्पष्ट लिखें। source date/ID न बचा हो तो invent न करें। local files तक पहुँच न हो तो उसी stable filename की updated file वापस दें; saved होने का दावा न करें।

एक coordinator ही मुख्य memory और canonical chat files लिखे। specialists अलग proposals दें। नए message आने पर append/update करें, archive को प्राथमिक स्रोत और current summaries को उससे निकला view मानें।

स्रोत का क्रम newest_first/oldest_first/selected_not_chronological/unknown लिखें। event संख्या अपने आप समय का क्रम नहीं है। message dates अज्ञात हों तो order और chronology की सीमा स्पष्ट रहे।
