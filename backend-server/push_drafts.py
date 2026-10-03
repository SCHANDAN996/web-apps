import sqlite3

content_hi = """# अध्याय 4: प्रतिशत (Percentage)

**परिचय:**
प्रतिशत गणित का वह जादुई उपकरण है जिसका उपयोग हम तुलना करने के लिए करते हैं। चाहे परीक्षा में आपके अंक हों, दुकान पर मिलने वाली छूट हो, या मोबाइल की बैटरी... हर जगह प्रतिशत है! यह अध्याय प्रतियोगी परीक्षाओं (SSC, Banking) की नींव है, इसलिए इसे समझना अत्यंत महत्वपूर्ण है।

**क्या है यह प्रतिशत? (Feynman Style):**
सोचो कि तुम्हारे पास एक बड़ा सा पिज़्ज़ा है जिसे तुमने 100 बराबर टुकड़ों में काट लिया है। प्रतिशत का मतलब ही होता है "प्रति 100" (Per Cent)। 
अगर तुमने उन 100 में से 20 टुकड़े खा लिए, तो हम कहेंगे कि तुमने पिज़्ज़ा का 20% खा लिया! इसका सीधा सा मतलब है, किसी भी चीज़ को 100 हिस्सों में बाँट कर देखना।
अगर तुम्हारे पास 50 रुपये हैं और मैंने कहा कि इसका 10% मुझे दे दो। तो पहले 50 रुपये को 100 बराबर हिस्सों में बाँटो (हर हिस्सा 0.5 रुपये का होगा)। अब मुझे ऐसे 10 हिस्से दे दो (0.5 x 10 = 5 रुपये)। बहुत आसान है न?

> 🧠 **[Recall: 'प्रतिशत (Percent)' शब्द का शाब्दिक अर्थ क्या है?]**

**भिन्न (Fractions) और प्रतिशत की दोस्ती:**
भिन्न भी हिस्सा बताते हैं और प्रतिशत भी। अगर तुम पिज़्ज़ा का आधा हिस्सा (1/2) खाते हो, तो 100 टुकड़ों में से तुमने कितने खाए? 50 टुकड़े! इसलिए 1/2 का मतलब 50% होता है।
भिन्न को प्रतिशत में बदलने के लिए बस 100 से गुणा कर दो। 
उदाहरण: 1/4 × 100 = 25%।

> 💡 **[Stop and Think! 🤔: अगर 1/4 का मतलब 25% है, तो 3/4 का मतलब क्या होगा? दिमाग लगाओ... क्या यह 25% का 3 गुना नहीं होगा?]**

**तुलनात्मक प्रतिशत (Comparative Percentage):**
अक्सर परीक्षाओं में पूछा जाता है: *"A की आय B से 20% अधिक है, तो B की आय A से कितनी कम है?"*
इसमें सबसे बड़ी गलती यह होती है कि हम सोचते हैं उत्तर भी 20% ही होगा। नहीं!
मान लो B कमाता है 100 रुपये। A कमाएगा 120 रुपये।
अब B, A से 20 रुपये कम कमाता है। लेकिन अब हमारी तुलना A से हो रही है (आधार 120 है)।
तो: (20 / 120) × 100 = 16.67%
*(ध्यान दें: SSC CGL 2018 में यह सवाल सीधा पूछा गया था!)*

> 🧠 **[Recall: जब हम यह कहते हैं कि X, Y से कितने प्रतिशत कम है, तो तुलना का आधार (Denominator/हर) क्या होता है?]**

**महत्वपूर्ण सूत्र (Key Formulas):**

| विवरण | सूत्र | उदाहरण |
|---|---|---|
| प्रतिशत निकालना | (हिस्सा / कुल) × 100 | (20/50) × 100 = 40% |
| भिन्न से प्रतिशत | भिन्न × 100 | 1/5 × 100 = 20% |
| प्रतिशत से भिन्न | प्रतिशत / 100 | 25/100 = 1/4 |
| शुद्ध क्रमिक प्रतिशत परिवर्तन (Net Successive Change) | A + B + (A×B)/100 | 20% वृद्धि, 10% कमी = 20 - 10 + (20×-10)/100 = 8% |

---
**[Mind Map - प्रतिशत (भिन्न रूपांतरण, क्रमिक परिवर्तन, और तुलना)]**
---

📌 **[Spaced Repetition Hint: इसे 2 दिन बाद दोहराएँ]**
"""

content_en = """# Chapter 4: Percentage

**Introduction:**
Percentage is the magic tool of mathematics used for comparison. Whether it's your marks in an exam, a discount at a shop, or your mobile phone's battery life... percentages are everywhere! This chapter is the absolute foundation for competitive exams (SSC, Banking, UPSC CSAT), so understanding it is extremely important.

**What is a Percentage? (Feynman Style):**
Imagine you have a large pizza cut into 100 equal slices. The word "Percentage" literally means "Per Cent" or "For every 100".
If you ate 20 slices out of those 100, we say you ate 20% of the pizza! It simply means looking at anything by dividing it into 100 equal parts.
If you have 50 rupees and I ask you to give me 10% of it. First, divide 50 rupees into 100 equal parts (each part will be 0.5 rupees). Now give me 10 such parts (0.5 x 10 = 5 rupees). Very easy, right?

> 🧠 **[Recall: What is the literal meaning of the word 'Percent'?]**

**The Friendship of Fractions and Percentages:**
Fractions show parts, and so do percentages. If you eat half (1/2) of a pizza, how many slices out of 100 did you eat? 50 slices! That's why 1/2 means 50%.
To convert a fraction into a percentage, just multiply it by 100. 
Example: 1/4 × 100 = 25%.

> 💡 **[Stop and Think! 🤔: If 1/4 means 25%, what would 3/4 mean? Use your brain... wouldn't it simply be 3 times of 25%?]**

**Comparative Percentage:**
Exams often ask this trick question: *"If A's income is 20% more than B's, by how much percent is B's income less than A's?"*
The biggest mistake we make here is thinking the answer will also be 20%. No!
Suppose B earns 100 rupees. A will earn 120 rupees.
Now, B earns 20 rupees less than A. But now we are comparing with A (the base is 120).
So: (20 / 120) × 100 = 16.67%
*(Note: This exact question was asked in SSC CGL 2018!)*

> 🧠 **[Recall: When we ask "by what percentage is X less than Y", what becomes the base (Denominator) of our comparison?]**

**Key Formulas:**

| Description | Formula | Example |
|---|---|---|
| Finding Percentage | (Part / Total) × 100 | (20/50) × 100 = 40% |
| Fraction to Percentage | Fraction × 100 | 1/5 × 100 = 20% |
| Percentage to Fraction | Percentage / 100 | 25/100 = 1/4 |
| Net Successive Percentage Change | A + B + (A×B)/100 | 20% increase, 10% decrease = 20 - 10 + (20×-10)/100 = 8% |

---
**[Mind Map - Percentage (Fraction Conversion, Successive Change, and Comparison)]**
---

📌 **[Spaced Repetition Hint: Review this after 2 days]**
"""

conn = sqlite3.connect('study_station.db')
c = conn.cursor()
c.execute("UPDATE book_chapter SET content_hi = ?, content_en = ? WHERE id = 4", (content_hi, content_en))
conn.commit()
conn.close()
print("Drafts pushed successfully to chapter id=4.")
