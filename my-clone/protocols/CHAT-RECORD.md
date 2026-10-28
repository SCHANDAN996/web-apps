# एक चैट — एक स्थिर रिकॉर्ड

`chats/records/<provider-and-chat-id>.md` में हर chat का एक record रखें। शीर्षक बदलने से filename न बदलें। source ID न हो तो local UUID और alias रखें। उसी conversation के updates उसी file में जुड़ें।

Template का JSON-compatible front matter पूरा करें। source_order और coverage लिखें; date न मिले तो null। स्थानीय import date को message date न मानें। event IDs स्थिर हों; actual message IDs और source timestamps जहाँ उपलब्ध हों रखें।

हर event में quote, paraphrase, interpretation/confidence, दूसरा संभव अर्थ, reaction scope, action evidence, follow-up state और privacy अलग हों। विचार/खोज/निर्णय/commitment/actual action में फर्क रखें। pasted third-party text और client-generated messages user की प्राकृतिक भाषा या beliefs नहीं।

Duplicate key: provider/account/chat + source message ID + event type + target। repeated export/summary एक independent confirmation नहीं। source IDs गायब हों तो possible duplicate बताएँ। correction पुराने record को supersede/link करे, चुपचाप मिटाए नहीं।

tools/build_chat_archive.py mechanical source compilation करता है। यह personality analysis नहीं करता और facts अपने-आप approve नहीं करता। यह केवल private local records पर चले।
