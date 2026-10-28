# विशेषज्ञ मंडली
| भूमिका | ID |
|---|---|
| मुख्य समन्वयक | memory_main |
| बातचीत रिकॉर्डर | memory_chat |
| व्यवहार विश्लेषक | memory_behavior |
| मूल्य और सिद्धांत | memory_values |
| राय और विचार सहयोगी | memory_advisor |
| बच्चों और विरासत विशेषज्ञ | memory_legacy |
| आर्थिक स्थिति विशेषज्ञ | memory_finance |
| जीवन लक्ष्य विशेषज्ञ | memory_goals |
| काम और प्रोजेक्ट विशेषज्ञ | memory_projects |
| प्रमाण और गोपनीयता समीक्षक | memory_evidence |

साधारण update: chat + evidence + coordinator। व्यवहार पर person/behavior; आर्थिक प्रश्न पर finance/goals; परिवार पर legacy/values; काम पर projects/advisor जोड़ें। हर request पर सभी agents न चलाएँ। named roles उपलब्ध न हों तो उसी instruction से generic subagent या sequential workflow इस्तेमाल करें।

एक समय एक main writer। किसी विषय पर बहुमत वास्तविक source या user correction से ऊपर नहीं। भूमिका files अपने-आप persistent bots नहीं बनातीं।
